# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No configuration files, scripts, or documentation for managing environment variables (e.g., `.env` files, `dotenv` setup, or path‑handling code) were provided. The claim does not include any artifact that shows API keys or data paths are configured, so the requirement is unmet.
- **T008** — No code, configuration files, or documentation for a base logging system (e.g., Python logging setup, log schema, provenance capture scripts) is present. The only artifacts described relate to data acquisition, modeling, and visualization, not to logging infrastructure, so the required artifact is missing.
- **T012** — The `code/download_data.py` script is only partially shown and lacks the actual download logic and JSON‑writing code; moreover the required `data/raw/download_status.json` file does not exist. The implementation does not demonstrably fulfill the fetching, DOI verification, and output requirements.
- **T014** — declared artifact(s) missing/empty/invalid: code/preprocess.py
- **T015** — declared artifact(s) missing/empty/invalid: code/preprocess.py
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_data.csv
- **T016b** — The required artifact `data/processed/modeling_config.json` does not exist, so the code cannot read the `abort_flag` or enforce the N ≥ 80 gate as specified. The missing file must be provided (or generated) for the task to be satisfied.
- **T018** — No code, script, or documentation was presented that adds the required validation logic to filter out trait/personality measures from the primary regression while permitting them only as covariates in secondary checks. Without any artifact to inspect, the task’s specification has not been demonstrably fulfilled.
- **T021b** — No code, notebook, script, or output files showing a Ridge Regression model with k‑fold cross‑validation are present, and there are no reported ridge coefficients or feature‑importance values. The required artifact is missing, so the task is not satisfied.
