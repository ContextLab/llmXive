# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw`, `data/processed`, `data/assets`) is provided; the artifact list is empty, so we cannot confirm that the directories were actually created.
- **T001b** — No evidence was provided showing that the required directories (`code`, `artifacts`, `tests`) actually exist or contain any files; without such artifacts the task requirement is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `ruff.toml`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure flake8/ruff and Black has not been satisfied. The implementer must add the appropriate configuration files and any integration steps (e.g., pre‑commit hooks) to complete the task.
- **T009c** — The required artifact `data/assets/reference_substructures.csv` does not exist, so no data ingestion or schema validation could have been performed. The implementer must create the CSV file with the verified data and ensure it conforms to the expected schema.
- **T009d** — The required artifact `data/raw/kinetic_dataset_raw.csv` does not exist, so the dataset was not downloaded as specified. The task remains undone.
- **T009e** — The required file `data/raw/kinetic_dataset_raw.csv` does not exist, so no SHA‑256 checksum can be computed or compared to the manifest. The task’s core requirement is therefore unmet.
- **T009f** — The required artifact `data/assets/kinetic_dataset.csv` does not exist, so no data ingestion or schema validation has been performed. The implementer must create the CSV file with the verified data and ensure it conforms to the expected schema.
- **T030** — declared artifact(s) missing/empty/invalid: data/assets/reference_substructures.csv
- **T033** — declared artifact(s) missing/empty/invalid: data/assets/kinetic_dataset.csv
- **T016** — No serialized graph files (e.g., `.parquet` or `.pkl`) are present in `data/processed/`, nor are any derivation logs provided. The required output artifacts are missing, so the task is not satisfied.
