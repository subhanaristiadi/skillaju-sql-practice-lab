-- Business question: Which enrollments are plausible re-engagement candidates using an explicit, non-causal proxy?
-- Grain: enrollment.
-- Tables: enrollments, students, courses.
-- Proxy definition: incomplete enrollment AND last access is >90 days before the maximum recorded last_accessed date.
-- This is a descriptive prioritization rule, not a diagnosis of disengagement.

WITH anchor AS (SELECT MAX(last_accessed) AS max_last_accessed FROM enrollments),
flagged AS (
 SELECT e.enrollment_id,e.student_id,e.course_id,e.completion_pct,e.last_accessed,
        a.max_last_accessed, a.max_last_accessed-e.last_accessed AS days_since_last_access,
        CASE WHEN e.completion_pct<100 AND a.max_last_accessed-e.last_accessed>90 THEN TRUE ELSE FALSE END AS at_risk_proxy
 FROM enrollments e CROSS JOIN anchor a
)
SELECT at_risk_proxy,COUNT(*) AS enrollments,COUNT(DISTINCT student_id) AS learners,ROUND(AVG(completion_pct),2) AS avg_completion_pct
FROM flagged GROUP BY at_risk_proxy ORDER BY at_risk_proxy DESC;

WITH anchor AS (SELECT MAX(last_accessed) AS max_last_accessed FROM enrollments), flagged AS (
 SELECT e.*,a.max_last_accessed
 FROM enrollments e CROSS JOIN anchor a
 WHERE e.completion_pct<100 AND a.max_last_accessed-e.last_accessed>90
)
SELECT c.course_id,c.title,COUNT(*) AS at_risk_enrollments,ROUND(AVG(f.completion_pct),2) AS avg_completion_pct
FROM flagged f JOIN courses c USING(course_id) GROUP BY c.course_id,c.title
ORDER BY at_risk_enrollments DESC;

SELECT s.acquisition_source,s.plan_type,COUNT(*) AS at_risk_enrollments,COUNT(DISTINCT s.student_id) AS learners
FROM enrollments e JOIN students s USING(student_id)
CROSS JOIN (SELECT MAX(last_accessed) AS max_last_accessed FROM enrollments) a
WHERE e.completion_pct<100 AND a.max_last_accessed-e.last_accessed>90
GROUP BY s.acquisition_source,s.plan_type HAVING COUNT(*)>=10
ORDER BY at_risk_enrollments DESC;

-- Low completion distribution.
SELECT CASE WHEN completion_pct=0 THEN '0%' WHEN completion_pct<25 THEN '1-24%' WHEN completion_pct<50 THEN '25-49%'
            WHEN completion_pct<75 THEN '50-74%' WHEN completion_pct<100 THEN '75-99%' ELSE '100%' END AS completion_band,
       COUNT(*) AS enrollments
FROM enrollments GROUP BY 1 ORDER BY MIN(completion_pct);
