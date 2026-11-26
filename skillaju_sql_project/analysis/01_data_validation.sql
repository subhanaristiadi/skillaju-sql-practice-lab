-- Business question: Is the loaded SKILLAJU dataset structurally reliable enough for analysis?
-- Grain: table-specific master, enrollment, and quiz-attempt grains.
-- Tables: students, instructors, courses, enrollments, quiz_results.

-- Row counts and PK uniqueness.
SELECT 'students' AS table_name, COUNT(*) AS row_count, COUNT(DISTINCT student_id) AS distinct_pk FROM students
UNION ALL SELECT 'instructors', COUNT(*), COUNT(DISTINCT instructor_id) FROM instructors
UNION ALL SELECT 'courses', COUNT(*), COUNT(DISTINCT course_id) FROM courses
UNION ALL SELECT 'enrollments', COUNT(*), COUNT(DISTINCT enrollment_id) FROM enrollments
UNION ALL SELECT 'quiz_results', COUNT(*), COUNT(DISTINCT quiz_id) FROM quiz_results;

-- FK integrity checks: every query should return zero rows.
SELECT e.enrollment_id, e.student_id FROM enrollments e LEFT JOIN students s USING (student_id) WHERE s.student_id IS NULL;
SELECT e.enrollment_id, e.course_id FROM enrollments e LEFT JOIN courses c USING (course_id) WHERE c.course_id IS NULL;
SELECT c.course_id, c.instructor_id FROM courses c LEFT JOIN instructors i USING (instructor_id) WHERE i.instructor_id IS NULL;
SELECT q.quiz_id FROM quiz_results q LEFT JOIN enrollments e USING (enrollment_id) WHERE e.enrollment_id IS NULL;

-- Redundant quiz relationship attributes must match the enrollment.
SELECT q.quiz_id, q.enrollment_id, q.student_id AS quiz_student_id, e.student_id AS enrollment_student_id,
       q.course_id AS quiz_course_id, e.course_id AS enrollment_course_id
FROM quiz_results q JOIN enrollments e USING (enrollment_id)
WHERE q.student_id IS DISTINCT FROM e.student_id OR q.course_id IS DISTINCT FROM e.course_id;

-- Domain/date consistency checks.
SELECT * FROM enrollments WHERE completion_pct NOT BETWEEN 0 AND 100;
SELECT * FROM enrollments WHERE completion_date IS NOT NULL AND completion_date < enrolled_date;
SELECT * FROM enrollments WHERE last_accessed < enrolled_date;
SELECT * FROM quiz_results WHERE score NOT BETWEEN 0 AND 100 OR attempt_number < 1 OR quiz_number < 1;
SELECT * FROM courses WHERE status NOT IN ('draft','published');

-- Completion/certificate consistency candidates; inspect before treating as errors.
SELECT certificate_issued, completion_pct, COUNT(*) AS enrollments
FROM enrollments
GROUP BY certificate_issued, completion_pct
ORDER BY certificate_issued, completion_pct;

-- Course stored enrollment count vs supplied enrollment records.
SELECT c.course_id, c.title, c.status, c.total_enrolled AS stored_total,
       COUNT(e.enrollment_id) AS enrollment_rows,
       c.total_enrolled - COUNT(e.enrollment_id) AS difference
FROM courses c LEFT JOIN enrollments e USING (course_id)
GROUP BY c.course_id, c.title, c.status, c.total_enrolled
ORDER BY ABS(c.total_enrolled - COUNT(e.enrollment_id)) DESC, c.course_id;
