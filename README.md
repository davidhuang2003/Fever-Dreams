# Fever-Dreams

## Assignment

Build one small browser game that teaches a player how to prepare for a severe storm and power outage. The player has limited time and money, chooses preparations, responds to three events, and receives a short explanation of what helped.

This is a CS50-style specification: it describes what the program must do, but your code and visual design can be your own. Complete only this scenario before adding other disasters.

## Game Loop

1. A user registers or logs in.
2. The user starts **The Long Night** scenario.
3. The player makes five preparation choices.
4. The player makes three response choices during the storm.
5. Each choice changes time, money, or readiness.
6. The final page explains the player's strengths and missed preparations.

Track four readiness areas: **Supplies**, **Communication**, **Safety**, and **Community**. Do not calculate a fictional survival percentage.

## Frontend

Use HTML, CSS, and JavaScript.

- HTML provides the forms, choices, status values, and result content.
- CSS makes the pages readable, responsive, and keyboard accessible.
- JavaScript submits choices with `fetch`, updates the screen, prevents double submissions, and draws a simple storm scene with Canvas.
- Important instructions must remain readable without Canvas or animation.
- Respect `prefers-reduced-motion` and never use color as the only status indicator.

Required pages are: home, registration, login, dashboard, scenario briefing, game, and results.

## Flask

Flask connects the browser to PostgreSQL. Implement routes for authentication, starting a playthrough, loading its current state, recording one choice, and displaying results.

When recording a choice, Flask must:

1. Confirm the user owns the playthrough.
2. Confirm the choice belongs to the current decision.
3. Reject duplicate, unaffordable, or late choices.
4. Insert the choice and update scores in one transaction.
5. Return the new state as JSON.

Store only the user's ID in the session. Hash passwords, use parameterized SQL, and keep `DATABASE_URL` and `SECRET_KEY` in `.env`.

## PostgreSQL

PostgreSQL is the source of truth. The main relationships are:

```text
users (1) --------< playthroughs >-------- (1) scenarios
scenarios (1) --------< decision_points (1) --------< choices
playthroughs (1) --------< player_choices >-------- (1) choices
choices >--------< guidance_sources through choice_sources
```

Use the tables defined in `schema.sql`:

- `users` stores accounts and password hashes.
- `scenarios` and `decision_points` store the ordered game content.
- `choices` stores costs, score effects, and feedback.
- `playthroughs` stores one user's current attempt and scores.
- `player_choices` records exactly one choice per decision.
- `guidance_sources` connects safety explanations to trusted sources.

Foreign keys and unique constraints must enforce these relationships. The same checks must still work after Flask restarts.

## Run the Starter

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
flask --app app run --debug
```

Create the PostgreSQL database, update `.env`, then apply `schema.sql` followed by `seed.sql`. Run tests with:

```powershell
python -m pytest -q
```

## Complete When

- A user can register, log in, log out, and see only their games.
- The seeded storm scenario can be completed from beginning to end.
- Refreshing or double-clicking cannot record a choice twice.
- Invalid choices do not partially change money, time, or scores.
- Results are rebuilt from PostgreSQL and cite preparedness guidance.
- The interface works on mobile, with a keyboard, and with reduced motion.
- Automated tests cover authentication, ownership, choice validation, and transactions.

Fever-Dreams is an educational simulator, not an emergency-alert service or a substitute for instructions from local authorities.
