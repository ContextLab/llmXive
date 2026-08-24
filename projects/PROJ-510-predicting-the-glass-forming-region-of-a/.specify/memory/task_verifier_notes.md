# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure was presented; the required root folder `projects/PROJ-510-predicting-the-glass-forming-region-of-a/` and its sub‑folders `data/`, `code/`, `tests/`, and `docs/` are not shown or listed, so the core artifact the task demanded is missing.
- **T003** — No linting configuration files (e.g., .flake8, pyproject.toml/black settings, pre‑commit hooks) or documentation of flake8/black setup are present. The task required delivering those artifacts, but none were provided.
- **T004** — No evidence of the required `data/raw/` and `data/processed/` directories or a `.gitignore` file containing rules for large files was provided. The implementer’s claim cannot be verified without these artifacts present in the repository.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No code, configuration file, or test showing that the data loading step now raises an explicit error when the `matsci/glass-forming-ability` fetch fails (and that no synthetic fallback is used) was provided. Without such artifact, we cannot confirm the required error‑handling behavior is implemented.
- **T016** — The provided `code/features.py` is incomplete (truncated, lacks any tolerance‑based validation logic and does not contain code to write a DataFrame to `data/processed/processed_alloys.csv`). Moreover, the required output file `data/processed/processed_alloys.csv` is absent from the repository.
- **T017** — No code, script, test, or documentation was provided showing that a validation step was added to check that `critical_cooling_rate` has non‑zero variance and at least 500 entries, nor any error handling for the failure case. The required artifact (e.g., updated ingestion/validation module or a test confirming the check) is missing.
