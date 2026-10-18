# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/pipeline/run_all.py exit=1
- **T002** — Checked `src/pipeline/ingest.py` (implements validation, harmonization, imputation, encoding) and `src/tests/test_ingest.py`. The pytest run fails with a `NameError: name '_fetch_with_metadata' is not defined` in the CLI wrapper, so the ingestion script never completes, and consequently `data/processed/cleaned_dataset.csv` is not created. The required unit test does not pass and the cleaned CSV is missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/results/vif_diagnostics.json
- **T003** — The `src/pipeline/features.py` script implements the required engineering steps, but the required output file `data/processed/features.parquet` is missing, and the script exits with an error because the prerequisite `cleaned_dataset.csv` is not present. Consequently no feature matrix (or residualization evidence) can be inspected, so the task’s deliverables are not satisfied.
- **T004** — Requested task execution failed; rerun successfully: src/pipeline/train.py exit=1; src/pipeline/evaluate.py exit=1
