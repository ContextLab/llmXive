# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (code/, data/raw, data/processed, tests/) is provided; the implementer did not supply any artifact showing that the project structure was created.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) were provided or referenced, so the required artifact for configuring ruff/flake8 and Black does not exist. The task therefore remains unfinished.
- **T005** — The required synthetic dataset file `data/processed/synthetic_mar_v1.csv` is not present, and the referenced schema `contracts/dataset.schema.yaml` is also missing, so the code cannot be verified to produce output that conforms to the schema. The next implementer must generate the CSV artifact (and optionally run the script) and provide the missing schema file.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/baseline_results.json
- **T017** — No code, tests, or documentation were provided showing that error handling for PSU = 1 clusters was added, nor any evidence of warnings or exclusion logic integrated into T009b/T015. The required implementation artifact is missing.
