# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure is shown or listed in the provided evidence; the implementer did not supply any proof that the required folders (`code/`, `data/raw/`, `data/processed/`, `data/models/`, `tests/unit/`, `tests/integration/`, `specs/`) actually exist. The task remains unfinished until those directories are created and demonstrated.
- **T001b** — No `__init__.py` files were presented in the evidence; the implementer provided no directory listings or file contents showing empty `__init__.py` files in the new project directories. Without these artifacts, the requirement to create empty package initializers is not satisfied.
- **T004** — No linting or formatting configuration files (e.g., `pyproject.toml` entries, `.ruff.toml`, `black.toml`, or a pre‑commit hook) were provided, nor any evidence that ruff and black have been set up in the repository. The required artifacts are missing.
- **T006** — The implementer provided no evidence of a `tests/` directory (with unit and integration subfolders) in the repository; no files or structure were shown. Consequently the required artifact is missing, so the task is not satisfied.
- **T013** — The repository contains a partially shown `code/data_ingestion.py` but the implementation of `process_and_save_heas_train` is truncated and does not demonstrate that it writes a CSV file. Moreover, the required output file `data/processed/heas_train.csv` is absent from the project. The task’s core deliverable—filtering for 5‑element+ systems and exporting the result—is therefore not verified.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/holdout_known.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/true_novel.csv
