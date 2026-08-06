# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project files or directory tree were presented; there is no evidence of a created codebase, folder hierarchy, or any non‑empty artifact that would constitute the required project structure. The implementer must add the actual project scaffold (e.g., README, src/, data/, scripts/, config files) to satisfy the task.
- **T003** — The implementer provided only a feature specification for uncertainty quantification and no linting/formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml`, or a pre‑commit hook). Consequently, the required artifact to configure Ruff and Black is missing.
- **T005** — The repository contains `code/data/download.py` with a plausible implementation, but the required output file `data/raw/oqmd.parquet` is missing, so the task of actually fetching and saving the dataset has not been fulfilled. The missing parquet file must be generated and present for the task to be considered complete.
- **T006** — The provided `preprocess.py` is truncated, never applies PCA to produce exactly 20 components, and does not write the required `features_20pca.csv` or `exclusion_log.json`. Both output files are missing from the repository. The implementation therefore does not meet the task specifications.
- **T007** — declared artifact(s) missing/empty/invalid: code/data/validation_report.json, data/processed/exclusion_log.json, data/validation_report.json
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The `code/models/baseline_nn.py` file exists and implements a two‑hidden‑layer heteroscedastic network within the parameter budget, but the required output artifact `results/models/baseline_seed42.pt` is absent from the repository. Without the saved model file, the task’s deliverable is not fulfilled.
- **T014** — The `code/models/mc_dropout.py` file exists and contains a dropout‑enabled model with `p=0.2` and logic for 30 stochastic forward passes, but the required output artifact `results/models/mc_dropout_model.pt` is missing and the script never saves the trained model to that path. The task’s primary deliverable is therefore not satisfied.
- **T018** — declared artifact(s) missing/empty/invalid: results/uq_predictions.csv
- **T022b** — declared artifact(s) missing/empty/invalid: results/uq_predictions.csv, results/calibration_report.csv, results/uncertainty_decomposition.csv
- **T024** — declared artifact(s) missing/empty/invalid: results/calibration_report.csv
- **T025a** — declared artifact(s) missing/empty/invalid: results/ece_scores_by_seed.json
