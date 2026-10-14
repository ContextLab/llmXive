# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Requested task execution failed; rerun successfully: src/pipeline/extract_descriptors.py exit=1
- **T005** — The grid‑search script and the generated `data/labels.csv` are present and contain plausible success rates, but the required schema file `label.schema.yaml` is missing, causing the contract test to fail and preventing validation of the CSV against the schema. The task’s verification step is therefore not satisfied.
- **T006** — Checked `src/pipeline/train_regressor.py` (implementation present) and the generated `data/metrics.json` (val_mse = 1.0295, baseline_mse = 0.475, `meets_sc006` = false). The required verification condition `val_mse < 0.9 * baseline_mse` is not met, and the unit test that asserts this fails. The task therefore does not satisfy the improvement requirement.
- **T008** — Requested task execution failed; rerun successfully: code/src/pipeline/validate_autocwm.py exit=1
