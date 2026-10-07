# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or file tree was provided showing the required folders (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `contracts/`, `logs/`). Without concrete evidence that these directories exist and are non‑empty, the claim that the project structure is created cannot be verified. The implementer must supply a file system snapshot (e.g., `tree` output or a zip archive) demonstrating the presence of all required directories.
- **T001b** — No `.gitignore` or `README.md` files were presented in the evidence, nor any content showing they contain a project title and description. The required stub files are missing, so the task is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, nor any documentation showing that ruff/flake8 and black have been set up for the project. Consequently, the requirement to configure these tools is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The `src/data/validate.py` file is truncated (ends abruptly in `sys.exit(E_SCH`) and does not contain a complete validation routine that checks the data against a schema and exits with `E_SCHEMA_MISSING` on failure. Moreover, the required `contracts/dataset.schema.yaml` (or `schema.yaml`) is absent from the repository, so the validator cannot even load the schema. Both the implementation and the necessary schema file are missing.
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/plots.py
- **T016b** — declared artifact(s) missing/empty/invalid: src/data/download_meddra.py, data/meddra_soc_mapping.csv
- **T015** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T016** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T018** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T022** — The repository contains a `src/analysis/disproportionality.py` file, but it only defines helper functions and does not include code that reads the required `data/processed/cleaned_vaers_full_non_covid.parquet` file, iterates over all SOCs, or writes out the 2×2 tables. Moreover, the specified input parquet file is absent from the project. Both the missing data file and the incomplete script prevent the task from being fulfilled.
- **T025b** — No `output/signals.csv` file or its contents were presented, so we cannot confirm the required columns, values, or the `background_rate_status` setting. The implementer must supply the actual CSV file with the specified schema and ensure all rows have `background_rate_status` set to “UNKNOWN”.
- **T027** — declared artifact(s) missing/empty/invalid: src/analysis/sensitivity.py
