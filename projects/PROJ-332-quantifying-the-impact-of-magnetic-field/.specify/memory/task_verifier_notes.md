# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was provided that the required directories (`code/`, `data/raw/`, `data/processed/`, `artifacts/`, `tests/`) actually exist in the project; the only artifacts shown are feature specifications, not a filesystem layout. The implementer must create and show the directory structure as specified.
- **T001b** — No `.gitignore` file was presented in the evidence; without an actual, non‑empty `.gitignore` listing Python‑related patterns and data‑artifact exclusions, the task requirement is not satisfied. The implementer must add a proper `.gitignore` to the repository.
- **T003a** — No flake8 configuration file (e.g., `.flake8`, `setup.cfg` with `[flake8]` section, or `tox.ini`) was provided or referenced, so there is no evidence that linting rules were actually configured. The required artifact is missing.
- **T003b** — No configuration file (e.g., `pyproject.toml`, `black.toml`, or similar) or any other artifact defining Black formatting rules is present in the provided evidence. Without such a file, the requirement to configure Black cannot be verified as fulfilled.
- **T006b** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T013** — The repository contains a partial `metrics.py` that defines only q‑profile extraction and shear calculation; it does not implement retrieval of `island_width`, the `derive_island_width` fallback, input fetching from EFIT, discharge exclusion logic, or CSV writing. Moreover, the required output file `data/processed/metrics.csv` is absent. These missing components mean the task’s requirements are not satisfied.
- **T014b** — The validator module exists, but the required schema files (`contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`) are missing, so the validation logic cannot actually be performed. Without these contracts the task’s core requirement is unmet.
- **T028** — declared artifact(s) missing/empty/invalid: outputs/summary_report.json
