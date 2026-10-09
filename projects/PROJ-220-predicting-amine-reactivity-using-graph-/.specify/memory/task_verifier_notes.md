# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The required directory `specs/001-predicting-amine-reactivity/` is missing, and the `data/raw`, `data/processed`, `data/derived`, and `artifacts` subfolders are not present in the provided file tree. Without these directories the specified project structure is not fully created.
- **T002** — The provided `pyproject.toml` correctly lists the required dependencies, but there is no accompanying virtual‑environment setup script or any evidence that rdkit version compatibility with torch and torch‑geometric was verified. The task explicitly required such a verification step, which is missing.
- **T003a** — The `[tool.ruff]` section in `pyproject.toml` is missing the required `select` configuration for rules E4, E7, E9, and F.
- **T003b** — The required `.gitignore` file is missing from the provided artifacts. No evidence of its existence or content was supplied.
- **T009b** — declared artifact(s) missing/empty/invalid: tests/integration/test_citation_gate_blocking.py
- **T019** — declared artifact(s) missing/empty/invalid: tests/unit/test_dataset_completeness.py
- **T027** — declared artifact(s) missing/empty/invalid: data/derived/training_metrics.json
- **T028** — declared artifact(s) missing/empty/invalid: tests/unit/test_predictions.py
- **T029** — declared artifact(s) missing/empty/invalid: tests/contract/test_feature_importance.py
- **T030** — declared artifact(s) missing/empty/invalid: tests/integration/test_interpretability_flow.py
- **T032** — declared artifact(s) missing/empty/invalid: data/derived/shap_plots/
- **T035** — declared artifact(s) missing/empty/invalid: tests/unit/test_interpretability_report.py, data/derived/interpretability_report.json
- **T042b** — declared artifact(s) missing/empty/invalid: tests/unit/test_data_fetch_error.py
