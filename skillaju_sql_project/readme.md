# SKILLAJU SQL Analytics Project

## Project Overview

SKILLAJU is a portfolio-oriented PostgreSQL 16 analytics project focused on learner acquisition, course demand, learning outcomes, assessment performance, instructor performance, pricing proxies, cohorts, and engagement. The project progresses from data validation and foundational aggregation to joins, CTEs, window functions, segmentation, benchmarking, and strategic evidence tables.

The supplied Business Questions are the analytical roadmap, while the supplied data reference and CSV structure are the source of truth. No analysis result is embedded in this README; results should be generated from the database.

## Business Objective

Translate platform learning data into reliable business analysis that can support decisions around: acquisition, catalog prioritization, completion improvement, assessment quality, instructor performance, pricing review, learner re-engagement, and strategic focus.

## Dataset & Database

- Dataset: SKILLAJU
- Source context: Ngulik Data
- DBMS: PostgreSQL 16
- Tables: `students`, `courses`, `instructors`, `enrollments`, `quiz_results`
- Supplied rows: 3,000 students; 50 courses; 30 instructors; 10,380 enrollments; 30,875 quiz attempts.

## Data Model

```text
instructors 1 ───< courses
students    1 ───< enrollments >─── 1 courses
                    1
                    └──< quiz_results
```

- One row in `students` = one learner.
- One row in `courses` = one course.
- One row in `instructors` = one instructor.
- One row in `enrollments` = one student-course enrollment.
- One row in `quiz_results` = one quiz attempt.
- `quiz_results.student_id` and `course_id` are redundant attributes that should match the related enrollment.

## Project Structure

```text
skillaju_sql_project/
├── schema.sql
├── load.sql
├── readme.md
└── analysis/
    ├── 01_data_validation.sql
    ├── 02_executive_kpis.sql
    ├── 03_learner_acquisition_segmentation.sql
    ├── 04_course_catalog_performance.sql
    ├── 05_completion_certification.sql
    ├── 06_quiz_assessment.sql
    ├── 07_instructor_performance.sql
    ├── 08_pricing_commercial.sql
    ├── 09_cohort_temporal.sql
    ├── 10_engagement_at_risk.sql
    └── 11_strategic_summary.sql
```

## Setup & Loading

Create or connect to a PostgreSQL 16 database, then run:

```bash
psql -d skillaju -f schema.sql
psql -d skillaju -f load.sql
```

Place the five CSV files in the working directory used by `psql`, or change the relative paths in `load.sql`. The loader uses explicit column lists, CSV headers, and UTF-8 encoding.

Run an analysis with:

```bash
psql -d skillaju -f analysis/01_data_validation.sql
```

Then continue through the analysis directory in numerical order.

## Analytical Roadmap

1. **Data validation** — row counts, PK uniqueness, FK integrity, redundant quiz IDs, domain/date checks, and stored-vs-recorded course enrollment counts.
2. **Executive KPIs** — inventory, enrollments, completion, certification, average completion, quiz pass rate, retries, and monthly volume.
3. **Learner acquisition & segmentation** — acquisition source, plan, source × plan, city/age-oriented segmentation.
4. **Course catalog performance** — course/category/level demand, rating-demand gaps, and descriptive price/duration views.
5. **Completion & certification** — course and segment outcomes, high-demand/low-completion opportunities, and time-to-completion where dates exist.
6. **Quiz assessment** — score/pass rates, difficult quiz numbers, retries, first vs later attempts, and completion/quiz-performance gaps.
7. **Instructor performance** — portfolio reach, ratings, completion, expertise benchmarking, and instructor profiles.
8. **Pricing & commercial** — listed-price demand, potential booking value, price bands, and descriptive correlations.
9. **Cohort & temporal analysis** — monthly/quarterly trends, registration cohorts, course creation timing, and recency.
10. **Engagement & at-risk proxy** — explicitly defined recency + incomplete-learning proxy and segment/course prioritization.
11. **Strategic summary** — evidence tables for course opportunities and learner segments.

## Business Questions Covered

