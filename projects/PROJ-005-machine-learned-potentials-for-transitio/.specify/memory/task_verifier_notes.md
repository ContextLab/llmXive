# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No evidence of a `data/raw/` directory or any checksum‑verification code (e.g., scripts, functions, or configuration files) is provided. The required artifact is missing, so the task is not satisfied.
- **T011** — declared artifact(s) missing/empty/invalid: src/data/splits.py
- **T028** — declared artifact(s) missing/empty/invalid: src/data/splits.py, src/models/ensemble.py
- **T015b** — The provided `src/data/ingest.py` does not contain any logic that checks a count and writes `data/processed/data_scarcity_flag.json`, and the expected JSON file is absent from the repository. Both the required code change and the output artifact are missing.
- **T016** — declared artifact(s) missing/empty/invalid: src/data/graph_construction.py
- **T017** — declared artifact(s) missing/empty/invalid: src/data/sweep_cutoff.py, data/results/cutoff_sensitivity.json
- **T018** — No code, script, configuration, or documentation was provided that implements outlier handling (i.e., detecting samples with coordination numbers > 6 and flagging them for exclusion from training while keeping them in the test set). The required artifact is missing, so the task is not satisfied.
- **T019** — declared artifact(s) missing/empty/invalid: schema.yaml
