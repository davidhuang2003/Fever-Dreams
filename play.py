"""Fever-Dreams: a terminal game about preparing for a storm.

Run it with:
    python play.py            play the game
    python play.py --setup    create the tables and load the scenario

This file only handles the terminal: printing text and reading what the
player types. The rules live in game.py and the data lives in PostgreSQL.
"""

import sys

from dotenv import load_dotenv

import db
import game

LINE = "-" * 60


# ---------------------------------------------------------------------------
# Small helpers for reading input
# ---------------------------------------------------------------------------

def ask_number(question, lowest, highest):
    """Keep asking until the player types a whole number in the range.

    Returns None if the player types q (to go back).
    """
    while True:
        answer = input(question).strip().lower()
        if answer == "q":
            return None
        if answer.isdigit() and lowest <= int(answer) <= highest:
            return int(answer)
        print(f"Please type a number from {lowest} to {highest}, or q to go back.")


def money(amount):
    """Format a number as dollars, like $25.00."""
    return f"${amount:.2f}"


def show_scores(scores):
    """Print the four readiness scores as simple text bars."""
    for category, score in scores.items():
        bar = "#" * (score // 5)
        print(f"  {category.title():<14} {score:>3}/100  {bar}")


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

def play_turn(connection, player, playthrough_id):
    """Show one decision and record the player's choice.

    Returns False when the game is over or the player wants to stop.
    """
    playthrough = game.load_playthrough(connection, playthrough_id, player["id"])
    decision = game.get_current_decision(connection, playthrough)
    if decision is None:
        return False

    total = game.count_decisions(connection, playthrough["scenario_id"])
    choices = game.get_choices(connection, decision["id"])

    print()
    print(LINE)
    print(f"Decision {decision['position']} of {total}  ({decision['phase'].upper()} phase)")
    print(f"Money left: {money(playthrough['remaining_budget'])}    "
          f"Time left: {playthrough['remaining_time']} hours")
    show_scores(game.get_scores(playthrough))
    print(LINE)
    print(decision["prompt"])
    print()
    for number, choice in enumerate(choices, start=1):
        print(f"  {number}. {choice['choice_text']}")
        print(f"     costs {choice['time_cost']} hours and {money(choice['budget_cost'])}")
    print()

    picked = ask_number("Your choice (or q to save and quit): ", 1, len(choices))
    if picked is None:
        print("Your game is saved. Choose 'Continue a game' to pick it up later.")
        return False

    try:
        choice = game.record_choice(connection, playthrough_id, player["id"], choices[picked - 1]["id"])
    except game.GameError as error:
        print(f"\n>> {error} Try another option.")
        return True

    print(f"\n>> {choice['feedback']}")
    input("Press Enter to continue...")
    return True


def show_results(connection, player, playthrough_id):
    """Print the debrief at the end of a game."""
    results = game.get_results(connection, playthrough_id, player["id"])

    print()
    print("=" * 60)
    print("DEBRIEF: The Long Night")
    print("=" * 60)
    show_scores(results["scores"])
    print(f"\nStrongest area: {results['strongest'].title()}")
    print(f"Area to work on: {results['weakest'].title()}")

    if results["helped"]:
        print("\nWhat helped:")
        for pick in results["helped"]:
            print(f"  + {pick['choice_text']}")
            print(f"    {pick['feedback']}")

    if results["could_improve"]:
        print("\nWhat to do differently next time:")
        for pick in results["could_improve"]:
            print(f"  - {pick['choice_text']}")
            print(f"    {pick['feedback']}")

    if results["sources"]:
        print("\nLearn more:")
        for source in results["sources"]:
            print(f"  {source['title']}: {source['url']}")
    print()


def run_game(connection, player, playthrough_id):
    """Play turns until the game ends or the player quits, then show results."""
    keep_going = True
    while keep_going:
        keep_going = play_turn(connection, player, playthrough_id)

    playthrough = game.load_playthrough(connection, playthrough_id, player["id"])
    if playthrough["status"] == "completed":
        show_results(connection, player, playthrough_id)


def new_game(connection, player):
    scenarios = game.list_scenarios(connection)
    if not scenarios:
        print("No scenarios found. Run: python play.py --setup")
        return

    # There is only one scenario for now, so start it directly.
    scenario = scenarios[0]
    print()
    print(LINE)
    print(scenario["title"].upper())
    print(LINE)
    print(scenario["description"])
    print(f"Household: {scenario['household_description']}")
    print(f"You have {money(scenario['starting_budget'])} and {scenario['starting_time']} hours to prepare.")
    input("\nPress Enter to begin...")

    playthrough_id = game.start_playthrough(connection, player["id"], scenario["id"])
    run_game(connection, player, playthrough_id)


def continue_game(connection, player):
    for playthrough in game.list_playthroughs(connection, player["id"]):
        if playthrough["status"] == "active":
            run_game(connection, player, playthrough["id"])
            return
    print("You have no unfinished games. Start a new one!")


def show_history(connection, player):
    playthroughs = game.list_playthroughs(connection, player["id"])
    if not playthroughs:
        print("You haven't played yet.")
        return

    print()
    for playthrough in playthroughs:
        started = playthrough["started_at"].strftime("%Y-%m-%d %H:%M")
        print(f"  Game #{playthrough['id']}  {playthrough['title']}  "
              f"{playthrough['status']}  (started {started})")

    game_id = ask_number("\nType a finished game's # to see its debrief, or q to go back: ",
                         1, max(p["id"] for p in playthroughs))
    if game_id is None:
        return
    try:
        show_results(connection, player, game_id)
    except game.GameError as error:
        print(error)


def main_menu(connection, player):
    while True:
        print()
        print(f"Hi {player['username']}! What would you like to do?")
        print("  1. New game")
        print("  2. Continue a game")
        print("  3. Past games")
        print("  4. Quit")
        option = ask_number("> ", 1, 4)

        if option == 1:
            new_game(connection, player)
        elif option == 2:
            continue_game(connection, player)
        elif option == 3:
            show_history(connection, player)
        else:
            print("Goodbye. Stay prepared!")
            return


def main():
    load_dotenv()  # reads DATABASE_URL from the .env file

    try:
        connection = db.connect()
    except Exception as error:
        print(f"Could not connect to PostgreSQL: {error}")
        return

    with connection:
        if "--setup" in sys.argv:
            db.setup_database(connection)
            print("Database is ready. Now run: python play.py")
            return

        print(LINE)
        print("FEVER-DREAMS: a disaster preparedness game")
        print("This is a learning game, not an emergency-alert service.")
        print(LINE)

        player = None
        while player is None:
            try:
                player = game.get_or_create_player(connection, input("What is your name? "))
            except game.GameError as error:
                print(error)

        main_menu(connection, player)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