The project operationalizes the major questions in the supplied Business Questions document: executive performance; acquisition and segmentation; course demand and catalog quality; completion and certification; quiz difficulty and retry behavior; instructor reach and quality; pricing and potential booking value; cohort and temporal differences; engagement/at-risk proxies; and strategic prioritization.

## SQL Concepts Demonstrated

- `SELECT`, `WHERE`, `ORDER BY`, `DISTINCT`, `LIMIT` where appropriate
- `CASE` and NULL-safe calculations
- `COUNT`, `COUNT(DISTINCT ...)`, `SUM`, `AVG`
- `GROUP BY`, `HAVING`
- `INNER JOIN`, `LEFT JOIN`, multi-table joins
- `FILTER` for conditional aggregation
- `DATE_TRUNC`, date arithmetic, and temporal grouping
- CTEs and layered analytical pipelines
- `ROW/RANK`-style ranking with `RANK` and `NTILE`
- `PARTITION BY` window comparisons
- `LAG` and running totals
- percentage/contribution calculations
- percentile analysis with `PERCENTILE_CONT`
- `CORR` for descriptive association
- course opportunity segmentation and benchmark profiles

## Critical Data-Grain Rules

- Enrollment KPIs use `enrollments` as the base grain.
- Quiz analysis uses `quiz_results` as the attempt grain.
- Joining enrollments to quiz results can multiply enrollment rows because one enrollment can have many quiz attempts. Use separate CTEs or `COUNT(DISTINCT enrollment_id)` when appropriate.
- Course attributes are one row per course.
- Instructor attributes are one row per instructor.
- Current recorded enrollment counts should be calculated from `enrollments`; `courses.total_enrolled` is mainly a consistency-validation field.

## Validation Methodology

`01_data_validation.sql` checks: row counts and primary-key uniqueness; enrollment-to-student and enrollment-to-course integrity; course-to-instructor integrity; quiz-to-enrollment integrity; quiz student/course consistency with enrollment; completion percentage bounds; date ordering; quiz bounds; course status values; completion/certificate combinations for inspection; and differences between stored course enrollment counts and recorded enrollment rows.

The supplied data reference reports no duplicate full rows, unique primary identifiers, valid tested foreign-key relationships, matching quiz student/course IDs, missing `completion_date`, and both draft and published courses. These checks should be rerun if the source files are replaced.

## Revenue / Commercial Rules

There is no transaction, payment, refund, discount, or payment-status table. Therefore `price_idr × enrollment count` is treated only as **potential booking value / listed-price booking-value proxy**, not actual revenue. Do not present it as realized revenue.

## Important Analytical Caveats

- Missing `completion_date` is not imputed.
- `last_accessed` is a recorded last-access date, not time spent or session duration.
- Quiz performance is assessment performance, not proof of real-world mastery.
- Observational relationships are not causal claims.
- Draft courses should generally be excluded from customer-facing performance analysis unless explicitly required.
- Any at-risk definition is a proxy. This project defines it explicitly as incomplete plus more than 90 days since last access relative to the maximum recorded `last_accessed` date in the dataset.
- Thresholds such as minimum enrollment counts and quartiles are analytical choices and should be disclosed when presenting results.

## Reproducibility

1. Load the schema.
2. Load all CSVs with `load.sql`.
3. Run `01_data_validation.sql`.
4. Review validation output before relying on downstream metrics.
5. Execute analyses `02` through `11`.
6. Export selected query outputs to CSV or a BI tool for visualization if desired.

## Portfolio Presentation

A strong presentation can follow this storyline: **data reliability → executive baseline → acquisition/learner segments → catalog demand → learning outcomes → assessment quality → instructor strengths → commercial proxy → cohort/recency signals → strategic priorities**.

Recommended final visuals include KPI cards, monthly enrollment trend, acquisition-source comparison, course demand vs completion matrix, category performance, quiz difficulty, instructor scorecard, potential booking-value ranking, cohort outcomes, and the explicitly defined re-engagement proxy.

All final claims should be generated from executed SQL and validated outputs rather than assumed from the dataset documentation alone.
