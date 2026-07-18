# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The repository lacks the required fixture `data/fixtures/monthly_sample.csv`, the output file `data/processed/synced.csv`, and the schema file `contracts/dataset.schema.yaml`. Moreover, the provided `test_pipeline_monthly_sync` does not reference the fixture nor validate the processed CSV against the schema, so the task’s specifications are not met.
- **T013c** — The `write_synced_csv` function in `code/data/align.py` is truncated and does not show the full implementation (e.g., the column‑assertion list is incomplete and there is no code that checks for NaNs or writes to `data/processed/synced.csv`). Moreover, the required output file `data/processed/synced.csv` does not exist. Both the function implementation and the expected output are missing.
