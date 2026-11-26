-- Business question: Which acquisition and learner segments combine scale with stronger learning outcomes?
-- Grain: student for registration counts; enrollment for enrollment/outcome counts.
-- Tables: students, enrollments.

SELECT acquisition_source, COUNT(*) AS registered_students
FROM students GROUP BY acquisition_source ORDER BY registered_students DESC;

SELECT s.acquisition_source, COUNT(*) AS enrollments, COUNT(DISTINCT e.student_id) AS unique_learners,
       ROUND(100.0 * COUNT(*) FILTER (WHERE e.completion_pct = 100) / NULLIF(COUNT(*),0),2) AS completion_rate_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE e.certificate_issued) / NULLIF(COUNT(*),0),2) AS certification_rate_pct
FROM enrollments e JOIN students s USING (student_id)
GROUP BY s.acquisition_source ORDER BY enrollments DESC;

SELECT s.plan_type, COUNT(*) AS enrollments, COUNT(DISTINCT e.student_id) AS unique_learners,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE e.completion_pct = 100) / NULLIF(COUNT(*),0),2) AS completion_rate_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE e.certificate_issued) / NULLIF(COUNT(*),0),2) AS certification_rate_pct
FROM enrollments e JOIN students s USING (student_id)
GROUP BY s.plan_type ORDER BY completion_rate_pct DESC;

-- Acquisition source x plan: scale and outcomes in one segmentation view.
SELECT s.acquisition_source, s.plan_type, COUNT(*) AS enrollments, COUNT(DISTINCT e.student_id) AS learners,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE e.completion_pct = 100) / NULLIF(COUNT(*),0),2) AS completion_rate_pct
FROM enrollments e JOIN students s USING (student_id)
GROUP BY s.acquisition_source, s.plan_type
HAVING COUNT(*) >= 30
ORDER BY completion_rate_pct DESC, enrollments DESC;

-- Age bands: explicitly defined descriptive segmentation.
SELECT CASE WHEN age < 25 THEN '<25' WHEN age < 35 THEN '25-34' ELSE '35+' END AS age_group,
       COUNT(DISTINCT s.student_id) AS students, COUNT(e.enrollment_id) AS enrollments,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct
FROM students s LEFT JOIN enrollments e USING (student_id)
GROUP BY 1 ORDER BY 1;
