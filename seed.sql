BEGIN;

INSERT INTO disaster_types (name, description)
VALUES (
    'Severe Storm',
    'Strong wind, heavy rain, lightning, and a possible extended power outage.'
)
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description;

INSERT INTO scenarios (
    disaster_type_id,
    title,
    description,
    household_description,
    starting_budget,
    starting_time,
    difficulty,
    is_published
)
SELECT
    id,
    'The Long Night',
    'A severe storm is forecast to arrive this evening and may interrupt power overnight.',
    'Two adults, one child, a dog, and a neighbor who may need assistance.',
    120.00,
    8,
    'beginner',
    TRUE
FROM disaster_types
WHERE name = 'Severe Storm'
ON CONFLICT (disaster_type_id, title) DO UPDATE SET
    description = EXCLUDED.description,
    household_description = EXCLUDED.household_description,
    starting_budget = EXCLUDED.starting_budget,
    starting_time = EXCLUDED.starting_time,
    difficulty = EXCLUDED.difficulty,
    is_published = EXCLUDED.is_published;

INSERT INTO decision_points (scenario_id, phase, position, prompt)
SELECT scenario.id, data.phase, data.position, data.prompt
FROM scenarios AS scenario
JOIN disaster_types AS disaster ON disaster.id = scenario.disaster_type_id
CROSS JOIN (
    VALUES
        ('prepare', 1, 'How will the household receive reliable updates?'),
        ('prepare', 2, 'Which supplies should be prepared before the storm?'),
        ('prepare', 3, 'How will household members reconnect if separated?'),
        ('prepare', 4, 'What should be done about phones and backup power?'),
        ('prepare', 5, 'Who else needs to be included in the plan?'),
        ('respond', 6, 'Wind and lightning intensify. Where should everyone wait?'),
        ('respond', 7, 'The power fails after dark. How should the room be lit?'),
        ('respond', 8, 'A power line is down across the street. What should the household do?')
) AS data(phase, position, prompt)
WHERE disaster.name = 'Severe Storm' AND scenario.title = 'The Long Night'
ON CONFLICT (scenario_id, position) DO UPDATE SET
    phase = EXCLUDED.phase,
    prompt = EXCLUDED.prompt;

INSERT INTO choices (
    decision_point_id,
    choice_text,
    time_cost,
    budget_cost,
    supplies_effect,
    communication_effect,
    safety_effect,
    community_effect,
    feedback
)
SELECT point.id, data.choice_text, data.time_cost, data.budget_cost,
       data.supplies_effect, data.communication_effect, data.safety_effect,
       data.community_effect, data.feedback
