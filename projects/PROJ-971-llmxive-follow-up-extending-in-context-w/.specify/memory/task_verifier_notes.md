# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The script `code/src/pipeline/compute_complexity.py` correctly generates `data/processed/task_complexity.csv` and `data/processed/correlation.txt`, but the required accompanying schema file `complexity.schema.yaml` is missing, violating the task’s specification that the CSV be provided with its schema.
- **T005** — Requested task execution failed; rerun successfully: src/pipeline/grid_search_labels.py exit=1
- **T006** — The `train_regressor.py` script runs and writes `metrics.json`, but the metrics show a baseline MSE of 0.0 and a validation MSE > 0, so `meets_sc006` is false – the regressor does **not** beat the temperature‑only baseline as required. Additionally, the promised verification test `code/tests/test_train_regressor_metrics.py` is missing.
- **T016** — The test `code/tests/test_descriptor_schema.py` exists, but it raises a `FileNotFoundError` because the required schema file `specs/001-auto-icwm-latent-dynamics/contracts/descriptor.schema.yaml` is missing, causing pytest to fail. The missing schema file must be added (or the path corrected) and the test must pass for the task to be considered complete.
