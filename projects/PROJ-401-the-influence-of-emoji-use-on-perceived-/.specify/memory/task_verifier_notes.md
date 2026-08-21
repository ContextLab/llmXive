# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `src/` directory or its subfolders (`src/data`, `src/analysis`, `src/utils`, `src/reports`) is provided; the required directory structure is missing.
- **T001b** — The implementer provided no evidence of a `tests/` directory or its subfolders (`unit`, `integration`, `contract`). Without a directory listing or files showing that this structure exists, the task requirement is not satisfied. The missing artifact is the required `tests/` directory hierarchy.
- **T001c** — No evidence of the required `data/` directory hierarchy (`data/raw`, `data/processed`, `state`) is present; the implementer provided no files, listings, or screenshots confirming the directories exist. The task cannot be considered done without concrete proof of the directory structure.
- **T003** — The evidence only contains user‑story specifications for data ingestion and analysis; there are no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or related scripts). Consequently, the requirement to configure flake8/black is not met. The missing artifacts are the actual linting/formatting configuration files and any integration steps.
- **T007** — No files were found in `src/data/contracts/` defining the required `Message` and `AnalysisResult` schemas; the implementer provided no code, schema definitions, or any artifact confirming these contracts exist. The task therefore remains unfinished.
- **T008** — No evidence was provided that the repository actually contains the required directories `data/raw/`, `data/processed/`, and `state/`; the implementer’s claim is unsubstantiated. The task cannot be considered complete without tangible proof of the directory structure.
- **T021** — declared artifact(s) missing/empty/invalid: src/analysis/power.py, state/power_analysis.yaml
- **T013** — No code, script, or documentation for a pipeline step that joins raw text with extracted features is present, nor any evidence that it handles zero‑length texts or encoding errors. Additionally, there is no verification that prerequisite T012’s data is available. The required artifact is missing entirely.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T015** — No code, configuration, or log files were supplied that demonstrate logging of extraction errors or skipped records; the claim cannot be verified without concrete artifacts. The required implementation of logging is missing.
- **T020** — The required artifact `tests/unit/test_power.py` does not exist on disk, so no unit test for the verification logic is present. The task’s core deliverable is missing.
- **T022** — declared artifact(s) missing/empty/invalid: state/power_analysis.yaml, state/verification.yaml
