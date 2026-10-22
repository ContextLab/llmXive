# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project lacks the required `code/src/config.py`, `code/src/fetch_data.py`, and `code/tests/test_fetch_data.py` files, the `scripts/` and `data/raw/` directories, and the `outputs/fetch_log.txt` log file. Consequently the fetch functions, their tests, and the verification steps are not present, so the task is not satisfied.
- **T002** — The run of `pytest` shows all three tests failing: a ValueError in the column‑absence check, and ImportErrors when trying to write the Parquet file because no parquet engine (pyarrow/fastparquet) is installed. Consequently `data/processed/clean.parquet` and `outputs/preprocessing_log.json` are never created, and the required schema file `processed_data.schema.yaml` is missing, so the pipeline does not perform the mandated JSON‑schema validation. The implementation therefore does not satisfy the task’s specifications.
- **T003** — Requested task execution failed; rerun successfully: code/src/correlation_analysis.py exit=1
