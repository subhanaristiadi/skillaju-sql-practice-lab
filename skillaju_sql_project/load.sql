-- SKILLAJU | PostgreSQL 16 data loading
-- Run from the directory containing the CSV files, after schema.sql.
-- Explicit column lists preserve the documented mapping even if table definitions change.

\copy students (student_id, name, email, age, city, registration_date, acquisition_source, plan_type) FROM 'students.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy instructors (instructor_id, name, expertise, city, courses_count, avg_rating, joined_date) FROM 'instructors.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy courses (course_id, title, category, instructor_id, price_idr, duration_hours, level, avg_rating, total_enrolled, created_date, status) FROM 'courses.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy enrollments (enrollment_id, student_id, course_id, enrolled_date, completion_date, completion_pct, certificate_issued, last_accessed) FROM 'enrollments.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy quiz_results (quiz_id, enrollment_id, student_id, course_id, quiz_number, attempt_number, score, passed, attempt_date) FROM 'quiz_results.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
