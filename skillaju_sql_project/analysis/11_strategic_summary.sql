-- Business question: Which measurable gaps should be prioritized for growth, quality, and retention?
-- Grain: course and segment scorecards. This file creates evidence tables for recommendations; it does not fabricate conclusions.
-- Tables: courses, enrollments, students.

-- Course opportunity matrix: demand, quality, learning outcome, and potential booking value.
WITH perf AS (
 SELECT c.course_id,c.title,c.category,c.status,c.avg_rating,c.price_idr,COUNT(e.enrollment_id) AS enrollments,
        ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/COUNT(*),2) AS completion_rate_pct,
        c.price_idr*COUNT(e.enrollment_id) AS potential_booking_value_idr
 FROM courses c LEFT JOIN enrollments e USING(course_id) WHERE c.status='published'
 GROUP BY c.course_id,c.title,c.category,c.status,c.avg_rating,c.price_idr
), q AS (
 SELECT *,NTILE(4) OVER(ORDER BY enrollments) AS demand_q,NTILE(4) OVER(ORDER BY avg_rating) AS rating_q,
           NTILE(4) OVER(ORDER BY completion_rate_pct) AS completion_q,NTILE(4) OVER(ORDER BY potential_booking_value_idr) AS value_q
 FROM perf
)
SELECT *,CASE
 WHEN demand_q=4 AND completion_q=1 THEN 'demand growth constrained by completion'
 WHEN demand_q=4 AND rating_q=1 THEN 'high demand / rating review'
 WHEN demand_q=1 AND rating_q=4 THEN 'quality strength / promotion opportunity'
 WHEN demand_q=4 AND value_q=4 THEN 'commercial priority'
 ELSE 'monitor' END AS opportunity_flag
FROM q ORDER BY CASE WHEN demand_q=4 AND completion_q=1 THEN 1 WHEN demand_q=4 AND rating_q=1 THEN 2 WHEN demand_q=1 AND rating_q=4 THEN 3 WHEN demand_q=4 AND value_q=4 THEN 4 ELSE 5 END, enrollments DESC;

-- Segment scorecard for targeted acquisition/retention discussions.
SELECT s.acquisition_source,s.plan_type,COUNT(*) AS enrollments,COUNT(DISTINCT s.student_id) AS learners,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/COUNT(*),2) AS completion_rate_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.certificate_issued)/COUNT(*),2) AS certification_rate_pct
FROM enrollments e JOIN students s USING(student_id)
GROUP BY s.acquisition_source,s.plan_type HAVING COUNT(*)>=30
ORDER BY completion_rate_pct DESC,enrollments DESC;

-- Executive validation reminder: potential booking value is a listed-price proxy, not actual revenue.
SELECT SUM(c.price_idr*course_enrollments.enrollments) AS total_potential_booking_value_idr
FROM courses c JOIN (SELECT course_id,COUNT(*) AS enrollments FROM enrollments GROUP BY course_id) course_enrollments USING(course_id)
WHERE c.status='published';
