import psycopg
import pytest

import game
import play


# ---------------------------------------------------------------------------
# Tests that don't need a database
# ---------------------------------------------------------------------------

def test_keep_in_range():
    assert game.keep_in_range(-20) == 0
    assert game.keep_in_range(50) == 50
    assert game.keep_in_range(130) == 100


def test_ask_number_retries_until_valid(monkeypatch):
    answers = iter(["hello", "9", "2"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert play.ask_number("> ", 1, 3) == 2


def test_ask_number_q_goes_back(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "q")
    assert play.ask_number("> ", 1, 3) is None


# ---------------------------------------------------------------------------
# Helpers for the database tests
# ---------------------------------------------------------------------------

def current_choices(connection, playthrough_id, user_id):
    playthrough = game.load_playthrough(connection, playthrough_id, user_id)
    decision = game.get_current_decision(connection, playthrough)
    return game.get_choices(connection, decision["id"])


def best_choice(connection, playthrough_id, user_id):
    """The current option that raises the readiness scores the most."""
    options = current_choices(connection, playthrough_id, user_id)
    ids = [option["id"] for option in options]
    return connection.execute(
        """
        SELECT * FROM choices WHERE id = ANY(%s)
        ORDER BY supplies_effect + communication_effect + safety_effect + community_effect DESC
        LIMIT 1
        """,
        [ids],
    ).fetchone()


def count_picks(connection, playthrough_id):
    row = connection.execute(
        "SELECT COUNT(*) AS n FROM player_choices WHERE playthrough_id = %s",
        [playthrough_id],
    ).fetchone()
    return row["n"]


# ---------------------------------------------------------------------------
# Players and scenarios
# ---------------------------------------------------------------------------

def test_same_name_returns_same_player(connection):
    first = game.get_or_create_player(connection, "Alex")
    second = game.get_or_create_player(connection, "  alex ")
    assert first["id"] == second["id"]


def test_blank_name_is_rejected(connection):
    with pytest.raises(game.GameError):
        game.get_or_create_player(connection, "   ")


def test_unpublished_scenario_cannot_start(connection, player):
    connection.execute("UPDATE scenarios SET is_published = FALSE")
    assert game.list_scenarios(connection) == []
    with pytest.raises(game.GameError):
        game.start_playthrough(connection, player["id"], 1)


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

def test_valid_choice_saves_exactly_one_row(connection, player, playthrough_id):
    choice = current_choices(connection, playthrough_id, player["id"])[0]
    game.record_choice(connection, playthrough_id, player["id"], choice["id"])

    assert count_picks(connection, playthrough_id) == 1
    playthrough = game.load_playthrough(connection, playthrough_id, player["id"])
    assert playthrough["current_position"] == 2
    assert playthrough["remaining_budget"] == 120 - choice["budget_cost"]


def test_same_choice_twice_is_rejected(connection, player, playthrough_id):
    choice = current_choices(connection, playthrough_id, player["id"])[0]
    game.record_choice(connection, playthrough_id, player["id"], choice["id"])

    with pytest.raises(game.GameError):
        game.record_choice(connection, playthrough_id, player["id"], choice["id"])
    assert count_picks(connection, playthrough_id) == 1


def test_choice_from_another_decision_is_rejected(connection, player, playthrough_id):
    other = connection.execute(
        "SELECT choices.id FROM choices JOIN decision_points ON decision_points.id = choices.decision_point_id "
        "WHERE decision_points.position = 8 LIMIT 1"
    ).fetchone()
    with pytest.raises(game.GameError):
        game.record_choice(connection, playthrough_id, player["id"], other["id"])
    assert count_picks(connection, playthrough_id) == 0


def test_unaffordable_choice_is_rejected(connection, player, playthrough_id):
    connection.execute("UPDATE playthroughs SET remaining_budget = 0 WHERE id = %s", [playthrough_id])
    expensive = best_choice(connection, playthrough_id, player["id"])  # costs $25
    with pytest.raises(game.GameError, match="money"):
        game.record_choice(connection, playthrough_id, player["id"], expensive["id"])
    assert count_picks(connection, playthrough_id) == 0


def test_other_players_game_is_hidden(connection, playthrough_id):
    stranger = game.get_or_create_player(connection, "stranger")
    with pytest.raises(game.GameError, match="not found"):
        game.load_playthrough(connection, playthrough_id, stranger["id"])
    with pytest.raises(game.GameError, match="not found"):
        game.record_choice(connection, playthrough_id, stranger["id"], 1)


def test_failed_choice_changes_nothing(connection, player, playthrough_id, monkeypatch):
    """Force an error halfway through the transaction and check it was undone."""
    before = game.load_playthrough(connection, playthrough_id, player["id"])
    choice = current_choices(connection, playthrough_id, player["id"])[0]

    def broken_count(*_args):
        raise psycopg.OperationalError("simulated failure")

    # count_decisions runs after the INSERT, so the INSERT must be rolled back.
    monkeypatch.setattr(game, "count_decisions", broken_count)
    with pytest.raises(psycopg.OperationalError):
        game.record_choice(connection, playthrough_id, player["id"], choice["id"])

    after = game.load_playthrough(connection, playthrough_id, player["id"])
    assert after == before
    assert count_picks(connection, playthrough_id) == 0


def test_full_game_completes_with_results(connection, player, playthrough_id):
    for _ in range(8):
        choice = best_choice(connection, playthrough_id, player["id"])
        game.record_choice(connection, playthrough_id, player["id"], choice["id"])

    playthrough = game.load_playthrough(connection, playthrough_id, player["id"])
    assert playthrough["status"] == "completed"
    assert playthrough["completed_at"] is not None

    results = game.get_results(connection, playthrough_id, player["id"])
    assert len(results["helped"]) == 8
    assert results["sources"]
