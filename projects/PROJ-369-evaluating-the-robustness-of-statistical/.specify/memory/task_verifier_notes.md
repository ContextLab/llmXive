# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project files, directories, or code were presented; the claim provides only a textual description of the required features without any actual artifact (e.g., folder hierarchy, scripts, notebooks, or data) to verify that the project structure has been created. The required implementation of the ingestion/preprocessing pipeline and synthetic data generation is absent.
- **T003** — I looked for linting/formatting configuration artifacts (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8` or equivalent) and any setup scripts, but none were presented. Without those files the task of configuring ruff/flake8 and Black is not demonstrated. The implementer must add the actual configuration files and ensure they are non‑empty and correctly set up.
- **T004** — No pytest configuration file (e.g., pytest.ini or conftest.py) or the required test directories (`tests/unit`, `tests/integration`, `tests/contract`) are present in the provided evidence. Consequently, the task of initializing the pytest setup and directory structure has not been demonstrated.
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T007** — declared artifact(s) missing/empty/invalid: src/data/schemas.py
- **T011** — The required unit‑test file `tests/unit/test_ingestion.py` does not exist in the repository, so no test verifying checksums or error handling for missing files is present. Consequently the task’s deliverable is missing.
