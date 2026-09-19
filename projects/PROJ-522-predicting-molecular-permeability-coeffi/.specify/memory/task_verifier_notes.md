# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No evidence of any `__init__.py` files in the `code/` or `tests/` subdirectories is provided; without seeing those files we cannot confirm they exist and are non‑empty. The required package initializer files are missing from the artifact set.
- **T001c** — No `.gitkeep` files are present in any `data/` subdirectory; the repository lacks the required placeholder files to preserve empty directories in version control. The task therefore remains undone.
- **T012a** — The repository contains an `ingestion.py` script, but it never writes the required Parquet files and the helper functions it calls (`fetch_nist_data`, etc.) are not shown to produce or save the data. The three expected output files (`data/raw/nist.parquet`, `data/raw/pubchem.parquet`, `data/raw/mtr.parquet`) are absent. The task therefore remains unfinished.
- **T012c** — The `deduplicate_smiles` function exists but its output columns differ from the required schema (`source_ids` vs. `source_id`) and the script never writes the deduplicated DataFrame to `data/processed/deduplicated.csv`. Moreover, the expected CSV file is missing from the repository. The task is therefore not fully satisfied.
- **T012d** — The required output files `data/processed/exclusion_log.json` and `data/processed/validation_report.json` are absent, and the provided `code/ingestion.py` (as shown) does not contain logic to enforce the ≥500 unique‑compound check, raise an error if the count is lower, or write the specified JSON reports. The implementation therefore does not meet the task’s functional requirements.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_log.json
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/exclusion_stats.json
- **T022b** — declared artifact(s) missing/empty/invalid: data/processed/predictions.csv
