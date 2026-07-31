# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required top‑level directories (`code/`, `data/`, `tests/`, `docs/`) is provided; the implementer did not supply a directory listing or any files showing that these folders exist. The task remains undone until those directories are created and visible.
- **T001b** — No `.gitignore` file is present in the provided evidence; the implementer did not supply the required artifact listing Python, data, and IDE patterns. The task remains undone.
- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml with black settings, pre‑commit hooks) are present, nor any documentation showing that flake8/black have been set up and integrated into the project. The provided material only describes a scientific feature and does not include the required linting setup.
- **T004** — No directory structure or `.gitkeep` files were presented as evidence; without visible `data/raw/.gitkeep`, `data/processed/.gitkeep`, and `data/interim/.gitkeep` we cannot confirm the required subdirectories were created.
- **T011** — declared artifact(s) missing/empty/invalid: code/data/download.py
- **T013** — No code, script, or log files were presented that demonstrate added error handling for missing reduction levels or corrupted EBSD files, nor any evidence that warnings are logged and processing continues as required by US‑1 Scenario 3. The implementer provided no tangible artifact to verify the requested functionality.
- **T014** — No code, script, or documentation implementing the required exclusion logic (flagging samples with >50 % filtered points as “low reliability” and removing them from the final training set) is present in the provided artifacts. The implementer’s claim cannot be verified because the necessary artifact is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_ebsd.parquet
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
- **T023** — declared artifact(s) missing/empty/invalid: tests/contract/test_model_output.py
