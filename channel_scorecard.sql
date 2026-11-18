-- SQLite: assumes channel_week has been loaded from data/channel_week.csv.
-- NULL ad spend means unavailable/not applicable, not zero cost.
WITH last_weeks AS (
    SELECT DISTINCT week FROM channel_week ORDER BY week DESC LIMIT 12
)
SELECT channel,
       SUM(sessions) AS sessions,
       SUM(attributed_orders) AS orders,
       100.0 * SUM(attributed_orders) / NULLIF(SUM(sessions), 0) AS cvr_pct,
       SUM(ad_spend) / NULLIF(SUM(attributed_orders), 0) AS cpa,
       SUM(attributed_revenue) / NULLIF(SUM(ad_spend), 0) AS roas
FROM channel_week
WHERE week IN (SELECT week FROM last_weeks)
GROUP BY channel
ORDER BY orders DESC;
