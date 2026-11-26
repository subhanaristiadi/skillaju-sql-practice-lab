"""Build all 75 exercises from the authoritative business-question Markdown."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = []

def add(title, sql, grain, note='', difficulty='Intermediate'):
    SPECS.append(dict(title=title, sql=sql.strip().rstrip(';')+';', grain=grain,
                      note=note, difficulty=difficulty))

RATE = "ROUND(100.0 * COUNT(*) FILTER (WHERE completion_pct = 100) / NULLIF(COUNT(*),0),2)"
CERT = "ROUND(100.0 * COUNT(*) FILTER (WHERE certificate_issued) / NULLIF(COUNT(*),0),2)"
CP = """WITH course_perf AS (
 SELECT c.course_id,c.title,c.category,c.level,c.status,c.instructor_id,c.price_idr,
        c.duration_hours,c.avg_rating,c.created_date,
        COUNT(e.enrollment_id) AS enrollments,COUNT(DISTINCT e.student_id) AS learners,
        COUNT(e.enrollment_id) FILTER(WHERE e.completion_pct=100) AS completed_enrollments,
        ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
        ROUND(100.0*COUNT(e.enrollment_id) FILTER(WHERE e.completion_pct=100)/NULLIF(COUNT(e.enrollment_id),0),2) AS completion_rate_pct,
        ROUND(100.0*COUNT(e.enrollment_id) FILTER(WHERE e.certificate_issued)/NULLIF(COUNT(e.enrollment_id),0),2) AS certification_rate_pct,
        c.price_idr::bigint*COUNT(e.enrollment_id) AS potential_booking_value_idr
 FROM courses c LEFT JOIN enrollments e USING(course_id)
 GROUP BY c.course_id,c.title,c.category,c.level,c.status,c.instructor_id,c.price_idr,c.duration_hours,c.avg_rating,c.created_date
)"""
SP = """WITH segment_perf AS (
 SELECT s.acquisition_source,s.plan_type,COUNT(*) AS enrollments,
        COUNT(DISTINCT s.student_id) AS learners,
        ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,
        ROUND(100.0*COUNT(*) FILTER(WHERE e.completion_pct=100)/COUNT(*),2) AS completion_rate_pct,
        ROUND(100.0*COUNT(*) FILTER(WHERE e.certificate_issued)/COUNT(*),2) AS certification_rate_pct
 FROM enrollments e JOIN students s USING(student_id)
 GROUP BY s.acquisition_source,s.plan_type
)"""
QP = CP + """, quiz_perf AS (
 SELECT course_id,COUNT(*) AS attempts,ROUND(AVG(score),2) AS avg_score,
        ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct
 FROM quiz_results GROUP BY course_id
)"""
IP = CP + """, instructor_perf AS (
 SELECT i.instructor_id,i.name,i.expertise,i.avg_rating,COUNT(c.course_id) AS courses,
        COALESCE(SUM(c.enrollments),0) AS enrollments,
        ROUND(100.0*SUM(c.completed_enrollments)/NULLIF(SUM(c.enrollments),0),2) AS completion_rate_pct
 FROM instructors i LEFT JOIN course_perf c USING(instructor_id)
 GROUP BY i.instructor_id,i.name,i.expertise,i.avg_rating
)"""
ANCHOR = "WITH anchor AS (SELECT MAX(last_accessed) AS as_of_date FROM enrollments)"
RISK = "e.completion_pct<100 AND a.as_of_date-e.last_accessed>90"
BASE_NOTE = "Completion = completion_pct = 100; certification = certificate_issued; rates are percentages rounded to 2 decimals. Counts use supplied enrollment rows, not courses.total_enrolled. Observational associations are not causal."
PUBLISHED = "Catalog recommendations include published courses only. High/low means above/below the unweighted mean of published course metrics, unless another rule is stated."

def course_query(columns, where='', order='enrollments DESC,course_id', limit=''):
    return CP+f" SELECT {columns} FROM course_perf {where} ORDER BY {order} {limit}"

def segment_query(dimension):
    return f"SELECT {dimension},COUNT(*) AS enrollments,COUNT(DISTINCT student_id) AS learners,{RATE} AS completion_rate_pct,{CERT} AS certification_rate_pct,ROUND(AVG(completion_pct),2) AS avg_completion_pct FROM enrollments JOIN students USING(student_id) GROUP BY {dimension} ORDER BY enrollments DESC,{dimension}"

# 1. Executive Performance (5)
add('Dataset inventory', "SELECT (SELECT COUNT(*) FROM students) AS students,(SELECT COUNT(*) FROM enrollments) AS enrollments,(SELECT COUNT(*) FROM courses) AS courses,(SELECT COUNT(*) FROM instructors) AS instructors,(SELECT COUNT(*) FROM quiz_results) AS quiz_attempts", 'One dataset snapshot', difficulty='Beginner')
add('Monthly enrollment trend', "SELECT DATE_TRUNC('month',enrolled_date)::date AS month,COUNT(*) AS enrollments FROM enrollments GROUP BY 1 ORDER BY 1", 'One calendar month', difficulty='Beginner')
add('Overall learning outcomes', f"SELECT {RATE} AS completion_rate_pct,{CERT} AS certification_rate_pct,ROUND(AVG(completion_pct),2) AS avg_completion_pct FROM enrollments", 'One dataset snapshot', difficulty='Beginner')
add('Dimensions with the largest outcome gaps', f"""WITH outcomes AS (
 SELECT 'plan_type' AS dimension,s.plan_type AS segment,e.completion_pct FROM enrollments e JOIN students s USING(student_id)
 UNION ALL SELECT 'acquisition_source',s.acquisition_source,e.completion_pct FROM enrollments e JOIN students s USING(student_id)
 UNION ALL SELECT 'city',s.city,e.completion_pct FROM enrollments e JOIN students s USING(student_id)
 UNION ALL SELECT 'category',c.category,e.completion_pct FROM enrollments e JOIN courses c USING(course_id)
 UNION ALL SELECT 'level',c.level,e.completion_pct FROM enrollments e JOIN courses c USING(course_id)
), rates AS (SELECT dimension,segment,{RATE} AS completion_rate_pct FROM outcomes GROUP BY 1,2)
 SELECT dimension,MIN(completion_rate_pct) AS lowest_completion_pct,MAX(completion_rate_pct) AS highest_completion_pct,MAX(completion_rate_pct)-MIN(completion_rate_pct) AS gap_pp FROM rates GROUP BY dimension ORDER BY gap_pp DESC,dimension""", 'One dimension', 'Compare completion-rate range across plan, source, city, category and level.', 'Advanced')
add('Platform strengths and weaknesses', f"SELECT c.category,COUNT(*) AS enrollments,{RATE} AS completion_rate_pct,{CERT} AS certification_rate_pct,ROUND(AVG(completion_pct),2) AS avg_completion_pct FROM enrollments e JOIN courses c USING(course_id) GROUP BY c.category ORDER BY completion_rate_pct DESC,c.category", 'One course category', 'Use the category scorecard as evidence; discuss strengths and weaknesses in personal notes.')

# 2. Learner Acquisition & Segmentation (8)
add('Registered students by acquisition source', 'SELECT acquisition_source,COUNT(*) AS students FROM students GROUP BY acquisition_source ORDER BY students DESC,acquisition_source', 'One acquisition source', difficulty='Beginner')
add('Enrollments by acquisition source', 'SELECT s.acquisition_source,COUNT(*) AS enrollments FROM enrollments e JOIN students s USING(student_id) GROUP BY s.acquisition_source ORDER BY enrollments DESC,s.acquisition_source', 'One acquisition source', difficulty='Beginner')
add('Learning outcomes by acquisition source', segment_query('acquisition_source'), 'One acquisition source')
add('Learning outcomes by learner plan', segment_query('plan_type'), 'One plan type')
add('Students and enrollments by city', 'SELECT s.city,COUNT(DISTINCT s.student_id) AS students,COUNT(e.enrollment_id) AS enrollments FROM students s LEFT JOIN enrollments e USING(student_id) GROUP BY s.city ORDER BY students DESC,s.city', 'One student city')
add('Age groups, course choice and completion', f"SELECT CASE WHEN s.age<25 THEN '18-24' WHEN s.age<35 THEN '25-34' ELSE '35-45' END AS age_group,c.category,COUNT(*) AS enrollments,{RATE} AS completion_rate_pct FROM enrollments e JOIN students s USING(student_id) JOIN courses c USING(course_id) GROUP BY 1,2 ORDER BY 1,2", 'One age group × category', 'Age bands: 18–24, 25–34, 35–45.')
add('Strongest acquisition source and plan combinations', SP+' SELECT acquisition_source,plan_type,enrollments,learners,completion_rate_pct,certification_rate_pct FROM segment_perf WHERE enrollments>=30 ORDER BY completion_rate_pct DESC,certification_rate_pct DESC,acquisition_source,plan_type', 'One acquisition source × plan', 'Require at least 30 enrollments; rank by completion then certification.')
add('Active but under-completing learner segments', SP+' SELECT acquisition_source,plan_type,enrollments,learners,avg_completion_pct,completion_rate_pct FROM segment_perf WHERE enrollments>(SELECT AVG(enrollments) FROM segment_perf) AND completion_rate_pct<(SELECT AVG(completion_rate_pct) FROM segment_perf) ORDER BY enrollments DESC,acquisition_source,plan_type', 'One acquisition source × plan', 'Active proxy = above-mean enrollment count; under-completing = below-mean segment completion rate. Activity frequency is unavailable.', 'Advanced')

# 3. Course Demand & Catalog (10)
add('Most popular courses', course_query('course_id,title,enrollments', "WHERE status='published'", limit='LIMIT 10'), 'One published course', 'Rank the top 10 by recorded enrollments; break ties by course_id.', 'Beginner')
add('Least popular courses', course_query('course_id,title,enrollments', "WHERE status='published'", 'enrollments,course_id', 'LIMIT 10'), 'One published course', 'Bottom 10 published courses including zero enrollments; break ties by course_id.', 'Beginner')
add('Learner demand by category', "SELECT c.category,COUNT(*) AS enrollments,COUNT(DISTINCT e.student_id) AS learners FROM enrollments e JOIN courses c USING(course_id) WHERE c.status='published' GROUP BY c.category ORDER BY learners DESC,c.category", 'One published course category')
add('Demand by course level', "SELECT c.level,COUNT(*) AS enrollments,COUNT(DISTINCT e.student_id) AS learners FROM enrollments e JOIN courses c USING(course_id) WHERE c.status='published' GROUP BY c.level ORDER BY enrollments DESC,c.level", 'One published course level')
add('Price, duration and course demand', course_query('course_id,title,price_idr,duration_hours,enrollments', "WHERE status='published'"), 'One published course', 'Compare course-level listed price, duration and recorded enrollments; discuss associations in notes.')
add('High-demand courses with low ratings', course_query('course_id,title,enrollments,avg_rating', "WHERE status='published' AND enrollments>(SELECT AVG(enrollments) FROM course_perf WHERE status='published') AND avg_rating<(SELECT AVG(avg_rating) FROM course_perf WHERE status='published')"), 'One published course', PUBLISHED)
add('Highly rated courses with low demand', course_query('course_id,title,enrollments,avg_rating', "WHERE status='published' AND enrollments<(SELECT AVG(enrollments) FROM course_perf WHERE status='published') AND avg_rating>(SELECT AVG(avg_rating) FROM course_perf WHERE status='published')", 'avg_rating DESC,course_id'), 'One published course', PUBLISHED)
add('Draft versus published catalog attributes', 'SELECT status,COUNT(*) AS courses,ROUND(AVG(price_idr),2) AS avg_price_idr,ROUND(AVG(duration_hours),2) AS avg_duration_hours,ROUND(AVG(avg_rating),2) AS avg_rating FROM courses GROUP BY status ORDER BY status', 'One course status', 'Include both draft and published courses. Attribute differences alone do not establish causation.')
add('Catalog representation by category and level', 'SELECT category,level,COUNT(*) AS courses,ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(),2) AS catalog_share_pct FROM courses GROUP BY category,level ORDER BY courses DESC,category,level', 'One category × level', 'All catalog courses; representation is a share of courses, not a market-demand benchmark.')
add('Course promotion and improvement priorities', course_query("course_id,title,enrollments,avg_rating,completion_rate_pct,CASE WHEN completion_rate_pct<(SELECT AVG(completion_rate_pct) FROM course_perf WHERE status='published') THEN 'improve completion' WHEN avg_rating<(SELECT AVG(avg_rating) FROM course_perf WHERE status='published') THEN 'review content' ELSE 'promotion candidate' END AS recommendation", "WHERE status='published'"), 'One published course', PUBLISHED+' Rule priority: low completion, low rating, otherwise promotion candidate.', 'Advanced')

# 4. Learning Completion & Certification (10)
add('Overall course completion rate', f'SELECT COUNT(*) AS enrollments,COUNT(*) FILTER(WHERE completion_pct=100) AS completed_enrollments,{RATE} AS completion_rate_pct FROM enrollments', 'One dataset snapshot', difficulty='Beginner')
add('Course completion ranking', course_query('course_id,title,enrollments,completion_rate_pct', 'WHERE enrollments>0', 'completion_rate_pct DESC,course_id'), 'One enrolled course', 'Include all statuses; return the complete ranking so both extremes are visible.')
add('Completion by category and level', f'SELECT c.category,c.level,COUNT(*) AS enrollments,{RATE} AS completion_rate_pct FROM enrollments e JOIN courses c USING(course_id) GROUP BY c.category,c.level ORDER BY completion_rate_pct DESC,c.category,c.level', 'One category × level')
add('High enrollment with low completion', course_query('course_id,title,enrollments,completion_rate_pct', "WHERE status='published' AND enrollments>(SELECT AVG(enrollments) FROM course_perf WHERE status='published') AND completion_rate_pct<(SELECT AVG(completion_rate_pct) FROM course_perf WHERE status='published')"), 'One published course', PUBLISHED)
add('Low enrollment with high completion', course_query('course_id,title,enrollments,completion_rate_pct', "WHERE status='published' AND enrollments<(SELECT AVG(enrollments) FROM course_perf WHERE status='published') AND completion_rate_pct>(SELECT AVG(completion_rate_pct) FROM course_perf WHERE status='published')", 'completion_rate_pct DESC,course_id'), 'One published course', PUBLISHED)
add('Time from enrollment to completion', 'SELECT COUNT(*) AS dated_completions,ROUND(AVG(completion_date-enrolled_date),2) AS avg_days_to_complete,PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY completion_date-enrolled_date) AS median_days_to_complete FROM enrollments WHERE completion_pct=100 AND completion_date IS NOT NULL AND completion_date>=enrolled_date', 'One dated-completion summary', 'Only 100% completed enrollments with non-null, non-negative elapsed dates. Do not impute dates.', 'Advanced')
add('Completion by plan type', segment_query('plan_type'), 'One plan type')
add('Completion by acquisition source', segment_query('acquisition_source'), 'One acquisition source')
add('Cities with high or low completion', segment_query('city'), 'One student city', 'Return every city ranked by enrollment count; interpret extremes with their sample size.')
add('Learner and course segments needing improvement', f'SELECT s.plan_type,c.category,COUNT(*) AS enrollments,{RATE} AS completion_rate_pct FROM enrollments e JOIN students s USING(student_id) JOIN courses c USING(course_id) GROUP BY s.plan_type,c.category HAVING COUNT(*)>=30 ORDER BY completion_rate_pct,s.plan_type,c.category', 'One plan × category', 'Require at least 30 enrollments; lowest completion first.')

# 5. Quiz & Assessment Performance (10)
add('Overall quiz scores and pass rate', 'SELECT COUNT(*) AS attempts,ROUND(AVG(score),2) AS avg_score,ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct FROM quiz_results', 'One quiz-attempt summary', difficulty='Beginner')
add('Assessment outcomes by course', "SELECT c.course_id,c.title,COUNT(*) AS attempts,ROUND(AVG(q.score),2) AS avg_score,ROUND(100.0*COUNT(*) FILTER(WHERE q.passed)/COUNT(*),2) AS pass_rate_pct FROM quiz_results q JOIN courses c USING(course_id) GROUP BY c.course_id,c.title ORDER BY pass_rate_pct,c.course_id", 'One course; quiz-attempt outcomes')
quiz_by_number = 'SELECT quiz_number,COUNT(*) AS attempts,ROUND(AVG(score),2) AS avg_score,ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct FROM quiz_results GROUP BY quiz_number'
add('Most difficult quiz numbers', quiz_by_number+' ORDER BY pass_rate_pct,quiz_number', 'One quiz sequence number', 'Difficulty proxy = lowest observed pass rate, aggregated across courses.')
add('Performance across quiz sequence', quiz_by_number+' ORDER BY quiz_number', 'One quiz sequence number', 'Sequence comparison is cross-sectional; it does not measure the same learners over time.')
add('How often learners retry quizzes', 'SELECT COUNT(*) AS attempts,COUNT(*) FILTER(WHERE attempt_number>1) AS retry_attempts,ROUND(100.0*COUNT(*) FILTER(WHERE attempt_number>1)/COUNT(*),2) AS retry_rate_pct,COUNT(DISTINCT student_id) FILTER(WHERE attempt_number>1) AS retrying_learners FROM quiz_results', 'One quiz-attempt summary', 'Retry rate = attempts numbered >1 / all attempts; not a percentage of learners.')
add('Score change after a quiz retry', "WITH first_attempt AS (SELECT enrollment_id,quiz_number,AVG(score) AS first_score FROM quiz_results WHERE attempt_number=1 GROUP BY 1,2),later AS (SELECT enrollment_id,quiz_number,AVG(score) AS later_score FROM quiz_results WHERE attempt_number>1 GROUP BY 1,2) SELECT COUNT(*) AS retried_quizzes,ROUND(AVG(later_score-first_score),2) AS avg_score_change FROM first_attempt JOIN later USING(enrollment_id,quiz_number)", 'One paired-retry summary', 'Pair by enrollment_id + quiz_number; average later attempts per quiz before comparing with first attempt. Association, not causal improvement.', 'Advanced')
add('First-attempt versus retry pass rate', "SELECT CASE WHEN attempt_number=1 THEN 'first attempt' ELSE 'retry' END AS attempt_group,COUNT(*) AS attempts,ROUND(AVG(score),2) AS avg_score,ROUND(100.0*COUNT(*) FILTER(WHERE passed)/COUNT(*),2) AS pass_rate_pct FROM quiz_results GROUP BY 1 ORDER BY 1", 'One attempt group')
def mismatch(condition):
    return QP+f" SELECT c.course_id,c.title,c.enrollments,c.completion_rate_pct,q.attempts,q.avg_score,q.pass_rate_pct FROM course_perf c JOIN quiz_perf q USING(course_id) WHERE c.status='published' AND {condition} ORDER BY c.course_id"
add('Strong completion with weak quiz outcomes', mismatch("c.completion_rate_pct>(SELECT AVG(completion_rate_pct) FROM course_perf WHERE status='published') AND q.pass_rate_pct<(SELECT AVG(pass_rate_pct) FROM quiz_perf JOIN courses USING(course_id) WHERE status='published')"), 'One published course', PUBLISHED+' Quiz strength uses the mean published-course pass rate. Aggregate enrollments and quiz attempts separately.', 'Advanced')
add('Strong quiz outcomes with weak completion', mismatch("c.completion_rate_pct<(SELECT AVG(completion_rate_pct) FROM course_perf WHERE status='published') AND q.pass_rate_pct>(SELECT AVG(pass_rate_pct) FROM quiz_perf JOIN courses USING(course_id) WHERE status='published')"), 'One published course', PUBLISHED+' Quiz strength uses the mean published-course pass rate. Aggregate separately to avoid fan-out.', 'Advanced')
add('Quiz content and difficulty review candidates', 'WITH quiz_perf AS ('+quiz_by_number+") SELECT quiz_number,attempts,avg_score,pass_rate_pct FROM quiz_perf WHERE pass_rate_pct<(SELECT AVG(pass_rate_pct) FROM quiz_perf) ORDER BY pass_rate_pct,quiz_number", 'One quiz sequence number', 'Review proxy = below the unweighted mean pass rate across quiz numbers.')

# 6. Instructor Performance (8)
add('Highest-rated instructors', 'SELECT instructor_id,name,avg_rating FROM instructors ORDER BY avg_rating DESC,instructor_id', 'One instructor', difficulty='Beginner')
add('Actual courses managed per instructor', 'SELECT i.instructor_id,i.name,COUNT(c.course_id) AS courses FROM instructors i LEFT JOIN courses c USING(instructor_id) GROUP BY i.instructor_id,i.name ORDER BY courses DESC,i.instructor_id', 'One instructor', 'Count actual courses; do not use the unverified stored courses_count.', 'Beginner')
add('Instructor enrollment reach', IP+' SELECT instructor_id,name,courses,enrollments FROM instructor_perf ORDER BY enrollments DESC,instructor_id', 'One instructor')
add('Instructor ratings and course demand', IP+' SELECT instructor_id,name,avg_rating,courses,enrollments FROM instructor_perf ORDER BY avg_rating DESC,instructor_id', 'One instructor', 'Include instructors with no recorded courses/enrollments; discuss associations in notes.')
add('Expertise areas and learning outcomes', f'SELECT i.expertise,COUNT(DISTINCT c.course_id) AS courses,COUNT(*) AS enrollments,{RATE} AS completion_rate_pct,{CERT} AS certification_rate_pct FROM enrollments e JOIN courses c USING(course_id) JOIN instructors i USING(instructor_id) GROUP BY i.expertise ORDER BY enrollments DESC,i.expertise', 'One instructor expertise')
add('Instructor completion performance', IP+' SELECT instructor_id,name,enrollments,completion_rate_pct FROM instructor_perf WHERE enrollments>0 ORDER BY completion_rate_pct DESC,instructor_id', 'One instructor', 'Enrollment-weighted completion across all courses; round at final aggregation.', 'Advanced')
add('Strong instructor quality with limited reach', IP+' SELECT instructor_id,name,avg_rating,courses,enrollments FROM instructor_perf WHERE avg_rating>(SELECT AVG(avg_rating) FROM instructor_perf) AND enrollments<(SELECT AVG(enrollments) FROM instructor_perf) ORDER BY avg_rating DESC,instructor_id', 'One instructor', 'Quality proxy = rating above instructor mean; limited reach = enrollment count below instructor mean.')
add('Instructor support and capacity priorities', IP+" SELECT instructor_id,name,courses,enrollments,completion_rate_pct,CASE WHEN courses=0 THEN 'capacity opportunity' WHEN completion_rate_pct<(SELECT AVG(completion_rate_pct) FROM instructor_perf) THEN 'content support' WHEN courses>(SELECT AVG(courses) FROM instructor_perf) THEN 'capacity review' ELSE 'monitor' END AS recommendation FROM instructor_perf ORDER BY instructor_id", 'One instructor', 'Rule priority: no courses, below-mean completion, above-mean course load, otherwise monitor. This is a review proxy.', 'Advanced')

# 7. Pricing & Commercial Analysis (7)
add('Enrollments across listed price points', "SELECT c.price_idr,COUNT(*) AS enrollments FROM enrollments e JOIN courses c USING(course_id) WHERE c.status='published' GROUP BY c.price_idr ORDER BY c.price_idr", 'One published price point', difficulty='Beginner')
add('Potential gross booking value by course', course_query('course_id,title,price_idr,enrollments,potential_booking_value_idr', "WHERE status='published'", 'potential_booking_value_idr DESC,course_id'), 'One published course', 'Potential booking value = listed price × recorded enrollments. Not confirmed revenue.')
add('Potential booking value by category', CP+" SELECT category,SUM(enrollments) AS enrollments,SUM(potential_booking_value_idr) AS potential_booking_value_idr FROM course_perf WHERE status='published' GROUP BY category ORDER BY potential_booking_value_idr DESC,category", 'One published category', 'No payment, refund or discount data; booking value is a listed-price proxy.')
add('Price and enrollment association', CP+" SELECT price_idr,COUNT(*) AS courses,SUM(enrollments) AS enrollments,ROUND(AVG(enrollments),2) AS avg_enrollments_per_course FROM course_perf WHERE status='published' GROUP BY price_idr ORDER BY price_idr", 'One published price point', 'Report average enrollments per course so differing catalog sizes do not distort demand.')
add('Pricing, completion and quiz outcomes', "WITH outcomes AS (SELECT c.price_idr,COUNT(*) AS enrollments,"+RATE+" AS completion_rate_pct FROM enrollments e JOIN courses c USING(course_id) WHERE c.status='published' GROUP BY c.price_idr),quiz AS (SELECT c.price_idr,ROUND(AVG(q.score),2) AS avg_quiz_score,ROUND(100.0*COUNT(*) FILTER(WHERE q.passed)/COUNT(*),2) AS quiz_pass_rate_pct FROM quiz_results q JOIN courses c USING(course_id) WHERE c.status='published' GROUP BY c.price_idr) SELECT o.price_idr,o.enrollments,o.completion_rate_pct,q.avg_quiz_score,q.quiz_pass_rate_pct FROM outcomes o LEFT JOIN quiz q USING(price_idr) ORDER BY o.price_idr", 'One published price point', 'Aggregate quiz and enrollment grains separately; no causal pricing claim.', 'Advanced')
add('High demand, rating and potential value', course_query('course_id,title,enrollments,avg_rating,potential_booking_value_idr', "WHERE status='published' AND enrollments>(SELECT AVG(enrollments) FROM course_perf WHERE status='published') AND avg_rating>(SELECT AVG(avg_rating) FROM course_perf WHERE status='published') AND potential_booking_value_idr>(SELECT AVG(potential_booking_value_idr) FROM course_perf WHERE status='published')", 'potential_booking_value_idr DESC,course_id'), 'One published course', PUBLISHED+' Potential value is not actual revenue.')
add('Pricing and packaging review candidates', course_query('course_id,title,price_idr,enrollments,avg_rating,completion_rate_pct', "WHERE status='published' AND price_idr>(SELECT AVG(price_idr) FROM course_perf WHERE status='published') AND enrollments<(SELECT AVG(enrollments) FROM course_perf WHERE status='published')"), 'One published course', PUBLISHED+' Review proxy = above-mean price and below-mean demand; not evidence that price causes low demand.')

# 8. Cohort & Temporal Analysis (6)
add('Enrollment cohort completion and certification', f"SELECT DATE_TRUNC('month',enrolled_date)::date AS enrollment_cohort,COUNT(*) AS enrollments,{RATE} AS completion_rate_pct,{CERT} AS certification_rate_pct FROM enrollments GROUP BY 1 ORDER BY 1", 'One monthly enrollment cohort', 'Recent cohorts have less observation time; compare descriptively.')
add('Registration cohort engagement and outcomes', "SELECT DATE_TRUNC('year',s.registration_date)::date AS registration_cohort,COUNT(DISTINCT s.student_id) AS students,COUNT(e.enrollment_id) AS enrollments,ROUND(AVG(e.completion_pct),2) AS avg_completion_pct,ROUND(100.0*COUNT(e.enrollment_id) FILTER(WHERE e.completion_pct=100)/NULLIF(COUNT(e.enrollment_id),0),2) AS completion_rate_pct FROM students s LEFT JOIN enrollments e USING(student_id) GROUP BY 1 ORDER BY 1", 'One yearly registration cohort', 'Engagement proxy = recorded enrollments; include registered students without enrollments.')
add('Course creation timing and observed demand', CP+' SELECT DATE_TRUNC(\'year\',created_date)::date AS creation_year,status,COUNT(*) AS courses,ROUND(AVG(enrollments),2) AS avg_enrollments_per_course FROM course_perf GROUP BY 1,2 ORDER BY 1,2', 'One creation year × course status', 'Course ages and observation windows differ; creation date does not establish a causal effect.')
add('Seasonal enrollment and quiz activity', "WITH activity AS (SELECT EXTRACT(MONTH FROM enrolled_date)::integer AS month_of_year,COUNT(*) AS enrollments,0::bigint AS quiz_attempts FROM enrollments GROUP BY 1 UNION ALL SELECT EXTRACT(MONTH FROM attempt_date)::integer,0::bigint,COUNT(*) FROM quiz_results GROUP BY 1) SELECT month_of_year,SUM(enrollments) AS enrollments,SUM(quiz_attempts) AS quiz_attempts FROM activity GROUP BY month_of_year ORDER BY month_of_year", 'One month of year', 'Aggregate across all observed years; partial years and coverage may distort apparent seasonality.')
add('Learner recency across enrollment cohorts', ANCHOR+" SELECT DATE_TRUNC('month',e.enrolled_date)::date AS enrollment_cohort,a.as_of_date,COUNT(*) AS enrollments,ROUND(AVG(a.as_of_date-e.last_accessed),2) AS avg_days_since_access FROM enrollments e CROSS JOIN anchor a GROUP BY 1,2 ORDER BY 1", 'One monthly enrollment cohort', 'Recency anchor is MAX(last_accessed) in the dataset, not today.')
add('Cohorts showing disengagement signals', ANCHOR+f" SELECT DATE_TRUNC('month',e.enrolled_date)::date AS enrollment_cohort,a.as_of_date,COUNT(*) AS enrollments,COUNT(*) FILTER(WHERE {RISK}) AS at_risk_enrollments,ROUND(100.0*COUNT(*) FILTER(WHERE {RISK})/COUNT(*),2) AS at_risk_rate_pct FROM enrollments e CROSS JOIN anchor a GROUP BY 1,2 ORDER BY 1", 'One monthly enrollment cohort', 'At-risk proxy = incomplete AND last access >90 days before dataset MAX(last_accessed). Not a diagnosis.', 'Advanced')

# 9. Engagement & At-Risk Learners (5)
add('Low-completion enrollment population', 'SELECT COUNT(*) AS enrollments,COUNT(*) FILTER(WHERE completion_pct<25) AS low_completion_enrollments,ROUND(100.0*COUNT(*) FILTER(WHERE completion_pct<25)/COUNT(*),2) AS low_completion_rate_pct FROM enrollments', 'One enrollment summary', 'Low completion is explicitly defined as completion_pct <25, including zero.', 'Beginner')
add('Courses with partially completed enrollments', 'SELECT c.course_id,c.title,COUNT(*) AS partially_completed_enrollments FROM enrollments e JOIN courses c USING(course_id) WHERE e.completion_pct>0 AND e.completion_pct<100 GROUP BY c.course_id,c.title ORDER BY partially_completed_enrollments DESC,c.course_id', 'One course', 'Partially completed means 0 < completion_pct <100.')
add('Learner segments with the lowest completion', SP+' SELECT acquisition_source,plan_type,enrollments,learners,avg_completion_pct,completion_rate_pct FROM segment_perf WHERE enrollments>=30 ORDER BY completion_rate_pct,acquisition_source,plan_type', 'One acquisition source × plan', 'Require at least 30 enrollments; sort completion ascending.')
add('Define an explicit at-risk learner proxy', ANCHOR+f" SELECT a.as_of_date,({RISK}) AS at_risk_proxy,COUNT(*) AS enrollments,COUNT(DISTINCT e.student_id) AS learners,ROUND(AVG(e.completion_pct),2) AS avg_completion_pct FROM enrollments e CROSS JOIN anchor a GROUP BY 1,2 ORDER BY at_risk_proxy DESC", 'One risk-proxy group', 'At risk = completion_pct <100 AND last_accessed more than 90 days before MAX(last_accessed). Learners may occur in both groups.', 'Advanced')
add('Re-engagement intervention targets', ANCHOR+f" SELECT c.course_id,c.title,s.acquisition_source,s.plan_type,COUNT(*) AS at_risk_enrollments FROM enrollments e JOIN students s USING(student_id) JOIN courses c USING(course_id) CROSS JOIN anchor a WHERE {RISK} GROUP BY c.course_id,c.title,s.acquisition_source,s.plan_type ORDER BY at_risk_enrollments DESC,c.course_id,s.acquisition_source,s.plan_type LIMIT 100", 'One course × acquisition source × plan', 'Return the top 100 groups by at-risk enrollment count. Break ties by course_id, acquisition_source, plan_type. Same explicit >90-day incomplete proxy.', 'Advanced')

# 10. Strategic Questions (6)
add('Categories to prioritize for growth', CP+" SELECT category,SUM(enrollments) AS enrollments,ROUND(100.0*SUM(completed_enrollments)/NULLIF(SUM(enrollments),0),2) AS completion_rate_pct,SUM(potential_booking_value_idr) AS potential_booking_value_idr FROM course_perf WHERE status='published' GROUP BY category ORDER BY completion_rate_pct DESC,enrollments DESC,category", 'One published category', 'Evidence scorecard ranked by completion then demand; record justified recommendations in notes. Potential value is not revenue.', 'Advanced')
add('Improve courses before further promotion', course_query('course_id,title,enrollments,avg_rating,completion_rate_pct', "WHERE status='published' AND enrollments>(SELECT AVG(enrollments) FROM course_perf WHERE status='published') AND (completion_rate_pct<(SELECT AVG(completion_rate_pct) FROM course_perf WHERE status='published') OR avg_rating<(SELECT AVG(avg_rating) FROM course_perf WHERE status='published'))"), 'One published course', PUBLISHED+' Review candidates have high demand and either low completion or low rating.', 'Advanced')
add('Targeted acquisition and retention segments', SP+" SELECT acquisition_source,plan_type,enrollments,completion_rate_pct,certification_rate_pct,CASE WHEN completion_rate_pct>=(SELECT AVG(completion_rate_pct) FROM segment_perf) THEN 'acquisition candidate' ELSE 'retention support' END AS recommendation FROM segment_perf WHERE enrollments>=30 ORDER BY acquisition_source,plan_type", 'One acquisition source × plan', 'At least 30 enrollments; above/equal mean segment completion → acquisition candidate; otherwise retention support.', 'Advanced')
add('Largest gaps between demand and learning success', course_query('course_id,title,enrollments,completion_rate_pct,enrollments-completed_enrollments AS incomplete_enrollments', "WHERE status='published'", 'incomplete_enrollments DESC,course_id'), 'One published course', 'Gap = actual incomplete enrollment count, rather than a difference between incompatible units.', 'Advanced')
add('Strategic instructor and expertise strengths', IP+' SELECT instructor_id,name,expertise,avg_rating,enrollments,completion_rate_pct FROM instructor_perf WHERE avg_rating>=(SELECT AVG(avg_rating) FROM instructor_perf) AND completion_rate_pct>=(SELECT AVG(completion_rate_pct) FROM instructor_perf) ORDER BY enrollments DESC,instructor_id', 'One instructor', 'Strength proxy = at/above mean instructor rating and completion. Use expertise labels as context.', 'Advanced')
add('Three evidence-based priority actions', CP+""", ranked AS (
 SELECT course_id,title,enrollments,completion_rate_pct,ROW_NUMBER() OVER(ORDER BY enrollments DESC,course_id) AS demand_rank,
 ROW_NUMBER() OVER(ORDER BY completion_rate_pct,course_id) AS completion_rank FROM course_perf WHERE status='published' AND enrollments>0
), action_evidence AS (
 SELECT 1 AS priority,'Improve completion' AS action,title AS target,enrollments AS affected_enrollments FROM ranked WHERE completion_rank=1
 UNION ALL SELECT 2,'Review high-demand content',title,enrollments FROM ranked WHERE demand_rank=1
 UNION ALL SELECT 3,'Re-engage inactive enrollments','Incomplete; last access >90 days before dataset anchor',COUNT(*) FROM enrollments CROSS JOIN (SELECT MAX(last_accessed) AS as_of_date FROM enrollments) a WHERE completion_pct<100 AND a.as_of_date-last_accessed>90
) SELECT priority,action,target,affected_enrollments FROM action_evidence ORDER BY priority""", 'One proposed priority action', 'A deterministic planning baseline, not a causal forecast: lowest completion course, highest demand course, and at-risk population. Explain alternatives and limitations in notes.', 'Advanced')

def main():
    import sqlglot
    from sqlglot import exp
    source = ROOT/'docs/skillaju_business_questions.md'
    questions=[]
    section=None
    for line in source.read_text(encoding='utf-8').splitlines():
        match=re.match(r'## (\d+)\. (.+)',line)
        if match:
            number=int(match[1]); section=(number,match[2])
        match=re.match(r'(\d+)\. (.+)',line)
        if match and section and section[0]<=10:
            questions.append((section,int(match[1]),match[2]))
    assert len(SPECS)==len(questions)==75,(len(SPECS),len(questions))
    exercises=[]; refs={}
    prefixes=['EXE','ACQ','CAT','CMP','QIZ','INS','PRC','COH','RSK','STR']
    for spec,((number,topic),qnum,question) in zip(SPECS,questions):
        eid=f'{prefixes[number-1]}-{qnum:02d}'
        tree=sqlglot.parse_one(spec['sql'],read='postgres')
        tables=sorted({t.name for t in tree.find_all(exp.Table)} & {'students','courses','instructors','enrollments','quiz_results'})
        outputs=tree.named_selects
        assert outputs and '*' not in outputs,(eid,outputs)
        exercises.append(dict(id=eid,topic=topic,title=spec['title'],difficulty=spec['difficulty'],business_question=question,required_tables=tables,analytical_grain=spec['grain'],expected_output=outputs,learning_objectives=[topic,'PostgreSQL result interpretation','Respect analytical grain'],limitations=BASE_NOTE+' '+spec['note'],validation_policy='Use exact column aliases and column order; row order is ignored. Numbers are normalized to six decimal places. Match the stated filters and baseline definitions.',source_question=f'{number}.{qnum}',source_file='docs/skillaju_business_questions.md'))
        refs[eid]=dict(sql=spec['sql'],policy=dict(compare_column_names=True,order_matters=False))
    (ROOT/'exercises.json').write_text(json.dumps(exercises,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'reference_queries.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'coverage_matrix.md').write_text('# Business-question coverage\n\nEvery numbered question in sections 1–10 has one exercise. Section 11 contains deliverable guidance, retained in the source Markdown.\n\n| Source | Exercise | Topic | Title |\n|---|---|---|---|\n'+'\n'.join(f"| {e['source_question']} | {e['id']} | {e['topic']} | {e['title']} |" for e in exercises)+'\n',encoding='utf-8')
    print(f'Built {len(exercises)} exercises across {len(set(e["topic"] for e in exercises))} topics.')

if __name__=='__main__': main()
