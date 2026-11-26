# Skillaju SQL Practice Lab

A PostgreSQL learning application using the original [Sedukopi SQL Practice Lab](https://github.com/subhanaristiadi/sedukopi-sql-practice-lab) interface. The original CSS is preserved verbatim; branding, schema and curriculum use Skillaju.

- Frontend: [GitHub Pages](https://subhanaristiadi.github.io/skillaju-sql-practice-lab/)
- API: [Render](https://skillaju-sql-practice-lab.onrender.com/health)
- Database: Neon PostgreSQL in Singapore; dedicated `skillaju_reader` role with SELECT privileges on the `lab` views only.
- Dataset source: [Ngulikdata — Skillaju](https://ngulikdata.com/datasets/skillaju).

All **75 numbered business questions across 10 topics** in [the original Markdown](docs/skillaju_business_questions.md) are included, with a reference query, output aliases, analytical grain, assumptions and automatic validation. [Coverage matrix](coverage_matrix.md). Section 11 describes standard deliverables and remains in the original document.

| Table | Records |
|---|---:|
| students | 3,000 |
| instructors | 30 |
| courses | 50 |
| enrollments | 10,380 |
| quiz_results | 30,875 |

The app supports search, topic/difficulty/completion filters, schema cards, query execution, answer validation, saved SQL, personal notes, reference SQL, progress export/import and keyboard execution with Ctrl/Cmd+Enter. Browser storage is specific to this application.

## Run locally

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL in .env to a dedicated SELECT-only Neon role.
.venv/Scripts/python server.py
```

In a separate terminal:

```powershell
python scripts/package_pages.py
python -m http.server 5500 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:5500`. The public `config.js` uses the local API on localhost and the Render API on GitHub Pages. No database password is shipped to the browser.

## Curriculum and checks

```powershell
python scripts/build_curriculum.py
python -m unittest discover -s tests -v
python scripts/verify_neon.py
```

The verification script requests a hidden JSON configuration containing `database_url`, checks reader privileges and dataset counts, and executes all 75 references against PostgreSQL. Its report is stored in ignored `.local/`. Credentials are not logged or written. `scripts/seed_neon.py` imports the five original CSVs into an **empty** database only, refusing to overwrite existing tables. It uses the same hidden-input mechanism and applies the versioned schema in `skillaju_sql_project/schema.sql`. Original CSVs are local inputs, excluded from Git. Obtain them from the dataset source when setting up a fresh checkout. After seeding and creating `skillaju_reader`, apply `skillaju_sql_project/reader_views.sql` as the database owner.

Public SQL uses schema `lab`. Student and instructor names are replaced with ID-based labels; student emails use `example.invalid`. All IDs, dates, dimensions and numerical measurements are retained. Original names/emails remain in private source tables in schema `public`; the API role has no SELECT permission there. The public repository and Pages artifact contain no source CSV records.

## Analytical definitions

Completion uses `completion_pct = 100`; certification uses `certificate_issued`. Enrollment counts come from `enrollments`. Quiz outcomes use quiz-attempt grain; enrollment and quiz aggregates are calculated separately to prevent double counting. Instructor completion is weighted by actual enrollment counts. Rates are rounded to two decimals.

Potential booking value is `price_idr × recorded enrollment count`, **not confirmed revenue**. At-risk is an explicitly stated proxy: incomplete enrollment and last access more than 90 days before the dataset's maximum `last_accessed`. It does not use today's date or imply a diagnosis.

Qualitative questions use a documented, deterministic evidence table as the validation baseline. The exercise warning states thresholds and filters; recommendations and alternative interpretations belong in personal notes. Baseline rules are exercise assumptions, not undocumented business facts. Recent cohorts have shorter observation windows; observational relationships do not establish causation.

Validation checks exact output aliases and column order, normalizes numbers to six decimal places and compares row multisets (including duplicates). Equivalent SQL can pass. Truncated results cannot pass validation. Query results are limited to 500 displayed rows, a bounded payload and a 10-second database timeout. SQL parsing permits SELECT/CTE with approved analytical functions and Skillaju tables only. Transactions and the database role are read-only. Rate and concurrency limits bound public query use.

## Deploy

GitHub Actions packages only `index.html`, `config.js`, `api-client.js`, `exercises.json` and `.nojekyll` into the Pages artifact. Backend source, reference SQL, CSVs and credentials are excluded from that artifact. Pages uses the `main` branch Actions workflow.

Render runs `gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 35`. Set `DATABASE_URL` through Render secret environment variables to the reader connection, `REQUIRE_NON_SUPERUSER=true` and `CORS_ALLOWED_ORIGINS=https://subhanaristiadi.github.io`. `/ready` is fast liveness; `/health` verifies actual database connectivity and role privileges.

The service is managed directly through Render. `render.yaml` is a reproducible Blueprint alternative, not a second deployment to apply in parallel. Credentials remain only in Neon/Render secret storage. Render Free can sleep when idle, so the first API request may take about a minute; the exercise list loads independently from Pages. The page quietly warms the service through `/ready`. Requests retry transient connection failures up to three times within one 90-second timeout. SQL errors and rate limits are reported immediately beside the query; an initial connection failure does not display a permanent header warning.

Original UI reference revision: `269ac04b611487a0b70e5884b6e20dbb8ef72f4a`. Existing CSVs and original Skillaju SQL analysis files are preserved.
