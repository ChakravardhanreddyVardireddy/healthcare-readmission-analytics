-- readmission_queries.sql
-- SQL analysis queries for the CMS Hospital Readmissions Reduction Program
-- (HRRP) sample, run against the SQLite database at data/hrrp.db
-- (build it first with: python scripts/01_clean_data.py)
--
-- Table: readmissions
-- Columns: facility_name, facility_id, state, measure_name,
--          number_of_discharges, footnote, excess_readmission_ratio,
--          predicted_readmission_rate, expected_readmission_rate,
--          number_of_readmissions, start_date, end_date

-- 1. Overall penalty rate: what share of scored facility-measures show
--    excess (worse-than-expected) readmissions?
SELECT
    COUNT(*) AS total_scored,
    SUM(CASE WHEN excess_readmission_ratio > 1.0 THEN 1 ELSE 0 END) AS penalized,
    ROUND(100.0 * SUM(CASE WHEN excess_readmission_ratio > 1.0 THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS pct_penalized
FROM readmissions
WHERE excess_readmission_ratio IS NOT NULL;

-- 2. Average excess readmission ratio and penalty rate by condition,
--    ranked worst to best. This tells us which clinical conditions are
--    driving the most excess readmissions across the sample.
SELECT
    measure_name,
    COUNT(*) AS n_hospitals,
    ROUND(AVG(excess_readmission_ratio), 4) AS avg_excess_ratio,
    ROUND(100.0 * SUM(CASE WHEN excess_readmission_ratio > 1.0 THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS pct_penalized
FROM readmissions
WHERE excess_readmission_ratio IS NOT NULL
GROUP BY measure_name
ORDER BY avg_excess_ratio DESC;

-- 3. Average excess readmission ratio and penalty rate by state.
SELECT
    state,
    COUNT(*) AS n_hospitals,
    ROUND(AVG(excess_readmission_ratio), 4) AS avg_excess_ratio,
    ROUND(100.0 * SUM(CASE WHEN excess_readmission_ratio > 1.0 THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS pct_penalized
FROM readmissions
WHERE excess_readmission_ratio IS NOT NULL
GROUP BY state
ORDER BY avg_excess_ratio DESC;

-- 4. Top 10 worst-performing facility-measures (highest excess ratio).
--    These are the hospitals with the largest gap between actual and
--    expected readmissions for a given condition.
SELECT
    facility_name,
    state,
    measure_name,
    excess_readmission_ratio,
    number_of_discharges
FROM readmissions
WHERE excess_readmission_ratio IS NOT NULL
ORDER BY excess_readmission_ratio DESC
LIMIT 10;

-- 5. Facilities that are penalized (ratio > 1.0) across 4 or more of the
--    6 tracked conditions - i.e. hospitals with a systemic readmissions
--    problem rather than a single-condition outlier.
SELECT
    facility_name,
    state,
    COUNT(*) AS n_measures_scored,
    SUM(CASE WHEN excess_readmission_ratio > 1.0 THEN 1 ELSE 0 END) AS n_measures_penalized,
    ROUND(AVG(excess_readmission_ratio), 4) AS avg_excess_ratio
FROM readmissions
WHERE excess_readmission_ratio IS NOT NULL
GROUP BY facility_name, state
HAVING COUNT(*) >= 4
ORDER BY n_measures_penalized DESC, avg_excess_ratio DESC
LIMIT 10;

-- 6. Readmission rate "gap" (predicted - expected) by condition. A
--    positive gap means hospitals are readmitting patients more often
--    than a similar hospital nationally would be expected to for that
--    condition - a direct measure of avoidable readmission burden.
SELECT
    measure_name,
    ROUND(AVG(predicted_readmission_rate - expected_readmission_rate), 3) AS avg_gap,
    ROUND(AVG(predicted_readmission_rate), 2) AS avg_predicted_rate,
    ROUND(AVG(expected_readmission_rate), 2) AS avg_expected_rate
FROM readmissions
WHERE predicted_readmission_rate IS NOT NULL
  AND expected_readmission_rate IS NOT NULL
GROUP BY measure_name
ORDER BY avg_gap DESC;

-- 7. Data completeness check: how many facility-measure records were
--    suppressed by CMS for low volume ("Too Few to Report" / N/A)?
SELECT
    state,
    COUNT(*) AS total_records,
    SUM(CASE WHEN excess_readmission_ratio IS NULL THEN 1 ELSE 0 END) AS suppressed,
    ROUND(100.0 * SUM(CASE WHEN excess_readmission_ratio IS NULL THEN 1 ELSE 0 END)
          / COUNT(*), 1) AS pct_suppressed
FROM readmissions
GROUP BY state
ORDER BY pct_suppressed DESC;
