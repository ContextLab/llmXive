# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `outputs/fetch_log.txt` file is missing, and there is no evidence that the verification steps (running `pytest` and confirming the log file is non‑empty) were performed. Without this log file the task’s verification criteria are not satisfied.
- **T002** — The pipeline code (`code/src/preprocess.py`) and its unit tests exist, but the required output artifacts are absent: `processed_data.schema.yaml` is missing (so schema validation cannot occur), and the function never produced `data/processed/clean.parquet` nor `outputs/preprocessing_log.json` (both files are reported as missing). Consequently the tests that check for these files would fail, and the task’s validation requirement is not satisfied.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
