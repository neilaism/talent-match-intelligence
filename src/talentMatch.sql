-- join employee data and their dims
CREATE TABLE employee_dim_joined AS
SELECT 
    e.employee_id,
    e.fullname,
    e.position_id,
    p.name AS position_name,
    e.directorate_id,
    d.name AS directorate_name,
    e.grade_id,
    g.name AS grade_name
FROM employees e
LEFT JOIN dim_directorates d ON e.directorate_id = d.directorate_id
LEFT JOIN dim_grades g ON e.grade_id = g.grade_id
LEFT JOIN dim_positions p ON e.position_id = p.position_id;

-- check data
SELECT * FROM employee_dim_joined LIMIT 5;

-- unpivot employee_success_score to convert wide to long format
CREATE TABLE employee_score_long AS
SELECT employee_id, 'faxtor' AS tv, faxtor::numeric AS score FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'gtq', gtq::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'tiki', tiki::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'Papi_O', "Papi_O"::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'Papi_P', "Papi_P"::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'Papi_N', "Papi_N"::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'futuristic', futuristic::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'focus', focus::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'responsibility', responsibility::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'relator', relator::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'SEA', "SEA"::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'QDD', "QDD"::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'FTC', "FTC"::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'grade_name', grade_name::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'education_level', education_level::numeric FROM employee_success_score
  UNION ALL
  SELECT employee_id, 'years_of_service_months', years_of_service_months::numeric FROM employee_success_score;

-- check data
SELECT * FROM employee_score_long LIMIT 5;

-- mapping tv to tgv
CREATE TABLE employee_score_long_tgv AS
SELECT 
    l.employee_id,
    t.tgv AS tgv_name,
    l.tv AS tv_name,
    l.score AS user_score
FROM employee_score_long l
LEFT JOIN tv_to_tgv t 
    ON LOWER(l.tv) = LOWER(t.tv);

-- check data
SELECT * FROM employee_score_long_tgv LIMIT 5;

-- merge employee score and its metadata
CREATE TABLE employee_scores AS
SELECT 
    e.employee_id,
    e.grade_name AS grade,
    e.directorate_name AS directorate,
    e.position_name AS role,
    l.tgv_name,
    l.tv_name,
    l.user_score
FROM employee_dim_joined e
JOIN employee_score_long_tgv l
    ON e.employee_id = l.employee_id;

-- check data
SELECT * FROM employee_scores LIMIT 5;

-- identify selected_talent_ids
CREATE TABLE benchmark_source AS 
    SELECT DISTINCT employee_id
    FROM employee_success_score
    WHERE is_top = TRUE;

-- calculate baseline score using median of selected talent scores
CREATE TABLE baseline_score_calc AS
    SELECT
        e.directorate,
        e.role,
        e.grade,
        e.tgv_name,
        e.tv_name,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.user_score) AS baseline_score
    FROM employee_scores e
    JOIN benchmark_source b
      ON e.employee_id = b.employee_id
    GROUP BY e.directorate, e.role, e.grade, e.tgv_name, e.tv_name; 

-- join all employees to these median baseline score
CREATE TABLE expected_output AS 
    SELECT 
        e.employee_id,
        e.directorate,
        e.role,
        e.grade,
        e.tgv_name,
        e.tv_name,
        b.baseline_score,
        e.user_score,
        ROUND(LEAST(e.user_score / NULLIF(b.baseline_score, 0), 1.0)::numeric, 4) AS tv_match_rate
    FROM employee_scores e
    JOIN baseline_score_calc b
      ON LOWER(TRIM(e.role)) = LOWER(TRIM(b.role))
     AND LOWER(TRIM(e.grade)) = LOWER(TRIM(b.grade))
     AND LOWER(TRIM(e.tv_name)) = LOWER(TRIM(b.tv_name));

-- add 2 columns: tgv_match_rate and final_match_rate
DROP TABLE IF EXISTS expected_output_final;

CREATE TABLE expected_output_final AS
SELECT 
    e.employee_id,
    e.directorate,
    e.role,
    e.grade,
    e.tgv_name,
    e.tv_name,
    e.baseline_score,
    e.user_score,
    e.tv_match_rate,
    ROUND((AVG(e.tv_match_rate) OVER (PARTITION BY e.employee_id, e.tgv_name))::numeric, 4) AS tgv_match_rate,
    ROUND((
        SUM(
            COALESCE(e.tv_match_rate, 0) 
            * COALESCE(tvw.tv_weight, 0) 
            * COALESCE(tgvw.tgv_weights, 0)
        ) OVER (PARTITION BY e.employee_id)
    )::numeric, 4) AS final_match_rate
FROM expected_output e
LEFT JOIN tv_weights tvw 
    ON LOWER(TRIM(e.tv_name)) = LOWER(TRIM(tvw.tv))
LEFT JOIN tgv_weights tgvw 
    ON LOWER(TRIM(e.tgv_name)) = LOWER(TRIM(tgvw.tgv))
ORDER BY final_match_rate DESC;


-- Indexes for fast dashboard filters
CREATE INDEX IF NOT EXISTS idx_expected_role ON expected_output_final (role);
CREATE INDEX IF NOT EXISTS idx_expected_grade ON expected_output_final (grade);
CREATE INDEX IF NOT EXISTS idx_expected_employee ON expected_output_final (employee_id);
CREATE INDEX IF NOT EXISTS idx_expected_tgv ON expected_output_final (tgv_name);

