# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file paths were provided showing that the required folders (`projects/PROJ-328-predicting-the-impact-of-composition-on-/data/`, `code/`, `tests/`, `models/`) actually exist; without concrete evidence the claim cannot be verified. The implementer must supply a directory tree or screenshots confirming the creation of these directories.
- **T003** — No linting or formatting configuration files (e.g., `setup.cfg`, `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) are present in the provided evidence, nor any CI steps showing they run after T001. Without these artifacts the requirement to configure flake8/black cannot be confirmed.
- **T005** — No files or code were found under `code/ingestion/`, and there is no placeholder implementation for a literature aggregator. The required ingestion scaffolding artifact is missing, so the task is not satisfied.
- **T006** — No evidence of a `code/features/` directory (or any files within it) was provided; the implementer did not supply the required directory structure or any placeholder indicating it has been created. Without the actual folder and its contents, the task requirement is not satisfied.
- **T007** — No files or code snippets for `code/models/SolderComposition.py` or `code/models/CompositionalDescriptor.py` (or equivalent) were provided, so we cannot verify that the required data model classes exist, are non‑empty, and contain the appropriate fields. The implementer must add the two model definitions in the `code/models/` directory.
- **T008** — The provided information contains only the feature specification for the solder hardness prediction pipeline; there is no evidence of any files or code under `code/utils/` that implement error handling or logging infrastructure. Consequently, the required artifact is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/raw/solder_hardness_raw.csv, data/checksums.txt
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/solder_hardness_validated.csv
- **T025** — declared artifact(s) missing/empty/invalid: code/evaluation/cv.py
