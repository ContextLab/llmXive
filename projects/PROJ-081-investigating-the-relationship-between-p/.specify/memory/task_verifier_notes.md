# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project lacks the required `scripts/`, `data/raw/`, and `outputs/` directories (and the `outputs/fetch_log.txt` file is missing). The three fetch functions raise an `AttributeError` because they use `pd.compat.StringIO`, causing all `test_fetch_data.py` tests to error, so the verification step fails and the paired‑species count is never checked.
- **T002** — The implementation `code/src/preprocess.py` raises errors during execution (ambiguous Series truth value and JSONDecodeError when loading the schema), causing all three pytest cases to fail. Consequently the required output files `data/processed/clean.parquet` and `outputs/preprocessing_log.json` are never created, and the schema file `processed_data.schema.yaml` is missing/empty. The tests therefore do not pass and the task’s deliverables are not satisfied.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
