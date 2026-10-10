"""The rules of the game.

Every function here talks to PostgreSQL. The terminal code in play.py only
shows what these functions return and passes along what the player typed.
Keeping the rules here (and not in play.py) means there is one place to read
and test them.
"""

# The four readiness scores. Each one is a column named like "supplies_score".
CATEGORIES = ["supplies", "communication", "safety", "community"]


class GameError(Exception):
    """Raised when the player tries something the rules don't allow.

    When this happens, nothing is saved to the database.
    """


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

def get_or_create_player(connection, username):
    """Find the player with this name, or create them if they are new."""
    username = username.strip()
    if username == "" or len(username) > 50:
        raise GameError("Names must be between 1 and 50 characters.")

    # %s is a placeholder. psycopg fills it in safely, which prevents
    # SQL injection. Never build SQL by gluing strings together.
    player = connection.execute(
        "SELECT id, username FROM users WHERE LOWER(username) = LOWER(%s)",
        [username],
    ).fetchone()

    if player is None:
        player = connection.execute(
            "INSERT INTO users (username) VALUES (%s) RETURNING id, username",
            [username],
        ).fetchone()

    return player


# ---------------------------------------------------------------------------
# Scenarios and playthroughs
# ---------------------------------------------------------------------------

def list_scenarios(connection):
    """Return every scenario that is published (ready to play)."""
    return connection.execute(
        """
        SELECT id, title, description, household_description,
               starting_budget, starting_time, difficulty
        FROM scenarios
        WHERE is_published = TRUE
        ORDER BY id
        """
    ).fetchall()


def start_playthrough(connection, user_id, scenario_id):
    """Start a new game of a scenario. Returns the new playthrough's id."""
    scenario = connection.execute(
        "SELECT starting_budget, starting_time FROM scenarios WHERE id = %s AND is_published = TRUE",
        [scenario_id],
    ).fetchone()
    if scenario is None:
        raise GameError("That scenario does not exist or is not published.")

    new_row = connection.execute(
        """
        INSERT INTO playthroughs (user_id, scenario_id, remaining_budget, remaining_time)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        [user_id, scenario_id, scenario["starting_budget"], scenario["starting_time"]],
    ).fetchone()
    return new_row["id"]


def list_playthroughs(connection, user_id):
    """Return this player's games, newest first."""
    return connection.execute(
        """
        SELECT playthroughs.id, playthroughs.status, playthroughs.started_at,
               playthroughs.current_position, scenarios.title
        FROM playthroughs
        JOIN scenarios ON scenarios.id = playthroughs.scenario_id
        WHERE playthroughs.user_id = %s
        ORDER BY playthroughs.id DESC
        """,
        [user_id],
    ).fetchall()


def load_playthrough(connection, playthrough_id, user_id):
    """Load one playthrough, but only if it belongs to this player."""
    playthrough = connection.execute(
        "SELECT * FROM playthroughs WHERE id = %s AND user_id = %s",
        [playthrough_id, user_id],
    ).fetchone()
    if playthrough is None:
        raise GameError("Playthrough not found.")
    return playthrough


def get_scores(playthrough):
    """Turn a playthrough row into a simple {"supplies": 10, ...} dictionary."""
    scores = {}
    for category in CATEGORIES:
        scores[category] = playthrough[category + "_score"]
    return scores


# ---------------------------------------------------------------------------
# Playing a turn
# ---------------------------------------------------------------------------

def get_current_decision(connection, playthrough):
    """Return the decision the player is on now, or None if the game is over."""
    if playthrough["status"] != "active":
        return None

    return connection.execute(
        """
        SELECT id, phase, position, prompt
        FROM decision_points
        WHERE scenario_id = %s AND position = %s
        """,
        [playthrough["scenario_id"], playthrough["current_position"]],
    ).fetchone()


def count_decisions(connection, scenario_id):
    """How many decisions a scenario has in total."""
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM decision_points WHERE scenario_id = %s",
        [scenario_id],
    ).fetchone()
    return row["total"]


def get_choices(connection, decision_id):
    """Return the options the player can pick for one decision."""
    return connection.execute(
        """
        SELECT id, choice_text, time_cost, budget_cost
        FROM choices
        WHERE decision_point_id = %s
        ORDER BY id
        """,
        [decision_id],
    ).fetchall()


def keep_in_range(score):
    """Scores must stay between 0 and 100 (schema.sql enforces this too)."""
    return max(0, min(100, score))


