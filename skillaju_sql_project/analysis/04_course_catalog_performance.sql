-- Business question: Which courses/categories show the strongest demand and where are demand-quality gaps?
-- Grain: course for catalog attributes; enrollment for current recorded demand.
-- Tables: courses, enrollments. Draft courses are retained for catalog validation but published-only metrics are used for customer-facing comparisons.

WITH course_perf AS (
    SELECT c.course_id, c.title, c.category, c.level, c.status, c.price_idr, c.duration_hours, c.avg_rating,
           c.total_enrolled AS stored_total_enrolled, COUNT(e.enrollment_id) AS recorded_enrollments,
           ROUND(100.0 * COUNT(e.enrollment_id) / NULLIF(SUM(COUNT(e.enrollment_id)) OVER (),0),2) AS enrollment_share_pct
    FROM courses c LEFT JOIN enrollments e USING (course_id)
    GROUP BY c.course_id, c.title, c.category, c.level, c.status, c.price_idr, c.duration_hours, c.avg_rating, c.total_enrolled
)
SELECT * FROM course_perf WHERE status = 'published' ORDER BY recorded_enrollments DESC;

SELECT category, COUNT(*) AS courses, SUM(recorded_enrollments) AS enrollments,
       ROUND(100.0 * SUM(recorded_enrollments) / NULLIF(SUM(SUM(recorded_enrollments)) OVER (),0),2) AS enrollment_share_pct,
       ROUND(AVG(avg_rating),2) AS avg_course_rating
FROM (SELECT c.*, COUNT(e.enrollment_id) AS recorded_enrollments FROM courses c LEFT JOIN enrollments e USING(course_id) GROUP BY c.course_id) x
WHERE status='published' GROUP BY category ORDER BY enrollments DESC;

SELECT level, COUNT(*) AS courses, SUM(recorded_enrollments) AS enrollments, ROUND(AVG(avg_rating),2) AS avg_rating
FROM (SELECT c.*, COUNT(e.enrollment_id) AS recorded_enrollments FROM courses c LEFT JOIN enrollments e USING(course_id) GROUP BY c.course_id) x
WHERE status='published' GROUP BY level ORDER BY enrollments DESC;

-- High-demand/low-rating and high-rating/low-demand candidates using within-published-catalog quartiles.
WITH p AS (
 SELECT c.course_id,c.title,c.category,c.avg_rating,COUNT(e.enrollment_id) AS enrollments,
        NTILE(4) OVER (ORDER BY COUNT(e.enrollment_id)) AS demand_quartile,
        NTILE(4) OVER (ORDER BY c.avg_rating) AS rating_quartile
 FROM courses c LEFT JOIN enrollments e USING(course_id) WHERE c.status='published'
 GROUP BY c.course_id,c.title,c.category,c.avg_rating
)
SELECT *, CASE WHEN demand_quartile=4 AND rating_quartile=1 THEN 'high demand / low rating'
               WHEN demand_quartile=1 AND rating_quartile=4 THEN 'high rating / low demand' END AS gap_type
FROM p WHERE (demand_quartile=4 AND rating_quartile=1) OR (demand_quartile=1 AND rating_quartile=4)
ORDER BY gap_type, enrollments DESC;

-- Price/duration association is descriptive, not causal.
SELECT ROUND(c.price_idr / 100000.0) * 100000 AS price_band_idr,
       COUNT(DISTINCT c.course_id) AS courses, COUNT(e.enrollment_id) AS enrollments, ROUND(AVG(c.duration_hours),2) AS avg_duration_hours
FROM courses c LEFT JOIN enrollments e USING(course_id)
WHERE c.status='published' GROUP BY 1 ORDER BY 1;
