-- Business question: How do cohorts and time periods differ in learning outcomes and engagement recency?
-- Grain: enrollment cohort for learning outcomes; student registration cohort for learner-level comparisons.
-- Tables: enrollments, students, courses.

SELECT DATE_TRUNC('month',enrolled_date)::date AS enrollment_cohort,COUNT(*) AS enrollments,COUNT(DISTINCT student_id) AS learners,
       ROUND(100.0*COUNT(*) FILTER(WHERE completion_pct=100)/COUNT(*),2) AS completion_rate_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE certificate_issued)/COUNT(*),2) AS certification_rate_pct,
       ROUND(AVG(completion_pct),2) AS avg_completion_pct
FROM enrollments GROUP BY 1 ORDER BY 1;

SELECT DATE_TRUNC('quarter',enrolled_date)::date AS quarter,COUNT(*) AS enrollments,
       SUM(COUNT(*)) OVER(ORDER BY DATE_TRUNC('quarter',enrolled_date)) AS running_enrollments,
       LAG(COUNT(*)) OVER(ORDER BY DATE_TRUNC('quarter',enrolled_date)) AS prior_quarter_enrollments,
       ROUND(100.0*(COUNT(*)-LAG(COUNT(*)) OVER(ORDER BY DATE_TRUNC('quarter',enrolled_date))) / NULLIF(LAG(COUNT(*)) OVER(ORDER BY DATE_TRUNC('quarter',enrolled_date)),0),2) AS qoq_growth_pct
FROM enrollments GROUP BY 1 ORDER BY 1;

-- Registration cohorts by year: learner outcomes from their recorded enrollments.
SELECT DATE_TRUNC('year',s.registration_date)::date AS registration_cohort,COUNT(DISTINCT s.student_id) AS students,COUNT(e.enrollment_id) AS enrollments,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(e.enrollment_id) FILTER(WHERE e.completion_pct=100)/NULLIF(COUNT(e.enrollment_id),0),2) AS completion_rate_pct
FROM students s LEFT JOIN enrollments e USING(student_id) GROUP BY 1 ORDER BY 1;

-- Course creation timing vs demand: descriptive relationship at course grain.
SELECT DATE_TRUNC('year',c.created_date)::date AS creation_year,c.status,COUNT(*) AS courses,
       ROUND(AVG(recorded_enrollments),2) AS avg_recorded_enrollments,ROUND(AVG(c.avg_rating),2) AS avg_rating
FROM (SELECT c.*,COUNT(e.enrollment_id) AS recorded_enrollments FROM courses c LEFT JOIN enrollments e USING(course_id) GROUP BY c.course_id) c
GROUP BY 1,2 ORDER BY 1,2;

-- Recency proxy: days since last access relative to the dataset's maximum recorded access date, not current date.
WITH anchor AS (SELECT MAX(last_accessed) AS max_last_accessed FROM enrollments)
SELECT CASE WHEN max_last_accessed-last_accessed <= 30 THEN '0-30 days'
            WHEN max_last_accessed-last_accessed <= 90 THEN '31-90 days'
            WHEN max_last_accessed-last_accessed <= 180 THEN '91-180 days' ELSE '181+ days' END AS recency_band,
       COUNT(*) AS enrollments,ROUND(AVG(completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE completion_pct=100)/COUNT(*),2) AS completion_rate_pct
FROM enrollments CROSS JOIN anchor GROUP BY 1 ORDER BY MIN(max_last_accessed-last_accessed);
