# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T103** — Checked `code/data/validate.py` – it loads `descriptor_names.json` and exits 0/1 based on validation logic, but there is no execution record showing `python code/data/validate.py data/processed/descriptors.parquet` actually returning 0, nor a test where a column name is corrupted to produce a non‑zero exit. Execution evidence for both the successful and failure cases is missing.
- **T102** — The `tests/contract/validators.py` file exists, but `pytest tests/contract/ -q` does not pass: `test_dataset_schema.py` fails because the descriptor DataFrame is missing many expected columns, causing a validation error. The contract test suite must all succeed for the task to be considered complete.
- **T101** — Requested task execution failed; rerun successfully: code/data/generate_descriptors.py exit=1; tests/contract/test_dataset_schema.py exit=1; tests/contract/test_model_output.py exit=1; tests/integration/test_full_pipeline.py exit=2
