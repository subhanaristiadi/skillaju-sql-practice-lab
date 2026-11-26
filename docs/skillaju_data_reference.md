# SKILLAJU — Data Reference

## Dataset Overview

| File | Rows | Primary Key | Purpose |
|---|---:|---|---|
| `students(1).csv` | 3,000 | `student_id` | Learner master data |
| `courses(1).csv` | 50 | `course_id` | Course/catalog data |
| `instructors(1).csv` | 30 | `instructor_id` | Instructor master data |
| `enrollments(1).csv` | 10,380 | `enrollment_id` | Student-course enrollment and progress |
| `quiz_results(1).csv` | 30,875 | `quiz_id` | Quiz attempt results |

Public context: https://ngulikdata.com/datasets/skillaju

## 1. students

**Grain:** one row per student.

| Column | Type | Description |
|---|---|---|
| `student_id` | string | Unique learner identifier |
| `name` | string | Learner name |
| `email` | string | Learner email |
| `age` | integer | Age; observed range 18–45 |
| `city` | string | Learner city |
| `registration_date` | date | Date the learner registered |
| `acquisition_source` | categorical | Google, Instagram, YouTube, Referral, TikTok, Organic |
| `plan_type` | categorical | free, basic, pro |

Notes: `student_id` and `email` are unique in the supplied file. Names are not unique.

## 2. courses

**Grain:** one row per course.

| Column | Type | Description |
|---|---|---|
| `course_id` | string | Unique course identifier |
| `title` | string | Course title |
| `category` | categorical | SQL, Excel, Power BI, Data Engineering, Python, Statistics |
| `instructor_id` | string | Instructor assigned to the course |
| `price_idr` | integer | Listed course price in IDR |
| `duration_hours` | integer | Course duration in hours |
| `level` | categorical | beginner, intermediate, advanced |
| `avg_rating` | decimal | Course average rating |
| `total_enrolled` | integer | Enrollment count stored in the course table |
| `created_date` | date | Course creation date |
| `status` | categorical | draft or published |

Observed ranges: price IDR 0–599,000; duration 4–30 hours; rating 4.0–4.9; stored `total_enrolled` 60–1,998.

**Important:** For current analytical counts, prefer calculating enrollment counts from `enrollments` when the question concerns the supplied enrollment records. Compare against `courses.total_enrolled` if validating consistency.

## 3. instructors

**Grain:** one row per instructor.

| Column | Type | Description |
|---|---|---|
| `instructor_id` | string | Unique instructor identifier |
| `name` | string | Instructor name |
| `expertise` | categorical | SQL & Data Engineering; Excel & Google Sheets; Statistics & Analytics; Power BI & Tableau; Data Visualization; Python & Machine Learning |
| `city` | string | Instructor city |
| `courses_count` | integer | Number of courses attributed to instructor |
| `avg_rating` | decimal | Instructor average rating |
| `joined_date` | date | Instructor join date |

Observed: 30 instructors; `courses_count` ranges 1–6 and `avg_rating` ranges 4.1–5.0.

## 4. enrollments

**Grain:** one row per student-course enrollment.

| Column | Type | Description |
|---|---|---|
| `enrollment_id` | string | Unique enrollment identifier |
| `student_id` | string | Learner identifier |
| `course_id` | string | Course identifier |
| `enrolled_date` | date | Enrollment date |
| `completion_date` | date/null | Completion date when present |
| `completion_pct` | integer | Completion percentage, 0–100 |
| `certificate_issued` | boolean | Whether certificate was issued |
| `last_accessed` | date | Last recorded access date |

Observed date range for `enrolled_date`: 2022-01-14 to 2025-03-15.

`completion_date` contains missing values. Do not impute them without an explicit rule.

## 5. quiz_results

**Grain:** one row per quiz attempt.

| Column | Type | Description |
|---|---|---|
| `quiz_id` | string | Unique quiz-result record identifier |
| `enrollment_id` | string | Enrollment being assessed |
| `student_id` | string | Learner identifier |
| `course_id` | string | Course identifier |
| `quiz_number` | integer | Quiz sequence number within course/enrollment |
| `attempt_number` | integer | Attempt number; 1–3 observed |
| `score` | integer | Quiz score; observed range 30–100 |
| `passed` | boolean | Whether the attempt passed |
| `attempt_date` | date | Quiz attempt date |

Observed `quiz_number` range: 1–7; `attempt_number` range: 1–3.

## Relationship Map

```text
instructors
   1 ───────< courses
                  |
                  | 1
                  v
students  1 ───< enrollments >─── 1 courses
                  |
                  | 1
                  v
             quiz_results
```

More precisely:
- One instructor can have multiple courses.
- One student can have multiple enrollments.
- One course can have multiple enrollments.
- One enrollment can have multiple quiz-result rows.
- `quiz_results.student_id` and `quiz_results.course_id` are redundant relationship attributes and should match the referenced enrollment.

## Data Quality Checks Performed

For the supplied files:
- No duplicate full rows were observed.
- Primary identifiers are unique within their respective tables.
- Foreign-key relationships were valid for the tested joins.
- Quiz student/course IDs matched the corresponding enrollment IDs.
- `enrollments` has missing values, primarily in `completion_date`.
- No missing values were observed in the other four files.
- Course status contains both `draft` and `published`.

These checks describe the supplied files at analysis time; re-check them if files are replaced or updated.

## Recommended Join Patterns

### Student + Enrollment
Join:
`enrollments.student_id = students.student_id`

Use for learner segmentation, acquisition source, plan type, city, age, and cohort analysis.

### Enrollment + Course
Join:
`enrollments.course_id = courses.course_id`

Use for category, title, level, price, duration, rating, status, and course performance.

### Course + Instructor
Join:
`courses.instructor_id = instructors.instructor_id`

Use for instructor performance, expertise, course portfolio, and instructor-level comparisons.

### Enrollment + Quiz
Join:
`quiz_results.enrollment_id = enrollments.enrollment_id`

Use for quiz performance in the context of learner enrollment and completion.

## Analytical Caveats

1. There is no transaction/payment table; do not call `price_idr × enrollments` actual revenue.
2. There is no discount/refund/payment-status information.
3. There is no explicit session-duration or learning-time measure.
4. `last_accessed` indicates a recorded last access date, not time spent.
5. Quiz scores measure assessment performance, not necessarily real-world skill mastery.
6. Observational relationships should not be interpreted as causal.
7. The `total_enrolled` course field should be validated against the enrollment table before being used as a current-period KPI.
8. Draft courses may be excluded from customer-facing catalog performance analyses unless the question explicitly includes them.
