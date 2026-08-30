# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — The repository contains a partially shown `code/03_compute_graph_metrics.py`, but the file is truncated and does not demonstrate the required subject‑processing loop, the try/except handling with `sys.exit(1)`, or the CSV writing logic. Moreover, the required output `data/processed/graph_metrics.csv` is absent. Consequently the task’s specifications are not fully satisfied.
- **T041** — No test file containing `test_collinearity_filter` is present, and there is no evidence of a failing unit test that generates a matrix with duplicate columns and asserts the collinearity filter removes one. The required artifact is missing, so the task is not satisfied.
- **T023** — The repository contains a `code/04_train_model.py` file, but it does not show a `train_model(data, decline_threshold=3)` function and the required output artifacts (`data/processed/model.pkl`, `cv_results.json`, `model_params.json`) are absent. The task therefore is not fulfilled.
