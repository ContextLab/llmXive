# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No evidence of a `contracts/` directory or any files within it is presented; the implementer provided only the project specification, not the required directory structure or its contents. The task’s artifact is missing.
- **T010a** — The repository contains a `code/ingestion.py` file, but it does not implement the required fallback logic (exception handling and synthetic data generation) within this module, and the expected output files `data/raw/raw_dataset.csv` and `data/raw/metadata.json` are missing. Consequently the task’s critical execution flow and required artifacts are not satisfied.
- **T010b** — The repository contains `code/ingestion.py`, but the required output file `data/raw/raw_dataset.csv` is missing, so the ingestion step was never completed (or its result was not saved). Consequently the schema validation cannot be confirmed. The next implementer must run the ingestion script and ensure the CSV is created with the required columns.
- **T012a** — declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/processed/cleaned_age_filtered.csv, data/processed/exclusion_counts.json
- **T012b** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_age_filtered.csv, data/processed/cleaned_score_filtered.csv, data/processed/exclusion_counts.json
- **T012d** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_score_filtered.csv, data/processed/mmse_flag.json
- **T012e** — declared artifact(s) missing/empty/invalid: data/processed/mmse_flag.json
- **T012c** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_counts.json, data/processed/exclusion_log.json
