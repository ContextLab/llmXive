# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The repository contains the required `src/modeling/config.yaml` file, but there is no accompanying code or script that actually loads this configuration (e.g., a Python module using `yaml.safe_load`). The task explicitly requires setting up environment configuration management by loading the file, which is not demonstrated. Implement a loader (e.g., `src/modeling/config.py`) that reads the YAML and makes the settings available.
- **T013** — The `src/utils/chemistry.py` file exists but relies on `config.yaml` for reaction templates, and that file is missing, so no real patterns are available. Moreover, the implementation uses a simplistic string‑contain check rather than proper reaction template matching (e.g., RDKit SMARTS), and does not demonstrate classification into the three required types. The required configuration and robust matching logic are absent.
- **T016** — No code, script, or modified CSV file was presented showing the added logic to count samples per class, log warnings for classes with fewer than 1,000 rows, and physically remove those rows from the output. The required artifact is missing, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/filtered_reactions.csv
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/feature_matrix.parquet
- **T027** — declared artifact(s) missing/empty/invalid: data/models/xgboost_model.json, data/processed/training_log.json
