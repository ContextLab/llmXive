# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `outputs/fetch_log.txt` file is missing, and the `fetch_hpid()` function raises a `KeyError` because the Titanic CSV does not contain a `PassengerId` column, causing all `test_fetch_data.py` tests to error. Consequently the required pytest verification does not pass.
- **T002** — The implementation `code/src/preprocess.py` raises errors during execution (ambiguous Series truth value and JSONDecodeError when loading the schema), causing all three pytest cases to fail. Consequently the required output files `data/processed/clean.parquet` and `outputs/preprocessing_log.json` are never created, and the schema file `processed_data.schema.yaml` is missing/empty. The tests therefore do not pass and the task’s deliverables are not satisfied.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
