# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or similar) or any evidence of ruff/black setup were presented. The claim provides only a unrelated feature specification, so the required linting/formatting tooling is missing.
- **T006** — No evidence of the required `data/raw/`, `data/interim/`, `data/processed/`, or `data/external/` directories is provided; the implementer did not supply any artifact confirming the directory structure exists.
- **T007** — No evidence of a `tests/` directory or its required subfolders (`unit/`, `integration/`, `contract/`) is present in the provided artifacts; the implementer did not supply any file listings or screenshots confirming the structure.
- **T008** — No pytest configuration file (e.g., `pytest.ini`, `pyproject.toml`, or `setup.cfg`) containing coverage threshold settings and a 300‑second timeout is present in the provided evidence. Without such a file, the task of configuring pytest with the required coverage and CI‑compatible timeout cannot be confirmed as completed.
- **T017** — No `quickstart.md` file was presented in the evidence, nor any excerpt or link confirming its existence in `specs/001-compression-impact-gw-reconstruction/`. Without the required document, the task’s deliverable is missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/data/inject.py
- **T020** — declared artifact(s) missing/empty/invalid: src/data/main.py
