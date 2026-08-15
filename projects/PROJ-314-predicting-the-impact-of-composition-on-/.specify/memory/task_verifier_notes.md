# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.ruff]` settings, a `.ruff.toml`, or a `black` configuration) are present in the provided evidence, nor any scripts or documentation showing that `ruff` and `black` have been set up for the project. The required artifacts to demonstrate that linting and formatting are configured are missing.
- **T004** — No evidence was provided that the `data/raw/`, `data/processed/`, and `data/artifacts/` directories actually exist (e.g., a directory listing, screenshots, or code that creates them). Without such artifacts, we cannot confirm the task was fulfilled.
- **T012a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T025** — The integration test file exists but is truncated and does not show code that creates `data/results/cv_split_report.json`. Moreover, the required JSON report file is absent from the repository. The task’s core output—a stratification report JSON with the specified schema—is missing.
- **T027b** — The `train_models()` function is truncated and never performs model training, cross‑validation loops, or writes any feature‑importance data. Moreover, the required `data/results/fold_importances.json` file does not exist. Both the core functionality and the critical output artifact are missing.
- **T041** — declared artifact(s) missing/empty/invalid: data/artifacts/shap_summary.png, data/results/feature_ranking.csv, data/results/stability_metrics.json
- **T056** — No code, tests, or documentation were provided showing that `group_correlated_features()` is now invoked before feature ranking in `generate_interpretation()`, nor that VIF > 5 triggers clustering and aggregate importance reporting. The required implementation artifact is missing.
- **T057** — declared artifact(s) missing/empty/invalid: data/results/permutation_test_report.json
- **T059** — declared artifact(s) missing/empty/invalid: data/processed/step_final_cleaned.csv
- **T062** — The repository lacks a `calculate_dataset_power()` implementation in `code/ingestion.py` (the file ends before such a function appears) and the required `data/reports/data_availability_report.json` file is absent, so the statistical power field cannot have been added. Both the code change and the output artifact are missing.
