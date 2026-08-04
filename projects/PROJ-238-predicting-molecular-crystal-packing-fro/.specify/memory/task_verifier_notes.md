# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — No `utils/descriptors.py` file or any code implementing the six molecular descriptor calculations is present; the submission provides no artifact to verify that volume, surface area, dipole, H‑bond acceptor/donor counts, and polar surface area are actually computed. The required implementation is missing.
- **T015** — No code, script, notebook, or data file was provided that demonstrates the calculation of `packing_coefficient = V_mol / V_cell` nor the filtering of values outside the [0, 1] range. Without such artifacts, we cannot confirm the requirement was implemented.
- **T016** — declared artifact(s) missing/empty/invalid: data/descriptors/raw_descriptors.csv, data/processed/missing_target.log
- **T018** — No `artifact_hashes` file (or any SHA‑256 checksum listings) was presented, and there is no evidence that checksums were generated for the raw CIFs or derived CSV/JSON files. The required artifact is missing, so the task is not satisfied.
- **T023** — No training script, model checkpoint, or evaluation output is present; the claim provides no code, logs, or results demonstrating that a Random Forest regressor was actually trained with default hyperparameters and `random_state=42`. The required artifact (e.g., a Python script/notebook and/or saved model file with accompanying performance metrics) is missing.
- **T024** — No code, notebook, log, model file, or evaluation output showing a Gradient Boosting regressor trained with default hyperparameters and `random_state=42` is present. The required artifact (training script/model and its results) is missing, so the task is not satisfied.
- **T025** — No code, script, notebook, or model artifact that computes and returns the training‑set mean of `packing_coefficient` was presented. Without a concrete implementation (e.g., a function/class, saved model file, or pipeline step) the requirement of providing a working mean‑predictor baseline is not satisfied. The next implementer must add the actual implementation and ensure it is accessible.
- **T029** — declared artifact(s) missing/empty/invalid: results/metrics.json
- **T033** — declared artifact(s) missing/empty/invalid: results/feature_importance.png
