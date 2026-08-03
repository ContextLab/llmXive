# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure (`code/`, `data/raw/`, `data/processed/`, `data/features/`, `tests/`, `state/projects/`) is present in the provided artifacts; there is no file or listing showing these folders were created. The claim cannot be verified without concrete evidence.
- **T001c** — No evidence of a `tests/` directory (or its sub‑directories `contract/`, `integration/`, `unit/`) was provided; the implementer did not supply any file listings, screenshots, or code confirming the required structure exists. The task remains undone.
- **T001d** — declared artifact(s) missing/empty/invalid: PROJ-122-identifying-structure-property-relations.yaml
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or CI scripts invoking flake8/black) are present in the provided evidence, nor any documentation showing that these tools have been set up and integrated into the project. The required artifacts to demonstrate that linting and formatting are configured are missing.
- **T004** — No `.gitignore` file or `pytest` configuration (e.g., `pytest.ini`, `conftest.py`, or test directory) was presented in the evidence, so the required artifacts are missing. The implementer must add these files with appropriate content to satisfy the task.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The `tests/test_contract.py` file exists, but it relies on `dataset.schema.yaml` (and `output.schema.yaml`) which are missing from the repository, causing the fixtures to fail. Without these schema files the contract tests cannot actually validate any data, so the required dependency tasks (T005, T006) are not satisfied. The missing schema files must be added for the task to be complete.
- **T020** — declared artifact(s) missing/empty/invalid: state/projects/PROJ-122-identifying-structure-property-relations.yaml
