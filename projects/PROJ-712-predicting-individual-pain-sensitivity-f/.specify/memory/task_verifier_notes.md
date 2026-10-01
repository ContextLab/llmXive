# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`data/raw/`, `data/processed/`, `artifacts/`, `state/`, `code/`, `tests/`) being present on disk is provided; the claim lacks any artifact confirming the project structure was created. The implementer must supply a directory listing or screenshots showing these folders exist.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — declared artifact(s) missing/empty/invalid: tests/integration/test_pipeline.py
- **T017** — The repository contains `code/main.py` with an aggregation function and the required assertion, but the script never writes the DataFrame to `data/processed/feature_matrix.csv` (the file is missing). Consequently the required output artifact does not exist, so the task is not fulfilled.
