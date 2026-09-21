# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided evidence only describes user stories and testing criteria; there is no indication that the required directories (`src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`) actually exist or contain any files. The task’s core deliverable—a project folder structure—is missing.
- **T003** — No project files (e.g., `pyproject.toml`, `requirements.txt`, `setup.cfg`, or a virtual environment) are provided, nor any evidence that a Python 3.11 project with the listed dependencies has been created. The only artifact is a textual feature specification, which does not satisfy the task of initializing the project with the required packages. The implementer must supply the actual project scaffold and dependency declarations.
- **T004** — The provided evidence contains only a feature specification for data ingestion and modeling; there are no linting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) or any mention of setting up flake8/black. Consequently, the requirement to configure linting and formatting tools is not satisfied.
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/data_fetch.py
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/validators.py
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/logging_config.py
- **T010** — declared artifact(s) missing/empty/invalid: src/models/hea_sample.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/fetch_oqmd.py, data/source_metadata.yaml
- **T015** — declared artifact(s) missing/empty/invalid: src/data/fetch_mp.py
- **T016** — declared artifact(s) missing/empty/invalid: src/data/filter.py
- **T017** — declared artifact(s) missing/empty/invalid: src/data/normalize.py
- **T018** — declared artifact(s) missing/empty/invalid: src/features/descriptors.py
- **T019** — declared artifact(s) missing/empty/invalid: src/features/targets.py
- **T020** — declared artifact(s) missing/empty/invalid: src/pipeline/ingest.py, data/source_metadata.yaml
- **T021** — declared artifact(s) missing/empty/invalid: src/report/power_report.py
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/hea_features.csv, data/source_metadata.yaml
- **T025** — The required file `src/model/derive_groups.py` does not exist, so no code implementing the “Alloy System” grouping key is present. The task cannot be considered fulfilled until this module is created with the appropriate logic.
