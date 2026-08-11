# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No logging configuration file, code snippet, or documentation was provided that sets up a logging infrastructure to emit warnings for missing geometric data or metallic behavior outliers. The required artifact is missing, so the task is not satisfied.
- **T009** — No configuration artifact (e.g., a `.env`, `config.yaml`, or Python module) defining random seeds and dataset URLs is present in the provided evidence, nor any documentation describing such setup. Consequently the requirement to establish environment configuration management is not satisfied.
- **T011#1** — The required file `tests/integration/test_ingestion.py` does not exist, so no integration test is present to verify the data ingestion pipeline. The task’s core artifact is missing, making the claim of completion invalid.
- **T012** — The repository contains `code/data/ingestion.py`, but the required fallback file `data/raw/mock_electrolytes.csv` is absent, so the script cannot satisfy the fallback behavior. Additionally, the provided source is truncated, leaving uncertainty about proper filtering logic. The missing mock CSV must be added (with the correct schema) and the script verified to fully implement the task.
- **T017** — No code, script, or test output was provided showing that a validation step was added to check for missing values in the feature matrix before it is written out. Without an artifact (e.g., a function, unit test, or log demonstrating the check), we cannot confirm the requirement was implemented. The next implementer must add and commit the validation logic and supply the corresponding code or test evidence.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/electrolyte_features.csv, data/processed/electrolyte_heldout.csv
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/bins.csv
- **T024** — No code, data, or report was provided that implements the required logic to find descriptors that enter the top‑3 importance at the high‑potential (4 V) bin but are absent from the low‑potential (0‑2 V) bin, nor any documentation explicitly referencing the spec’s 3‑5 V range and the known 4 V mapping limitation. The implementer must supply the actual implementation (e.g., a script or notebook) and its output demonstrating the identified descriptors and the required spec commentary.
- **T025** — declared artifact(s) missing/empty/invalid: data/validation/feature_importance_heatmap.png
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/model_run.json
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/model_run.json
- **T033** — declared artifact(s) missing/empty/invalid: data/validation/sensitivity_report.md
