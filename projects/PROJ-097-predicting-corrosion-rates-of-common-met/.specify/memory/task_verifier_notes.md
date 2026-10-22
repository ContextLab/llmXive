# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/pipeline/run_all.py exit=1
- **T002** — The `src/pipeline/ingest.py` implementation exists, but the required output file `data/processed/cleaned_dataset.csv` is missing, and there is no evidence that `pytest src/tests/test_ingest.py` was run successfully. Without the cleaned CSV and a passing test run, the task’s verification criteria are not satisfied.
- **T019** — Requested task execution failed; rerun successfully: src/pipeline/vif.py exit=1
- **T003** — The `src/pipeline/features.py` script implements the required engineering steps, but the required output file `data/processed/features.parquet` is missing, and the script exits with an error because the prerequisite `cleaned_dataset.csv` is not present. Consequently no feature matrix (or residualization evidence) can be inspected, so the task’s deliverables are not satisfied.
- **T004** — Requested task execution failed; rerun successfully: src/pipeline/train.py exit=1; src/pipeline/evaluate.py exit=1
