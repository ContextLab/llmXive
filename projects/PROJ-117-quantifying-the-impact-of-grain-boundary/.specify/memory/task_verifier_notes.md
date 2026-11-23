# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows the `code/`, `data/raw/`, `data/processed/`, and `models/` directories exist, but the required `artifacts/` directory is missing from the project structure. Adding an empty (or .gitkeep‑containing) `artifacts/` folder will satisfy the task.
- **T002** — The `requirements.txt` file exists and lists the required packages, but it does not pin them to specific versions (e.g., `pandas==1.5.3`). The task explicitly required *pinned* dependencies, and the current file fails to meet that specification (and also includes extra packages not requested). The implementer must add exact version specifiers for each listed dependency and remove any unintended entries.
- **T003** — The evidence provided contains no linting or formatting configuration files (e.g., `pyproject.toml` with Black and Ruff settings, a `.flake8` file, or a pre‑commit hook invoking these tools). Without such artifacts, the requirement to “configure linting (ruff/flake8) and formatting (black) tools” is not satisfied. Add the appropriate configuration files and, optionally, CI integration to complete the task.
- **T004** — The `data/metadata.yaml` file exists but only contains `sources` and `last_updated` keys; it lacks the required `version_tag`, `checksum`, and `retrieval_date` fields (or a proper schema defining them). The task’s specification for a provenance schema is therefore not met.
- **T009b** — declared artifact(s) missing/empty/invalid: code/download_kim.py, data/raw/kim/
- **T009c** — declared artifact(s) missing/empty/invalid: code/download_nist.py, data/raw/nist/
