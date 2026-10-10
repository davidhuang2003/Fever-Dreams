-- 1. Completion rate by scenario.
SELECT
    scenario.title,
    COUNT(playthrough.id) AS playthroughs_started,
    COUNT(playthrough.id) FILTER (WHERE playthrough.status = 'completed') AS completed,
    ROUND(
        100.0 * COUNT(playthrough.id) FILTER (WHERE playthrough.status = 'completed')
        / NULLIF(COUNT(playthrough.id), 0),
        1
    ) AS completion_rate_percent
FROM scenarios AS scenario
LEFT JOIN playthroughs AS playthrough ON playthrough.scenario_id = scenario.id
GROUP BY scenario.id, scenario.title
ORDER BY completion_rate_percent DESC NULLS LAST;

-- 2. Most frequently selected choices and their decision prompts.
SELECT
    point.prompt,
    choice.choice_text,
    COUNT(player_choice.id) AS times_selected
FROM player_choices AS player_choice
JOIN choices AS choice ON choice.id = player_choice.choice_id
JOIN decision_points AS point ON point.id = player_choice.decision_point_id
GROUP BY point.id, point.prompt, choice.id, choice.choice_text
ORDER BY times_selected DESC, point.position;

-- 3. Average final readiness scores for completed playthroughs.
SELECT
    scenario.title,
    ROUND(AVG(playthrough.supplies_score), 1) AS average_supplies,
    ROUND(AVG(playthrough.communication_score), 1) AS average_communication,
    ROUND(AVG(playthrough.safety_score), 1) AS average_safety,
    ROUND(AVG(playthrough.community_score), 1) AS average_community
FROM playthroughs AS playthrough
JOIN scenarios AS scenario ON scenario.id = playthrough.scenario_id
WHERE playthrough.status = 'completed'
GROUP BY scenario.id, scenario.title
ORDER BY scenario.title;

