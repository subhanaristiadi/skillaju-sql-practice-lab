-- SKILLAJU | PostgreSQL 16 schema
-- Source of truth: supplied SKILLAJU data reference and CSV files.

CREATE TABLE students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER NOT NULL,
    city TEXT NOT NULL,
    registration_date DATE NOT NULL,
    acquisition_source TEXT NOT NULL,
    plan_type TEXT NOT NULL
);

CREATE TABLE instructors (
    instructor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    expertise TEXT NOT NULL,
    city TEXT NOT NULL,
    courses_count INTEGER NOT NULL,
    avg_rating NUMERIC(3,1) NOT NULL,
    joined_date DATE NOT NULL
);

CREATE TABLE courses (
    course_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    instructor_id TEXT NOT NULL,
    price_idr INTEGER NOT NULL,
    duration_hours INTEGER NOT NULL,
    level TEXT NOT NULL,
    avg_rating NUMERIC(3,1) NOT NULL,
    total_enrolled INTEGER NOT NULL,
    created_date DATE NOT NULL,
    status TEXT NOT NULL,
    CONSTRAINT fk_courses_instructor
        FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
);

CREATE TABLE enrollments (
    enrollment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    enrolled_date DATE NOT NULL,
    completion_date DATE,
    completion_pct INTEGER NOT NULL,
    certificate_issued BOOLEAN NOT NULL,
    last_accessed DATE NOT NULL,
    CONSTRAINT fk_enrollments_student
        FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_enrollments_course
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE quiz_results (
    quiz_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    quiz_number INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL,
    score INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    attempt_date DATE NOT NULL,
    CONSTRAINT fk_quiz_enrollment
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
);

CREATE INDEX idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX idx_quiz_results_enrollment_id ON quiz_results(enrollment_id);
CREATE INDEX idx_quiz_results_course_id ON quiz_results(course_id);
CREATE INDEX idx_enrollments_enrolled_date ON enrollments(enrolled_date);
CREATE INDEX idx_quiz_results_attempt_date ON quiz_results(attempt_date);
