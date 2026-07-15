# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `code/`, `tests/`, and `data/` directories was provided; the claim lacks any actual artifact showing the project structure exists. The implementer must create and show these folders (with at least placeholder files) to satisfy the task.
- **T003** — No linting configuration files (e.g., .flake8, pyproject.toml/black settings, or pre‑commit hooks) are present in the provided evidence, so the task of configuring flake8/black and formatting tools is not satisfied. The implementer must add the appropriate configuration artifacts and ensure they are functional.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The submission provides only the task description and feature specification; there is no evidence of the required `data/raw/` and `data/processed/` directories being created, nor any script or utility for generating checksums. Without these artifacts, the task’s core requirement is not satisfied.
- **T012** — The `tests/contract/test_dataset.py` file exists, but the required `dataset.schema.yaml` file is missing, so the contract tests cannot actually validate the dataset against a schema. The missing schema file must be added (with the expected columns, types, etc.) for the task to be complete.
