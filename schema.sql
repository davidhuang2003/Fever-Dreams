BEGIN;

CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX users_username_lower_uq ON users (LOWER(username));
CREATE UNIQUE INDEX users_email_lower_uq ON users (LOWER(email));

CREATE TABLE disaster_types (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE scenarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    disaster_type_id BIGINT NOT NULL
        REFERENCES disaster_types(id) ON DELETE RESTRICT,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    household_description TEXT NOT NULL,
    starting_budget NUMERIC(10, 2) NOT NULL CHECK (starting_budget >= 0),
    starting_time INTEGER NOT NULL CHECK (starting_time >= 0),
    difficulty VARCHAR(20) NOT NULL
        CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (disaster_type_id, title)
);

CREATE TABLE decision_points (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id BIGINT NOT NULL
        REFERENCES scenarios(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL CHECK (phase IN ('prepare', 'respond')),
    position INTEGER NOT NULL CHECK (position > 0),
    prompt TEXT NOT NULL,
    UNIQUE (scenario_id, position)
);

CREATE TABLE choices (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    decision_point_id BIGINT NOT NULL
        REFERENCES decision_points(id) ON DELETE CASCADE,
    choice_text TEXT NOT NULL,
    time_cost INTEGER NOT NULL DEFAULT 0 CHECK (time_cost >= 0),
    budget_cost NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (budget_cost >= 0),
    supplies_effect INTEGER NOT NULL DEFAULT 0
        CHECK (supplies_effect BETWEEN -100 AND 100),
    communication_effect INTEGER NOT NULL DEFAULT 0
        CHECK (communication_effect BETWEEN -100 AND 100),
    safety_effect INTEGER NOT NULL DEFAULT 0
        CHECK (safety_effect BETWEEN -100 AND 100),
    community_effect INTEGER NOT NULL DEFAULT 0
        CHECK (community_effect BETWEEN -100 AND 100),
    feedback TEXT NOT NULL,
    UNIQUE (decision_point_id, choice_text),
    UNIQUE (id, decision_point_id)
);

CREATE TABLE guidance_sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization VARCHAR(160) NOT NULL,
    title VARCHAR(240) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    reviewed_at DATE NOT NULL
);

CREATE TABLE choice_sources (
    choice_id BIGINT NOT NULL REFERENCES choices(id) ON DELETE CASCADE,
    source_id BIGINT NOT NULL REFERENCES guidance_sources(id) ON DELETE RESTRICT,
    evidence_note TEXT,
    PRIMARY KEY (choice_id, source_id)
);

CREATE TABLE playthroughs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scenario_id BIGINT NOT NULL REFERENCES scenarios(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'abandoned')),
    remaining_budget NUMERIC(10, 2) NOT NULL CHECK (remaining_budget >= 0),
    remaining_time INTEGER NOT NULL CHECK (remaining_time >= 0),
    current_position INTEGER NOT NULL DEFAULT 1 CHECK (current_position > 0),
    supplies_score INTEGER NOT NULL DEFAULT 0 CHECK (supplies_score BETWEEN 0 AND 100),
    communication_score INTEGER NOT NULL DEFAULT 0 CHECK (communication_score BETWEEN 0 AND 100),
    safety_score INTEGER NOT NULL DEFAULT 0 CHECK (safety_score BETWEEN 0 AND 100),
    community_score INTEGER NOT NULL DEFAULT 0 CHECK (community_score BETWEEN 0 AND 100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CHECK (
        (status = 'completed' AND completed_at IS NOT NULL)
        OR (status <> 'completed' AND completed_at IS NULL)
    )
);

CREATE TABLE player_choices (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    playthrough_id BIGINT NOT NULL
        REFERENCES playthroughs(id) ON DELETE CASCADE,
    decision_point_id BIGINT NOT NULL
        REFERENCES decision_points(id) ON DELETE RESTRICT,
    choice_id BIGINT NOT NULL,
    selected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (playthrough_id, decision_point_id),
    FOREIGN KEY (choice_id, decision_point_id)
        REFERENCES choices(id, decision_point_id) ON DELETE RESTRICT
);

CREATE INDEX scenarios_disaster_type_idx ON scenarios (disaster_type_id);
CREATE INDEX decision_points_scenario_idx ON decision_points (scenario_id, position);
CREATE INDEX choices_decision_point_idx ON choices (decision_point_id);
CREATE INDEX playthroughs_user_idx ON playthroughs (user_id, started_at DESC);
CREATE INDEX playthroughs_scenario_idx ON playthroughs (scenario_id);
CREATE INDEX player_choices_playthrough_idx ON player_choices (playthrough_id, selected_at);
CREATE INDEX player_choices_choice_idx ON player_choices (choice_id);
CREATE INDEX choice_sources_source_idx ON choice_sources (source_id);

COMMIT;

