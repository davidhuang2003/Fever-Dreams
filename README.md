# Fever-Dreams

A small terminal game that teaches how to prepare for a severe storm and power outage. You have limited time and money, make 5 preparation choices and 3 choices during the storm, and get a debrief explaining what helped.

It uses only two languages:

- **Python** for the game (`play.py`, `game.py`, `db.py`)
- **PostgreSQL (SQL)** to store everything (`schema.sql`, `seed.sql`, `queries.sql`)

> Fever-Dreams is a learning game, not an emergency-alert service. Always follow instructions from local authorities.

## Example

```text
------------------------------------------------------------
Decision 1 of 8  (PREPARE phase)
Money left: $120.00    Time left: 8 hours
  Supplies         0/100
  Communication    0/100
  Safety           0/100
  Community        0/100
------------------------------------------------------------
How will the household receive reliable updates?

  1. Enable official alerts and locate a battery radio.
     costs 1 hours and $25.00
  2. Rely on social media posts from friends.
     costs 0 hours and $0.00

Your choice (or q to save and quit):
```

## Files

| File | What it does |
| --- | --- |
| `play.py` | The terminal screens: prints text and reads what you type. **Start here.** |
| `game.py` | The rules: checks each choice and saves it to the database |
| `db.py` | Connects to PostgreSQL and creates the tables |
| `schema.sql` | The tables and the rules the database enforces |
| `seed.sql` | The storm scenario: decisions, choices, and feedback |
| `queries.sql` | Example questions you can ask the data |
| `tests/` | Automated checks, run with `pytest` |

How a choice flows through the program:

```text
You type "1"  ->  play.py  ->  game.record_choice()  ->  PostgreSQL
                                   checks the rules
                                   saves everything or nothing
```

## Setup (Windows PowerShell)

You need **Python 3.10+** and **PostgreSQL**.

### 1. Install the Python packages

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks `Activate.ps1`, use `.venv\Scripts\python.exe` instead of `python`.

### 2. Create the database

Open **SQL Shell (psql)** or **pgAdmin** as the `postgres` user and run:

```sql
CREATE USER fever_dreams WITH PASSWORD 'choose-a-password';
CREATE DATABASE fever_dreams OWNER fever_dreams;
```

### 3. Tell the game where the database is

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace `change-me` with the password you chose. `.env` is never committed to Git.

### 4. Create the tables and load the scenario

```powershell
python play.py --setup
```

### 5. Play

```powershell
python play.py
```

## Running the Tests

```powershell
python -m pytest -q
```

Tests that need a database are **skipped** unless you create a second, throwaway database and set `TEST_DATABASE_URL` in `.env`. The tests delete every table in that database, so never point it at the one you play with.

```sql
CREATE DATABASE fever_dreams_test OWNER fever_dreams;
```

## How the Rules Are Enforced

The rules are checked in two places:

1. **`game.record_choice()`** checks that the game is yours, still running, that the choice belongs to the current decision, and that you can afford it. All of this runs inside one **transaction**, so if anything fails, nothing is saved.
2. **`schema.sql`** makes PostgreSQL refuse bad data even if the Python code has a bug. For example, money can't go below zero, scores stay between 0 and 100, and each decision can only be answered once per game.

## Ideas for What to Build Next

- Write your own questions in `queries.sql` (for example, *which bad choice is picked most often?*).
- Add a second scenario to `seed.sql`, such as a wildfire or flood, and let the player pick one.
- Add a "random event" decision that only appears if the player skipped a preparation.

## Glossary

- **Table**: like a spreadsheet with strict rules about what each column can hold.
- **Primary key / foreign key**: a row's unique id / a column that points to a row in another table.
- **Constraint**: a database rule that rejects bad data, such as a negative budget.
- **Transaction**: a group of database changes that all succeed or are all undone.
- **SQL injection**: an attack where typed text is run as SQL. Prevented by `%s` placeholders.
- **Environment variable**: a setting kept outside the code, like `DATABASE_URL` in `.env`.
