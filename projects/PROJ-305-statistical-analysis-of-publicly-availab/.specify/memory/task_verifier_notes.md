# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`src/`, `tests/`, `data/`, `output/`) was presented or described in the provided evidence; the implementer gave only a feature specification without showing the required folders or any files within them. Consequently the task requirement is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or documentation of their setup are present in the provided evidence, so the requirement to configure ruff/flake8 and Black cannot be confirmed. The implementer must add the actual configuration artifacts and demonstrate they are active in the project.
- **T004** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: src/data/validate.py, schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/plots.py
- **T009** — declared artifact(s) missing/empty/invalid: src/main.py
- **T039** — The required file `src/main.py` is missing entirely, so no memory‑check logic or chunked‑processing code could be present. The task’s core deliverable does not exist.
- **T040** — The required file `src/main.py` is missing entirely, so no memory‑check logic could have been added. Consequently the task’s deliverable does not exist.
- **T011** — The repository lacks `src/data/validate.py`, so the unit tests cannot even import the functions they are meant to test. Moreover, the provided `tests/unit/test_validate.py` (truncated) does not contain a test that asserts an `E_SCHEMA_MISSING` exception is raised for missing columns; it only checks for a generic `SystemExit`. Both the required source file and the specific test for `E_SCHEMA_MISSING` are missing.
- **T014** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T016** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T018** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T019** — Both required artifacts (`src/analysis/disproportionality.py` and `tests/unit/test_disproportionality.py`) are missing from the repository, so no unit test or implementation exists to verify the ROR/PRR/IC calculation logic. The task’s deliverable is therefore not present.
