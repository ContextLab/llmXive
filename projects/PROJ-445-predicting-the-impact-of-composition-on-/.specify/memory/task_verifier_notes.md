# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/split.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T016** — No script, configuration, or manifest file was provided that adds validation to check that all derived features are saved under `data/processed/` and that their content hashes are recorded in `state/manifest.json`. The required artifact (validation code and updated manifest) is missing.
- **T022** — declared artifact(s) missing/empty/invalid: src/utils/metrics.py
- **T023** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T019** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T020** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T026** — The required artifact `tests/integration/test_metrics.py` does not exist, so no integration test for bootstrapped confidence interval calculation is present. The task cannot be considered completed until this file is added with the appropriate test implementation.
- **T025#1** — No model files or checksum records were presented in the evidence; the required `data/models/lofo_models/` directory with N‑1 distinct Gradient Boosting models (each leaving out one chemical family) is absent, so the task’s deliverable is not demonstrated.
- **T031** — No `artifacts/shap_report.md` file is present, and there is no evidence that the report includes the required sections (feature importance, CI results, transferability metrics, the “Power Analysis” text extracted from `state/power_analysis.json`, and the “Causal Disclaimer” from `artifacts/causal_disclaimer.txt`). The implementer must create the markdown report with all specified content.
- **T032** — No `artifacts/performance_metrics.json` file was presented, and no content showing the required metrics (RMSE, R², MDES, VIF, confidence interval bounds, significance flag, transferability flags) was provided. The implementer must create and supply this JSON file with the specified fields.
- **T033** — No `state/manifest.json` file was provided, and there is no evidence that any SHAP subset hashes were recorded or reported. The required artifact is missing, so the task is not satisfied.
