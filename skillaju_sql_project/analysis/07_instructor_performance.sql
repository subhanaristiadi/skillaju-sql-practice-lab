-- Business question: Which instructors combine quality, reach, and learner outcomes?
-- Grain: course for course portfolio; enrollment for demand/outcomes; instructor for final scorecard.
-- Tables: instructors, courses, enrollments.

SELECT i.instructor_id,i.name,i.expertise,i.courses_count,i.avg_rating,
       COUNT(DISTINCT c.course_id) AS recorded_courses,COUNT(e.enrollment_id) AS enrollments,
       ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/NULLIF(COUNT(*),0),2) AS completion_rate_pct
FROM instructors i LEFT JOIN courses c ON c.instructor_id=i.instructor_id AND c.status='published'
LEFT JOIN enrollments e ON e.course_id=c.course_id
GROUP BY i.instructor_id,i.name,i.expertise,i.courses_count,i.avg_rating
ORDER BY enrollments DESC;

-- Rank instructors within expertise by recorded reach and rating.
WITH perf AS (
 SELECT i.instructor_id,i.name,i.expertise,i.avg_rating,COUNT(DISTINCT c.course_id) AS courses,COUNT(e.enrollment_id) AS enrollments,
        COALESCE(AVG(e.completion_pct),0) AS avg_completion_pct
 FROM instructors i LEFT JOIN courses c ON c.instructor_id=i.instructor_id AND c.status='published'
 LEFT JOIN enrollments e ON e.course_id=c.course_id
 GROUP BY i.instructor_id,i.name,i.expertise,i.avg_rating
)
SELECT *,RANK() OVER(PARTITION BY expertise ORDER BY enrollments DESC) AS reach_rank,
       RANK() OVER(PARTITION BY expertise ORDER BY avg_rating DESC) AS rating_rank
FROM perf ORDER BY expertise,reach_rank;

-- Instructor benchmark: compare each instructor to the average of instructors with published-course enrollment records.
WITH perf AS (
 SELECT i.instructor_id,i.name,i.avg_rating,COUNT(e.enrollment_id) AS enrollments,
        AVG(e.completion_pct) AS avg_completion_pct
 FROM instructors i LEFT JOIN courses c ON c.instructor_id=i.instructor_id AND c.status='published'
 LEFT JOIN enrollments e ON e.course_id=c.course_id
 GROUP BY i.instructor_id,i.name,i.avg_rating
), bench AS (SELECT AVG(enrollments) AS avg_enrollments,AVG(avg_completion_pct) AS avg_completion FROM perf WHERE enrollments>0)
SELECT p.*,b.avg_enrollments,b.avg_completion,
       CASE WHEN p.enrollments>b.avg_enrollments AND p.avg_rating>(SELECT AVG(avg_rating) FROM perf WHERE enrollments>0) THEN 'strong reach + rating'
            WHEN p.enrollments<b.avg_enrollments AND p.avg_rating>(SELECT AVG(avg_rating) FROM perf WHERE enrollments>0) THEN 'high quality / limited reach'
            WHEN p.enrollments>b.avg_enrollments AND p.avg_rating<(SELECT AVG(avg_rating) FROM perf WHERE enrollments>0) THEN 'high reach / rating review'
            ELSE 'other' END AS profile
FROM perf p CROSS JOIN bench b ORDER BY p.enrollments DESC;
