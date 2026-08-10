# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No code, configuration files, or documentation were provided to show that environment variables for data paths and random seeds have been set up or managed. The claim lacks any tangible artifact demonstrating the required configuration.
- **T016** — No code, script, notebook, or data artifact showing that gene‑expression values were aggregated into pathway‑level (e.g., TPS family) features is present. The claim lacks any tangible implementation or output that demonstrates the required dimensionality‑reduction step.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/merged_dataset.csv, data/results/data_validation_report.json
- **T022** — No code, notebook, or configuration file is present that demonstrates imputation parameters being fitted exclusively on training folds; the claim is unsupported by any artifact. A concrete implementation (e.g., a preprocessing pipeline integrated with cross‑validation that fits the imputer inside each training split) is required to satisfy T022.
- **T023** — The required artifact `data/results/model_metrics.json` does not exist, so no R² or RMSE metrics are provided. The implementer must create this JSON file with the calculated metrics.
- **T024** — declared artifact(s) missing/empty/invalid: data/models/random_forest.pkl
- **T025** — Both required files `data/results/model_metrics.json` and `data/results/interpretation_report.json` are missing, so the disclaimer cannot be present and the tests in `tests/test_model.py` would fail. The task’s core requirement—to inject the associational disclaimer into those JSON files—is therefore not satisfied.
- **T030** — declared artifact(s) missing/empty/invalid: data/results/feature_importance_pvalues.json
- **T034** — No updated `quickstart.md` containing the synthetic data generation and full pipeline execution commands, nor an updated `research.md` with data availability status, were provided as evidence. The required documentation artifacts are missing.
- **T036** — The required `data/results/perf_metrics.json` file does not exist, so no peak RAM usage was recorded, and the memory profiling requirement is unmet. The implementer must run `memory_profiler` on the full pipeline and create the JSON file with the measured peak RAM (ensuring it is below 6 GB).
- **T037** — No evidence of any files under `tests/unit/` was provided, and there is no listing or content showing additional unit tests that cover the specified edge cases (missing data, datasets with fewer than 50 samples). The required test artifacts are therefore missing.
- **T038** — No evidence of a `quickstart.md` validation run (e.g., execution logs, reproduced outputs, or a reproducibility report) is present; the implementer provided no artifacts demonstrating that the end‑to‑end pipeline was executed and validated. The required validation output is missing.
