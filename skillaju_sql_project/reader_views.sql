-- Public practice access uses anonymous learner/instructor identities.
-- Original CSV data and private source tables remain unchanged.
CREATE SCHEMA lab AUTHORIZATION skillaju_owner;

CREATE VIEW lab.students AS
SELECT student_id, 'Learner ' || student_id AS name,
       LOWER(student_id) || '@example.invalid' AS email,
       age, city, registration_date, acquisition_source, plan_type
FROM public.students;

CREATE VIEW lab.instructors AS
SELECT instructor_id, 'Instructor ' || instructor_id AS name,
       expertise, city, courses_count, avg_rating, joined_date
FROM public.instructors;

CREATE VIEW lab.courses AS SELECT * FROM public.courses;
CREATE VIEW lab.enrollments AS SELECT * FROM public.enrollments;
CREATE VIEW lab.quiz_results AS SELECT * FROM public.quiz_results;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM skillaju_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE skillaju_owner IN SCHEMA public
    REVOKE SELECT ON TABLES FROM skillaju_reader;
REVOKE ALL ON SCHEMA public FROM skillaju_reader;
GRANT USAGE ON SCHEMA lab TO skillaju_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA lab TO skillaju_reader;
ALTER ROLE skillaju_reader IN DATABASE skillaju SET search_path = lab, pg_catalog;
ALTER ROLE skillaju_reader SET default_transaction_read_only = on;
