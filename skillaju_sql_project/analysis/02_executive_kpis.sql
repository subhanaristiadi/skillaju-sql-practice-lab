-- Business question: What is the overall performance profile of SKILLAJU?
-- Grain: enrollment for learning KPIs; quiz attempt for assessment KPI; course/student/instructor for inventory counts.
-- Tables: students, courses, instructors, enrollments, quiz_results.

SELECT
    (SELECT COUNT(*) FROM students) AS students,
    (SELECT COUNT(*) FROM enrollments) AS enrollments,
    (SELECT COUNT(*) FROM courses) AS courses,
    (SELECT COUNT(*) FROM instructors) AS instructors,
    (SELECT COUNT(*) FROM quiz_results) AS quiz_attempts;

SELECT
    COUNT(*) AS enrollments,
    COUNT(DISTINCT student_id) AS unique_learners,
    ROUND(100.0 * COUNT(*) FILTER (WHERE completion_pct = 100) / NULLIF(COUNT(*),0), 2) AS completion_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE certificate_issued) / NULLIF(COUNT(*),0), 2) AS certification_rate_pct,
    ROUND(AVG(completion_pct), 2) AS avg_completion_pct
FROM enrollments;

SELECT
    ROUND(AVG(score), 2) AS avg_quiz_score,
    ROUND(100.0 * COUNT(*) FILTER (WHERE passed) / NULLIF(COUNT(*),0), 2) AS quiz_pass_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE attempt_number > 1) / NULLIF(COUNT(*),0), 2) AS retry_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE attempt_number = 1 AND passed) / NULLIF(COUNT(*) FILTER (WHERE attempt_number = 1),0), 2) AS first_attempt_pass_rate_pct
FROM quiz_results;

-- Monthly enrollment trend.
SELECT DATE_TRUNC('month', enrolled_date)::date AS month, COUNT(*) AS enrollments, COUNT(DISTINCT student_id) AS unique_learners
FROM enrollments
GROUP BY 1 ORDER BY 1;
