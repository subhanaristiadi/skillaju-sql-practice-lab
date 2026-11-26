-- Business question: How do price points relate to demand and potential booking value?
-- Grain: enrollment joined to one course; one enrollment contributes one listed-price booking-value proxy.
-- Tables: courses, enrollments. Potential booking value is not actual revenue.

SELECT c.course_id,c.title,c.category,c.price_idr,COUNT(e.enrollment_id) AS enrollments,
       c.price_idr*COUNT(e.enrollment_id) AS potential_booking_value_idr,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct
FROM courses c LEFT JOIN enrollments e USING(course_id)
WHERE c.status='published' GROUP BY c.course_id,c.title,c.category,c.price_idr
ORDER BY potential_booking_value_idr DESC;

SELECT c.category,COUNT(e.enrollment_id) AS enrollments,
       SUM(c.price_idr) AS potential_booking_value_idr,
       ROUND(AVG(c.price_idr),0) AS avg_listed_price_idr
FROM courses c JOIN enrollments e USING(course_id)
WHERE c.status='published' GROUP BY c.category ORDER BY potential_booking_value_idr DESC;

-- Descriptive price bands.
SELECT CASE WHEN price_idr=0 THEN 'free' WHEN price_idr<200000 THEN '<200k' WHEN price_idr<400000 THEN '200k-399k' ELSE '400k+' END AS price_band,
       COUNT(DISTINCT c.course_id) AS courses,COUNT(e.enrollment_id) AS enrollments,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct
FROM courses c LEFT JOIN enrollments e USING(course_id)
WHERE c.status='published' GROUP BY 1 ORDER BY MIN(price_idr);

-- Price vs enrollment at course grain: rank and correlation are descriptive only.
SELECT ROUND(CORR(price_idr::numeric, enrollments::numeric),3) AS price_enrollment_corr,
       ROUND(CORR(price_idr::numeric, avg_completion_pct::numeric),3) AS price_completion_corr
FROM (SELECT c.price_idr,COUNT(e.enrollment_id) AS enrollments,AVG(e.completion_pct) AS avg_completion_pct
      FROM courses c LEFT JOIN enrollments e USING(course_id) WHERE c.status='published' GROUP BY c.course_id,c.price_idr) x;

-- Strong demand + rating + potential booking value shortlist.
WITH p AS (
 SELECT c.course_id,c.title,c.avg_rating,c.price_idr,COUNT(e.enrollment_id) AS enrollments,
        c.price_idr*COUNT(e.enrollment_id) AS potential_booking_value_idr,
        NTILE(4) OVER(ORDER BY COUNT(e.enrollment_id)) AS demand_q,
        NTILE(4) OVER(ORDER BY c.avg_rating) AS rating_q,
        NTILE(4) OVER(ORDER BY c.price_idr*COUNT(e.enrollment_id)) AS value_q
 FROM courses c LEFT JOIN enrollments e USING(course_id) WHERE c.status='published'
 GROUP BY c.course_id,c.title,c.avg_rating,c.price_idr
)
SELECT * FROM p WHERE demand_q=4 AND rating_q=4 AND value_q=4 ORDER BY potential_booking_value_idr DESC;
