# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`projects/PROJ-334-predicting-avian-song-variation-with-cli/`, `data/`, `code/`, `tests/`) being present or populated was provided; the claim lacks any artifact listing or screenshots confirming their creation. The implementer must create and show the directory structure.
- **T002** — The implementer only supplied a feature specification and user stories; there is no evidence of a Python project being created, nor any files (e.g., `pyproject.toml`, `requirements.txt`, `setup.cfg`, or a virtual environment) listing the required dependencies. Consequently, the core task of initializing the project with the specified packages is not satisfied.
- **T003** — The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml` entries for Black, a `.ruff.toml` or `ruff.toml`, or any related setup scripts). Without these artifacts, the requirement to configure ruff and Black is not satisfied. The next implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- **T004** — declared artifact(s) missing/empty/invalid: data/checksums.txt
- **T005** — No configuration loader code or files were presented; the evidence consists only of a project specification unrelated to a base configuration loader. Consequently, the required artifact (a loader handling environment variables and paths) is missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — declared artifact(s) missing/empty/invalid: data/checksums.txt
- **T012** — declared artifact(s) missing/empty/invalid: data/checksums.txt
- **T013** — The repository lacks the required `contracts/*.schema.yaml` files (e.g., `schema.yaml` is missing), so validation cannot be performed. Moreover, `code/ingestion.py` is truncated and does not show a complete implementation of CSV loading, schema validation, or coordinate reprojection using the specified T008/T008a utilities. The task’s core requirements are therefore not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/analysis_dataset.csv, data/checksums.txt
