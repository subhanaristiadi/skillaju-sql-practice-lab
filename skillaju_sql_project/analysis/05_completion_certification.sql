-- Business question: Where are completion and certification outcomes strongest or weakest?
-- Grain: enrollment. Do not join quiz_results here unless the analysis explicitly needs quiz-level data.
-- Tables: enrollments, courses, students.

SELECT c.course_id,c.title,c.category,c.level,COUNT(e.enrollment_id) AS enrollments,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/NULLIF(COUNT(*),0),2) AS completion_rate_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.certificate_issued)/NULLIF(COUNT(*),0),2) AS certification_rate_pct
FROM enrollments e JOIN courses c USING(course_id)
WHERE c.status='published' GROUP BY c.course_id,c.title,c.category,c.level
HAVING COUNT(*) >= 20 ORDER BY completion_rate_pct DESC, enrollments DESC;

SELECT c.category,c.level,COUNT(*) AS enrollments,ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/NULLIF(COUNT(*),0),2) AS completion_rate_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.certificate_issued)/NULLIF(COUNT(*),0),2) AS certification_rate_pct
FROM enrollments e JOIN courses c USING(course_id)
WHERE c.status='published' GROUP BY c.category,c.level ORDER BY completion_rate_pct DESC;

-- Enrollment volume vs completion: prioritize courses with enough observations.
WITH perf AS (
 SELECT c.course_id,c.title,COUNT(*) AS enrollments,ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
        ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/COUNT(*),2) AS completion_rate_pct
 FROM enrollments e JOIN courses c USING(course_id) WHERE c.status='published' GROUP BY c.course_id,c.title
), ranked AS (
 SELECT *, NTILE(4) OVER(ORDER BY enrollments) AS demand_quartile, NTILE(4) OVER(ORDER BY completion_rate_pct) AS completion_quartile FROM perf
)
SELECT * FROM ranked WHERE demand_quartile=4 AND completion_quartile=1 ORDER BY enrollments DESC;

-- Time-to-completion only where completion_date is present; missing dates are not imputed.
SELECT COUNT(*) FILTER (WHERE completion_date IS NOT NULL) AS completed_with_date,
       ROUND(AVG(completion_date-enrolled_date) FILTER (WHERE completion_date IS NOT NULL),2) AS avg_days_to_completion,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY completion_date-enrolled_date) FILTER (WHERE completion_date IS NOT NULL) AS median_days_to_completion
FROM enrollments;

SELECT s.acquisition_source,s.plan_type,COUNT(*) AS enrollments,ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/COUNT(*),2) AS completion_rate_pct
FROM enrollments e JOIN students s USING(student_id) GROUP BY s.acquisition_source,s.plan_type
HAVING COUNT(*) >= 30 ORDER BY completion_rate_pct DESC;