FROM decision_points AS point
JOIN scenarios AS scenario ON scenario.id = point.scenario_id
CROSS JOIN (
    VALUES
        (1, 'Enable official alerts and locate a battery radio.', 1, 25.00, 5, 15, 10, 0,
         'Official alerts and a battery-powered information source help the household receive updates during an outage.'),
        (1, 'Rely on social media posts from friends.', 0, 0.00, 0, -5, -5, 0,
         'Posts from friends may be delayed or inaccurate. Confirm important instructions through official sources.'),
        (2, 'Gather water, shelf-stable food, flashlights, and batteries.', 2, 55.00, 25, 0, 10, 0,
         'A practical supply kit supports the household when stores are closed and electricity is unavailable.'),
        (2, 'Buy snacks but skip lighting and water.', 1, 25.00, 8, 0, -5, 0,
         'Food helps, but the kit remains incomplete without water and safe emergency lighting.'),
        (3, 'Choose a contact, meeting place, and written phone list.', 1, 0.00, 0, 25, 5, 5,
         'A communication plan gives everyone a shared method for reconnecting.'),
        (3, 'Decide to improvise if anyone gets separated.', 0, 0.00, 0, -10, -5, 0,
         'Improvising under stress can create confusion. Agree on contacts and meeting places ahead of time.'),
        (4, 'Charge devices and prepare power banks.', 1, 30.00, 5, 15, 5, 0,
         'Charged devices and backup power can extend access to messages and official information.'),
        (4, 'Leave devices at their current charge.', 0, 0.00, 0, -5, 0, 0,
         'An outage may last longer than expected, making available battery power important.'),
        (5, 'Pack pet supplies and check on the neighbor.', 2, 10.00, 8, 5, 5, 20,
         'Preparedness plans should include animals and people who may need additional assistance.'),
        (5, 'Plan only for the people inside the home.', 0, 0.00, 0, 0, 0, -10,
         'A household plan is stronger when it accounts for pets and safe ways to check on others.'),
        (6, 'Move indoors and stay away from windows.', 0, 0.00, 0, 0, 20, 0,
         'An interior location away from windows reduces exposure to wind-blown debris and broken glass.'),
        (6, 'Watch the storm from the covered porch.', 0, 0.00, 0, 0, -20, 0,
         'A porch still leaves people exposed to lightning, wind, and debris.'),
        (7, 'Use flashlights or battery-powered lanterns.', 0, 0.00, 5, 0, 15, 0,
         'Battery-powered lights avoid the fire risk created by unattended open flames.'),
        (7, 'Light several candles around the home.', 0, 0.00, 0, 0, -15, 0,
         'Open flames add a preventable fire risk during a power outage.'),
        (8, 'Stay far away and report the line to local authorities or the utility.', 0, 0.00, 0, 10, 25, 5,
         'Downed lines may be energized. Keep away, prevent others from approaching, and report the hazard.'),
        (8, 'Approach the line to see whether it is active.', 0, 0.00, 0, 0, -30, -5,
         'Never approach or touch a downed power line or anything in contact with it.')
) AS data(
    position, choice_text, time_cost, budget_cost, supplies_effect,
    communication_effect, safety_effect, community_effect, feedback
)
WHERE scenario.title = 'The Long Night' AND point.position = data.position
ON CONFLICT (decision_point_id, choice_text) DO UPDATE SET
    time_cost = EXCLUDED.time_cost,
    budget_cost = EXCLUDED.budget_cost,
    supplies_effect = EXCLUDED.supplies_effect,
    communication_effect = EXCLUDED.communication_effect,
    safety_effect = EXCLUDED.safety_effect,
    community_effect = EXCLUDED.community_effect,
    feedback = EXCLUDED.feedback;

INSERT INTO guidance_sources (organization, title, url, reviewed_at)
VALUES
    ('Ready.gov', 'Plan Ahead for Disasters', 'https://www.ready.gov/', CURRENT_DATE),
    ('Ready.gov', 'Build a Kit', 'https://www.ready.gov/kit', CURRENT_DATE),
    ('Ready.gov', 'Power Outages', 'https://www.ready.gov/power-outages', CURRENT_DATE)
ON CONFLICT (url) DO UPDATE SET
    organization = EXCLUDED.organization,
    title = EXCLUDED.title,
    reviewed_at = EXCLUDED.reviewed_at;

INSERT INTO choice_sources (choice_id, source_id, evidence_note)
SELECT choice.id, source.id, 'General preparedness guidance for this decision.'
FROM choices AS choice
JOIN decision_points AS point ON point.id = choice.decision_point_id
JOIN scenarios AS scenario ON scenario.id = point.scenario_id
JOIN guidance_sources AS source ON source.url = 'https://www.ready.gov/'
WHERE scenario.title = 'The Long Night'
ON CONFLICT (choice_id, source_id) DO NOTHING;

INSERT INTO choice_sources (choice_id, source_id, evidence_note)
SELECT choice.id, source.id, 'Supply and outage guidance for this decision.'
FROM choices AS choice
JOIN decision_points AS point ON point.id = choice.decision_point_id
JOIN scenarios AS scenario ON scenario.id = point.scenario_id
JOIN guidance_sources AS source
    ON source.url IN ('https://www.ready.gov/kit', 'https://www.ready.gov/power-outages')
WHERE scenario.title = 'The Long Night' AND point.position IN (2, 4, 7, 8)
ON CONFLICT (choice_id, source_id) DO NOTHING;

COMMIT;

