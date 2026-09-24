# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory tree or file listings were provided; the required folders (`code/`, `tests/`, `data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`) are not shown to exist or contain any content. The implementer’s claim lacks concrete evidence of the requested project structure.
- **T001b** — No evidence of `__init__.py` files in any `code/` subdirectory or in the `tests/` directory is provided; the artifact list is empty, so the requirement to create those files is not satisfied. The implementer must add the missing `__init__.py` files in every relevant subfolder.
- **T001c** — No `.gitkeep` files were presented for either `data/raw/` or `data/processed/`; the implementer provided no artifact evidence confirming the files exist. The required files must be added to those directories.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No configuration files, scripts, or documentation for managing environment variables (e.g., `.env` templates, `dotenv` setup, path‑resolution utilities, or README instructions) were provided. The evidence only contains a feature specification unrelated to environment variable management, so the required artifact is missing.
- **T014c** — The repository contains `code/data/preprocessing.py`, but the file is truncated and does not show any logic that writes the combined, preprocessed dataset to `data/processed/preprocessed_data.parquet`. Moreover, the expected parquet file is absent from the filesystem. Consequently, the required output artifact is missing and the implementation is not demonstrably complete.
