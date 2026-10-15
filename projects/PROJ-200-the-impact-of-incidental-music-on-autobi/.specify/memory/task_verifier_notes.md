# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — declared artifact(s) missing/empty/invalid: state.yaml
- **T001** — The project layout directories exist, `code/config.py` defines the required thresholds and seed, and `quickstart.md` documents the execution commands. However, `requirements.txt` does not list the required packages `statsmodels` and `pyarrow`; it only mentions them in comments and includes only `python-levenshtein`. The missing explicit dependencies cause the task to be incomplete.
- **T002** — Checked `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` – they exist and contain definitions that appear to align with the fields described in `spec.md`. However, there is no evidence that these schemas were actually validated with `jsonschema`; the provided test log fails before reaching any validation step due to an unrelated import error. A successful validation run (or passing test output) is required to satisfy the task.
- **T003** — The required output artifacts `data/processed/ingested_cohort.parquet`, `data/processed/user_track_pairs.parquet`, and `data/final/regression_summary.csv` are all missing from the project, so the pipeline has not produced the real result rows nor the regression summary with the required columns.
- **T004** — Requested task execution failed; rerun successfully: code/data_ingestion.py exit=1
