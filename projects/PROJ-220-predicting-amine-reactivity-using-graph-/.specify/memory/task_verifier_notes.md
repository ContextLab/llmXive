# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`src/`, `tests/`, `data/`, `specs/`) is shown or referenced in the provided evidence; the implementer did not supply any files or listings to confirm that these folders exist and contain appropriate starter content. The task’s core requirement—creating the project skeleton—is therefore unverified.
- **T003** — No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or similar) or scripts setting up ruff and black are present in the provided evidence. Without these artifacts, the task of configuring linting and formatting tools is not satisfied.
- **T011a** — declared artifact(s) missing/empty/invalid: src/utils/memory_monitor.py
- **T016** — declared artifact(s) missing/empty/invalid: src/data/preprocessing.py
- **T018a** — The `src/data/ingestion.py` file contains only placeholder functions and generic logging setup; it does not record normalization exclusions (missing Ea or temperature) to any file. Moreover, the required `data/raw/audit_log.json` does not exist. Both the logging behavior and the audit log artifact are missing.
- **T018b** — declared artifact(s) missing/empty/invalid: src/data/preprocessing.py, data/raw/audit_log.json
- **T019** — No dataset file, verification script, or log output was supplied; the claim provides only the specification text but no actual artifact showing that a dataset with complete SMILES, normalized kinetics, and calculated pKa fields exists. The required evidence to confirm the dataset’s validity is missing.
- **T022** — declared artifact(s) missing/empty/invalid: src/models/baseline.py
