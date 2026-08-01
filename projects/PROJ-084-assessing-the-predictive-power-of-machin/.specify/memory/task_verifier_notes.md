# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was provided that the required directories (`code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`) actually exist on disk; the response contains only the task description and no file‑system listing or screenshots showing those folders. The implementer must create the directories (and optionally include a brief directory tree) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or a `pre-commit` config) were provided or referenced, so there is no evidence that ruff and black have been set up in the `code/` directory. The required artifacts are missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T019** — The provided `download.py` contains only placeholder logic, raises a `FileNotFoundError` instead of performing a real download, and leaves the expected MD5 checksum empty. Moreover, the required output file `data/raw/uspto_raw.parquet` is missing. The implementation does not fulfill the download, checksum verification, or Constitution Principle II gate check as specified.
- **T014** — The provided `sanitize.py` defines helper functions but never loads `data/raw/uspto_raw.parquet` nor applies `remove_salts` to the data, and the required parquet file is absent from the repository. Consequently the script does not fulfill the stated requirement of loading, sanitizing, and standardizing the USPTO reactions.
- **T017** — declared artifact(s) missing/empty/invalid: code/preprocessing/ingest.py, data/processed/cleaned_reactions.parquet
- **T018** — declared artifact(s) missing/empty/invalid: code/preprocessing/ingest.py, data/results/data_quality_report.json
- **T010** — The provided `scaffold.py` only defines helper functions and a placeholder `main()` that does nothing; it never reads `cleaned_reactions.parquet` nor writes `scaffold_groups.parquet`. Moreover, both the required input parquet file and the expected output parquet file are absent from the repository. The task’s core requirement—to generate scaffold grouping keys from the sanitized reactions and produce the output file—is therefore not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: tests/integration/test_training_pipeline.py
