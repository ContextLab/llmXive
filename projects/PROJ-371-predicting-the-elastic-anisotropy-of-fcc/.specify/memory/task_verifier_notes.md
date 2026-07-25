# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T014b** — declared artifact(s) missing/empty/invalid: src/data/group_elements.py, data/processed/element_groups.json
- **T015** — declared artifact(s) missing/empty/invalid: src/cli/run_pipeline.py, data/processed/elastic_anisotropy.csv
- **T016** — declared artifact(s) missing/empty/invalid: src/cli/run_pipeline.py
- **T019#1** — declared artifact(s) missing/empty/invalid: tests/unit/test_evaluate.py
- **T022** — declared artifact(s) missing/empty/invalid: src/models/evaluate.py, data/processed/residuals_and_flags.json
- **T023** — No timing logs, benchmark results, or execution evidence were provided to demonstrate that the model training script actually finishes within 1 hour on a standard CPU environment. Without such artifacts, we cannot confirm the acceptance criterion for US‑2. The implementer must supply concrete run logs or a reproducible benchmark showing the training duration.
- **T024** — No `output/metrics.json` file or any evidence of logging hyperparameters and performance metrics is present; without this artifact the task requirement is not satisfied. The implementer must create the JSON file in the specified path containing the model’s hyperparameter settings and the evaluation metrics (e.g., R², MAE, RMSE) for traceability.
- **T025** — declared artifact(s) missing/empty/invalid: tests/unit/test_evaluate.py
- **T026** — declared artifact(s) missing/empty/invalid: tests/unit/test_sensitivity.py
