# Mini-project Work — Mini-project {{MP NO}}, ({{COHORT}})

It's where the learner does the mini-project works.

> This is **practice**, not portfolio. Your individual capstones live in *your own* `portfolio-…` repo and are never built here. Keep the two separate: this repo is disposable; your portfolio is forever.

## mini-project-template — Pre-commit & Quality Checks

Quality checks that run automatically before every commit (and in CI). They keep the repo
clean, consistent, and — because this repo is **public** — free of accidentally-committed secrets.

### One-time setup

```bash
pip install pre-commit      # or: uv tool install pre-commit
pre-commit install          # hooks now run on every `git commit`
```

That's it — from now on the checks run automatically when you commit. To also run them at
push time: `pre-commit install --hook-type pre-push`.

### Everyday use

- They run on the files you changed each time you `git commit`.
- If a hook **fixes** something (formatting, trailing whitespace), re-stage and commit again.
- Run everything by hand any time: `pre-commit run --all-files`.
- Skip once in an emergency: `git commit --no-verify` (avoid — CI will still catch it).
- Update hook versions: `pre-commit autoupdate`.

### What runs

| Hook | What it checks |
|------|----------------|
| `trailing-whitespace`, `end-of-file-fixer`, `mixed-line-ending` | Clean line endings and file endings. |
| `check-yaml`, `check-json`, `check-toml` | Config files actually parse. |
| `check-added-large-files` | Blocks files over 5 MB (keep data out of git). |
| `check-merge-conflict`, `check-case-conflict` | No conflict markers; no case-clashing filenames. |
| `check-executables-have-shebangs`, `check-shebang-scripts-are-executable` | Scripts are consistent. |
| `detect-private-key` + **`gitleaks`** | **Secret scanning** — blocks keys/tokens before they reach a public repo. |
| `ruff`, `ruff-format` | Python linting + formatting. |
| **`sqlfluff-lint`** | SQL linting — BigQuery dialect, dbt-aware (understands `ref()`/`source()` with no credentials). |
| `yamllint` | YAML style (tuned for GitHub Actions / dbt / k8s). |
| `markdownlint` | Markdown style (relaxed for technical docs). |
| `terraform_fmt` | Terraform formatting (only when `.tf` files change). |

Config lives in `.pre-commit-config.yaml`, `.sqlfluff`, `.yamllint.yaml`, and `.markdownlint.yaml` —
edit those to tune rules for your work.

### CI backstop

`.github/workflows/checks.yml` runs the **same** hooks on every pull request and push to `main`,
so the checks hold even if someone commits with `--no-verify`. One source of truth
(`.pre-commit-config.yaml`), enforced both locally and remotely.

## This mini-project

- **Brief:** see the relevant mini-project in the course repo (e.g. `mp1-sql-foundations/mini-project/README.md`).
- **Learner (anchor):** `{{LEARNER}}` — runs the mini-project and merges.
- **Learners:** see the week's plan posted in the cohort discussion.

## Session 1 — Python ETL pipeline

The pipeline lives in `py-project/` and follows the standard extract → transform → load split.

```text
py-project/
├── src/
│   ├── extract.py              ← read CSV / parquet / JSON, or call an API
│   ├── transform.py            ← type casting + custom business transformations
│   ├── load.py                 ← write CSV / parquet, partitioned or not
│   ├── nyc_trips_pipeline.py   ← the runnable pipeline (argparse CLI)
│   └── generate_sample_data.py ← seeds the gitignored raw sample
├── test/                       ← pytest unit tests
└── test_data/                  ← small fixtures for the extract tests
```

### Running the pipeline

All commands run from `py-project/`. The raw sample is gitignored, so generate it first:

```bash
uv sync
cd py-project
uv run python -m src.generate_sample_data
```

Then run the pipeline. Every path and option is a CLI argument:

```bash
# unpartitioned — one parquet file under data/processed
uv run python -m src.nyc_trips_pipeline

# partitioned by payment type
uv run python -m src.nyc_trips_pipeline \
  --output-path demo_data/data/processed/yellow_taxi_jan2024_partitioned \
  --partition-by payment_type

# partitioned CSV, two partition columns
uv run python -m src.nyc_trips_pipeline \
  --as-file-type csv \
  --output-path demo_data/data/processed/yellow_taxi_jan2024_csv_partitioned \
  --partition-by payment_type vendor_id
```

`uv run python -m src.nyc_trips_pipeline --help` lists every flag: `--input-path`,
`--input-file-type`, `--output-path`, `--as-file-type`, `--partition-by` and `--chunksize`.

### Transformations

`transform_data(data, transformations)` takes a `{column: transformation}` mapping.

| Transformation | Example | What it does |
|----------------|---------|--------------|
| `"uppercase"` / `"lowercase"` / `"strip"` | `{"name": "strip"}` | String cleaning. |
| `("type", "int")` / `("type", "float")` | `{"age": ("type", "int")}` | Numeric casting. |
| `("type", "date")` | `{"date": ("type", "date")}` | Parses to datetime; format inferred. |
| `("type", "date", fmt)` | `{"date": ("type", "date", "%d/%m/%Y")}` | Parses using an explicit format. |
| `("age", source)` | `{"age": ("age", "date_of_birth")}` | **Custom** — completed years, as of today. |
| `("age", source, as_of)` | `{"age": ("age", "date_of_birth", "2026-01-01")}` | **Custom** — age at a given date. |
| `("duration", start, end)` | `{"mins": ("duration", "pickup", "dropoff")}` | **Custom** — elapsed minutes between two datetimes. |
| `("duration", start, end, unit)` | `{"hrs": ("duration", "pickup", "dropoff", "hours")}` | **Custom** — `seconds`, `minutes`, `hours` or `days`. |
| `("round", n)` | `{"total_amount": ("round", 2)}` | **Custom** — round a numeric column. |

`age` and `duration` derive a *new* column, so the target need not already exist. Every
other transformation is applied in place. Unparseable dates become `NaT` and are logged
rather than raising, so one bad row cannot fail the whole run.

### Partitioning

`load_data(..., partition_by=...)` accepts one column or a list. When partitioning, the
output path is a **directory** and the writer produces Hive-style layout — parquet via
`partition_cols`, CSV via one `part.csv` per partition:

```text
yellow_taxi_jan2024_csv_partitioned/
└── payment_type=cash/
    └── vendor_id=1/
        └── part.csv
```

The partition values live in the directory names and are dropped from the files themselves.

### Tests

```bash
uv run pytest -q
```

Runs from the repository root or from `py-project/` — `pythonpath` and `testpaths` are set
in `pyproject.toml`, and the fixtures are anchored on the test files rather than the working
directory.

## How the submission works

1. Each member works on a **branch** (`feat/<your-handle>-<thing>`).
2. Open a **PR** into `main`. CI must be green (lint + tests + `terraform validate` + `dbt parse`).
3. A **learning-mate/faculty-trainer reviews** it; the **requester merges**.
4. End of week: the learner tags a demo commit and the cohort does a short walkthrough.

## Rules

- **No secrets, state, or raw data** committed (`.gitignore` covers the usual suspects).
- Any **cloud resources** the pod stands up get **torn down** at the end of the week — especially Composer / GKE / Dataproc.
- Keep it tidy: this repo may be archived after the week.

## Layout

Structure follows the module's brief. Check the README for this mini-project.
