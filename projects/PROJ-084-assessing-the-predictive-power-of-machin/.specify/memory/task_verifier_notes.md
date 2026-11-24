# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `specs/.../contracts/output.schema.yaml` (valid YAML with required keys) and `code/utils/validators.py` (functions exist and use Pydantic). However `dataset.schema.yaml` is missing, causing `validate_dataset_schema` to fail the required smoke‑check, and `code/config.py` lacks the listed constants (`TRAIN_VAL_TEST_SPLIT_RATIOS`, `BATCH_SIZE_ROWS`, `SC003_HIGH_YIELD_PERCENTILE`, `SUBSET_SIZE`). These omissions prevent the task from being fully satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/preprocessing/download.py exit=1
