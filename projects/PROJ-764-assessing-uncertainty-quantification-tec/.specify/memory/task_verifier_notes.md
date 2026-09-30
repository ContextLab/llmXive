# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005b** — The provided `code/data/download.py` defines a validator but does not write missing columns to `data/validation_report.json` nor update a config flag, and the required `data/validation_report.json` file is absent. Consequently the fallback logic and flag setting are not implemented.
- **T005d** — The repository lacks the required `data/validation_report.json` file, and the provided `code/data/download.py` does not contain any logic that writes counts of rows with structural descriptors or a list of missing columns to that JSON file. Consequently, the task’s validation‑update requirement is not fulfilled.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015b** — The required data file `data/processed/features_train_20pca.csv` is absent, causing the verification step to fail, and the provided `sparse_gp.py` is incomplete (truncated) with no visible fitting logic, RBF kernel setup, or training routine. The task’s core requirement—loading the PCA features and fitting a Sparse GP with 500 inducing points—is therefore not met.
- **T015c** — The `code/models/sparse_gp.py` file is incomplete (truncated mid‑definition, no training or save logic) and the required output file `results/models/sparse_gp_model.pt` is absent. Consequently the task of saving the fitted GP model to the specified path is not fulfilled.
- **T016a** — The repository lacks the required `results/models/sparse_gp_model.pt` file, and the provided `run_single_seed.py` is truncated (e.g., missing the logic to load model weights, iterate over the seed list, perform inference, and write the exact CSV columns). Consequently the script does not demonstrably fulfill the task’s specifications.
- **T018** — declared artifact(s) missing/empty/invalid: results/uq_predictions_base.csv
- **T023** — No PDF or PNG reliability diagram files are present in the `results/` directory (or any other location). The required visual artifacts for each UQ method are missing, so the task is not satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: results/calibration_report.csv
- **T025b** — declared artifact(s) missing/empty/invalid: results/ece_scores_by_seed.json, results/robustness_report.json
