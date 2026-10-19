# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — The required input file `data/derived/baseline_test_predictions.csv` is missing, so `compute_baseline_metrics()` cannot run and the expected outputs `data/derived/baseline_metrics.csv` and `data/derived/baseline_residuals.png` were never created. Additionally, the unit test fails to import `pytest` in the conftest, so it never validates the CSV/PNG generation. The task’s core artifacts are absent.
- **T102** — Requested task execution failed; rerun successfully: code/analysis/explainability.py exit=1
