# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The `code/00_feasibility_check.py` file exists but the required schema contract `contracts/dataset.schema.yaml` is missing, and there is no evidence of a `logs/schema_validation.log` being created. Without the schema file the validation cannot run, and the logging requirement is unmet.
- **T005a** — No directory structure is shown in the provided evidence; there is no listing or screenshot confirming that `projects/PROJ-453-.../data/raw`, `data/processed`, `code`, `results/models`, `results/figures`, `tests`, and `contracts` actually exist. The implementer’s claim cannot be verified without these artifacts.
- **T007a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T007b** — declared artifact(s) missing/empty/invalid: black.toml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T013** — The test implementation exists, but the required contract file `contracts/dataset.schema.yaml` is missing, so the test cannot actually validate the schema as specified. The missing schema file must be added for the task to be complete.
- **T015c** — The repository lacks the required `contracts/dataset.schema.yaml` file, so the validation logic cannot actually reference the schema. Moreover, the shown portion of `code/01_ingest.py` ends abruptly (truncated) and never demonstrates applying the loaded schema to the parsed DataFrames, indicating the validation step is not fully implemented. The task therefore remains unfinished.
- **T016b** — The `code/02_engineer.py` file exists but is truncated (e.g., `validate_and_save` is incomplete) and the required schema file `contracts/dataset.schema.yaml` is missing, so the script cannot actually validate raw data against the contract as the task demands. The missing schema and incomplete code must be provided/fixed.
- **T019** — The required output file `data/processed/participants_cleaned.csv` does not exist, and the provided `code/02_engineer.py` is truncated (ends mid‑function), indicating the implementation is unfinished and cannot produce the expected CSV. The task therefore remains incomplete.
- **T020** — No code, configuration file, or log output was presented showing that logging with level INFO, stdout destination, and the specified format has been added to the data ingestion and variable engineering steps. The required logging implementation is missing.
- **T023** — declared artifact(s) missing/empty/invalid: tests/unit/test_causal_language.py
