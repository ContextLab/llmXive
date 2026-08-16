# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No evidence of a logging configuration or any files under `data/logs/` was provided; the required artifact (logging infrastructure capturing exclusion counts and training metrics) is missing. The implementer must add the appropriate logging setup and ensure logs are written to the specified directory.
- **T009** — No evidence of a seed‑configuration file or code (e.g., a `seed_config.py`, JSON/YAML settings, or similar) located in a `code/` directory is provided; the claim lacks any artifact showing that random seeds are pinned and managed. The required environment‑configuration implementation is therefore missing.
- **T014** — declared artifact(s) missing/empty/invalid: code/training/train_baseline.py
- **T016** — No code, script, or log file was provided showing that RDKit parsing failures are caught, counted, logged, and excluded from the dataset as required by task T016. The implementer’s claim cannot be verified without concrete artifacts.
- **T017** — No code, log files, or documentation showing that logging for baseline training operations and exclusion counts was added were provided; the only evidence is the task description itself, which does not demonstrate the required implementation.
- **T022** — No training script, runtime logs, or result files were provided to demonstrate that a GNN model was trained and finished within 6 hours on a 2‑core CPU runner. The required artifacts (e.g., the MPNN training code, execution timing evidence, and the JSON evaluation report) are missing, so the task’s requirement cannot be verified.
- **T024** — declared artifact(s) missing/empty/invalid: results/gnn_metrics.json
- **T025** — No comparison script, function, or report that computes the RMSE delta between the Random Forest baseline and the GNN model is provided. The required artifact (code or output showing the delta calculation without a pass/fail flag) is missing, so the task is not satisfied.
