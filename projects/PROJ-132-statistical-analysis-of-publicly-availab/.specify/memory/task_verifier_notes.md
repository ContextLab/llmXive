# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided showing that the required directories (`src/data`, `src/models`, `src/analysis`, `data/raw`, `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`) actually exist on disk. Without a listing, screenshot, or other artifact confirming the `mkdir -p …` command was run, we cannot confirm the task was completed.
- **T003b** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T008** — declared artifact(s) missing/empty/invalid: src/models/utils.py
- **T010** — No logging configuration files, code snippets, or documentation were provided that set up a logging infrastructure to capture “insufficient data” events or model convergence failures. Without concrete artifacts (e.g., a logging module, config files, or example log entries), the requirement cannot be verified as met. The implementer must supply the actual logging setup and evidence that it records the specified events.
- **T011** — No configuration artifact (e.g., a YAML/JSON/INI file, environment variable definitions, or code that loads and applies random seeds and sampling parameters) was provided. The task required concrete environment‑configuration management for reproducible random seeding and sampling, but the evidence contains only high‑level project specifications and no actual config files or implementation. The implementer must add the appropriate configuration files and loading logic.
- **T014** — The required file `src/data/preprocess.py` does not exist, so no code can call the T005 download functions or perform file‑presence and checksum verification. The artifact is missing, making the task unfulfilled.
- **T015** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T017** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T018** — No code, script, configuration file, or data artifact was provided that implements the required logic to flag grid cells with insufficient observation density and to exclude them from downstream modeling. The claim lacks any tangible implementation or evidence that the feature depends on the completed T007 file‑creation step. The missing artifact must be supplied (e.g., a Python module or pipeline step with unit tests demonstrating the marking behavior).
- **T019** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T019b** — declared artifact(s) missing/empty/invalid: src/data/preprocess.py
- **T025** — declared artifact(s) missing/empty/invalid: src/models/utils.py