def record_choice(connection, playthrough_id, user_id, choice_id):
    """Check one choice against the rules and save it. Returns the choice.

    Everything inside "with connection.transaction()" is all-or-nothing:
    if any step raises an error, PostgreSQL undoes every change in the block.
    """
    with connection.transaction():
        # 1. Load the game. "FOR UPDATE" locks the row until we finish, so the
        #    same choice can't be saved twice at the same moment.
        playthrough = connection.execute(
            "SELECT * FROM playthroughs WHERE id = %s AND user_id = %s FOR UPDATE",
            [playthrough_id, user_id],
        ).fetchone()
        if playthrough is None:
            raise GameError("Playthrough not found.")
        if playthrough["status"] != "active":
            raise GameError("This game is already finished.")

        # 2. Make sure the choice belongs to the decision the player is on.
        decision = get_current_decision(connection, playthrough)
        choice = connection.execute(
            "SELECT * FROM choices WHERE id = %s AND decision_point_id = %s",
            [choice_id, decision["id"]],
        ).fetchone()
        if choice is None:
            raise GameError("That is not one of the current choices.")

        # 3. Make sure the player can afford it.
        if choice["time_cost"] > playthrough["remaining_time"]:
            raise GameError("There is not enough time left for that.")
        if choice["budget_cost"] > playthrough["remaining_budget"]:
            raise GameError("There is not enough money left for that.")

        # 4. Remember what the player picked. The UNIQUE rule in schema.sql
        #    rejects a second pick for the same decision.
        connection.execute(
            "INSERT INTO player_choices (playthrough_id, decision_point_id, choice_id) VALUES (%s, %s, %s)",
            [playthrough_id, decision["id"], choice_id],
        )

        # 5. Work out the new numbers.
        remaining_time = playthrough["remaining_time"] - choice["time_cost"]
        remaining_budget = playthrough["remaining_budget"] - choice["budget_cost"]
        supplies = keep_in_range(playthrough["supplies_score"] + choice["supplies_effect"])
        communication = keep_in_range(playthrough["communication_score"] + choice["communication_effect"])
        safety = keep_in_range(playthrough["safety_score"] + choice["safety_effect"])
        community = keep_in_range(playthrough["community_score"] + choice["community_effect"])

        # 6. Move to the next decision, or finish the game after the last one.
        if decision["position"] < count_decisions(connection, playthrough["scenario_id"]):
            next_position = decision["position"] + 1
            status = "active"
        else:
            next_position = decision["position"]
            status = "completed"

        # 7. Save the new numbers.
        connection.execute(
            """
            UPDATE playthroughs
            SET remaining_time = %s,
                remaining_budget = %s,
                supplies_score = %s,
                communication_score = %s,
                safety_score = %s,
                community_score = %s,
                current_position = %s,
                status = %s,
                completed_at = CASE WHEN %s = 'completed' THEN CURRENT_TIMESTAMP END
            WHERE id = %s
            """,
            [remaining_time, remaining_budget, supplies, communication, safety,
             community, next_position, status, status, playthrough_id],
        )

    return choice


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def get_results(connection, playthrough_id, user_id):
    """Build the end-of-game debrief from the choices saved in PostgreSQL."""
    playthrough = load_playthrough(connection, playthrough_id, user_id)
    scores = get_scores(playthrough)

    picks = connection.execute(
        """
        SELECT decision_points.position, decision_points.prompt,
               choices.choice_text, choices.feedback,
               choices.supplies_effect + choices.communication_effect
                 + choices.safety_effect + choices.community_effect AS total_effect
        FROM player_choices
        JOIN decision_points ON decision_points.id = player_choices.decision_point_id
        JOIN choices ON choices.id = player_choices.choice_id
        WHERE player_choices.playthrough_id = %s
        ORDER BY decision_points.position
        """,
        [playthrough_id],
    ).fetchall()

    sources = connection.execute(
        """
        SELECT DISTINCT guidance_sources.title, guidance_sources.url
        FROM player_choices
        JOIN choice_sources ON choice_sources.choice_id = player_choices.choice_id
        JOIN guidance_sources ON guidance_sources.id = choice_sources.source_id
        WHERE player_choices.playthrough_id = %s
        ORDER BY guidance_sources.title
        """,
        [playthrough_id],
    ).fetchall()

    # Sort the picks into "helped" and "could improve".
    helped = []
    could_improve = []
    for pick in picks:
        if pick["total_effect"] > 0:
            helped.append(pick)
        else:
            could_improve.append(pick)

    return {
        "status": playthrough["status"],
        "scores": scores,
        "strongest": max(scores, key=scores.get),
        "weakest": min(scores, key=scores.get),
        "helped": helped,
        "could_improve": could_improve,
        "sources": sources,
    }
