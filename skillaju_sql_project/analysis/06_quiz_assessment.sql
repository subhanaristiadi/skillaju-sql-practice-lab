-- Business question: Which assessments are difficult, and do retries improve performance?
-- Grain: one row per quiz attempt. Enrollment counts must not be inferred from quiz rows.
-- Tables: quiz_results, enrollments, courses when course context is needed.

SELECT ROUND(AVG(score),2) AS avg_score, ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct,
       ROUND(100.0*COUNT(*) FILTER(WHERE attempt_number>1)/COUNT(*),2) AS retry_rate_pct
FROM quiz_results;

SELECT quiz_number,COUNT(*) AS attempts,ROUND(AVG(score),2) AS avg_score,
       ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct
FROM quiz_results GROUP BY quiz_number ORDER BY quiz_number;

SELECT c.course_id,c.title,COUNT(*) AS attempts,ROUND(AVG(q.score),2) AS avg_score,
       ROUND(100.0*COUNT(*) FILTER(WHERE q.passed)/COUNT(*),2) AS pass_rate_pct
FROM quiz_results q JOIN courses c USING(course_id)
WHERE c.status='published' GROUP BY c.course_id,c.title HAVING COUNT(*)>=30 ORDER BY pass_rate_pct, attempts DESC;

-- Compare first attempts with later attempts by quiz identity within an enrollment.
WITH first_attempt AS (
 SELECT enrollment_id,quiz_number,score AS first_score,passed AS first_passed
 FROM quiz_results WHERE attempt_number=1
), later AS (
 SELECT enrollment_id,quiz_number,AVG(score) AS later_avg_score,
        100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*) AS later_pass_rate_pct
 FROM quiz_results WHERE attempt_number>1 GROUP BY enrollment_id,quiz_number
)
SELECT COUNT(*) AS retried_quizzes,ROUND(AVG(later.later_avg_score-first_attempt.first_score),2) AS avg_score_change,
       ROUND(100.0*AVG((later.later_pass_rate_pct/100.0)::numeric - CASE WHEN first_attempt.first_passed THEN 1 ELSE 0 END),2) AS avg_pass_status_change_pp
FROM first_attempt JOIN later USING(enrollment_id,quiz_number);

-- First-attempt vs later-attempt pass rates at attempt grain.
SELECT CASE WHEN attempt_number=1 THEN 'first attempt' ELSE 'retry' END AS attempt_group,
       COUNT(*) AS attempts,ROUND(AVG(score),2) AS avg_score,ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct
FROM quiz_results GROUP BY 1 ORDER BY 1;

-- Courses with strong completion but weak quiz performance, using enrollment-level completion and quiz-level pass rate separately.
WITH course_completion AS (
 SELECT course_id,COUNT(*) AS enrollments,ROUND(100.0*COUNT(*) FILTER(WHERE completion_pct=100)/COUNT(*),2) AS completion_rate_pct
 FROM enrollments GROUP BY course_id
), course_quiz AS (
 SELECT course_id,COUNT(*) AS attempts,ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS quiz_pass_rate_pct
 FROM quiz_results GROUP BY course_id
)
SELECT c.title,cc.enrollments,cc.completion_rate_pct,cq.attempts,cq.quiz_pass_rate_pct
FROM course_completion cc JOIN course_quiz cq USING(course_id) JOIN courses c USING(course_id)
WHERE c.status='published' AND cc.enrollments>=20
ORDER BY (cc.completion_rate_pct-cq.quiz_pass_rate_pct) DESC;
