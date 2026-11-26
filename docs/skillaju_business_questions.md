# SKILLAJU — Business Questions

This document defines the main analytical questions that can be answered from the current SKILLAJU dataset. Questions should be answered using the available data and the KPI definitions in `skillaju_project_instructions.md`.

## 1. Executive Performance
1. How many students, enrollments, courses, instructors, and quiz attempts are in the dataset?
2. How has enrollment volume changed over time?
3. What are the overall completion, certification, and average completion rates?
4. Which dimensions explain the largest differences in learning outcomes?
5. Which areas of the platform appear strongest and weakest?

## 2. Learner Acquisition & Segmentation
1. Which acquisition sources generate the most registered students?
2. Which acquisition sources generate the most enrollments?
3. Which acquisition sources are associated with higher completion and certification rates?
4. How do outcomes differ by `plan_type` (free, basic, pro)?
5. Which cities contribute the most students and enrollments?
6. Do learner age groups differ in course choice or completion?
7. Which acquisition source × plan combinations appear strongest?
8. Are some learner segments highly active but under-completing?

## 3. Course Demand & Catalog
1. Which courses have the most enrollments?
2. Which courses have the fewest enrollments?
3. Which categories attract the most learners?
4. How does demand differ by course level?
5. How do price and duration relate to enrollment volume?
6. Which published courses have high demand but relatively low ratings?
7. Which courses have high ratings but low demand?
8. Are draft courses materially different from published courses in observable catalog attributes?
9. Which categories or levels appear underrepresented or overrepresented in the catalog?
10. Which courses should be prioritized for promotion, improvement, or review?

## 4. Learning Completion & Certification
1. What is the overall course completion rate?
2. Which courses have the highest and lowest completion rates?
3. Which categories and levels have the best completion outcomes?
4. Which courses have high enrollment but low completion?
5. Which courses have low enrollment but high completion?
6. How long does it typically take from enrollment to completion when both dates are available?
7. Does learner plan type correlate with completion?
8. Does acquisition source correlate with completion?
9. Which cities have unusually high or low completion rates?
10. What learner/course segments should be targeted for completion improvement?

## 5. Quiz & Assessment Performance
1. What is the overall quiz average score and pass rate?
2. How do scores and pass rates vary by course?
3. Which quiz numbers are most difficult?
4. Does performance decline or improve across quiz numbers?
5. How often do learners retry quizzes?
6. Does a retry improve the score on average?
7. What is the first-attempt pass rate versus later-attempt pass rate?
8. Which courses have unusually low quiz performance despite strong completion?
9. Which courses have strong quiz performance but weak completion?
10. Are there quiz numbers that may warrant content or difficulty review?

## 6. Instructor Performance
1. Which instructors have the highest average ratings?
2. Which instructors manage the largest number of courses?
3. Which instructors' courses generate the most enrollments?
4. How do instructor ratings relate to course demand?
5. How do instructor expertise areas compare on enrollment and learner outcomes?
6. Are some instructors associated with unusually high or low completion rates across their courses?
7. Which instructors appear to have strong quality but limited course reach?
8. Where might instructor support, content review, or capacity balancing be useful?

## 7. Pricing & Commercial Analysis
1. How is enrollment distributed across price points?
2. Which courses generate the highest potential gross booking value using `price_idr × enrollment count`?
3. Which categories have the highest potential booking value?
4. Do higher-priced courses have lower or higher enrollment?
5. Does price appear associated with completion or quiz outcomes?
6. Which courses combine strong demand, strong rating, and high potential booking value?
7. Which courses may be candidates for pricing or packaging review?

**Important:** potential booking value is not confirmed revenue because the dataset contains no payment, refund, discount, or transaction table.

## 8. Cohort & Temporal Analysis
1. How do enrollment cohorts differ in completion and certification?
2. Which registration cohorts produce the strongest engagement or learning outcomes?
3. How has course creation timing affected observable demand?
4. Are there seasonal patterns in enrollment or quiz activity?
5. How does learner recency (`last_accessed`) vary across cohorts?
6. Which cohorts show signs of disengagement based on completion and last access?

## 9. Engagement & At-Risk Learners
1. How many enrollments have low completion percentages?
2. Which courses have the largest populations of partially completed enrollments?
3. Which learner segments show the lowest completion?
4. Can a practical at-risk proxy be created using `completion_pct` and `last_accessed`?
5. Which courses or segments should receive re-engagement interventions?

Any at-risk definition must be explicitly stated because the dataset does not provide session frequency, time spent, or cancellation status.

## 10. Strategic Questions
1. Which course categories should SKILLAJU prioritize for growth?
2. Which courses should be improved before additional promotion?
3. Which learner segments deserve targeted acquisition or retention efforts?
4. Where are the largest gaps between demand and learning success?
5. Which instructors or expertise areas are strategic strengths?
6. What three actions are most likely to improve enrollment, completion, or learner quality based on the evidence?

## 11. Standard Deliverables
For a broad SKILLAJU analysis, aim to provide:
- executive KPI snapshot;
- course/category ranking;
- learner segmentation;
- completion and certification analysis;
- quiz performance analysis;
- instructor analysis;
- commercial/pricing view where appropriate;
- key risks/data limitations;
- prioritized recommendations.
