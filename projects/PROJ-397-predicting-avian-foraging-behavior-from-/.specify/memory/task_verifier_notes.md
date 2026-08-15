# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/` directory or a `.gitkeep` file was provided; the artifact is missing entirely. The implementer must create the directory (using `mkdir -p`) and add a `.gitkeep` file inside (e.g., via `touch .gitkeep`).
- **T001b** — No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/models/` directory or a `.gitkeep` file inside is provided; the artifact is missing from the supplied information.
- **T001c** — No evidence of the `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/` directory or a `.gitkeep` file inside it was provided; the claim cannot be verified. The required directory and placeholder file must be created and shown.
- **T001d** — No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/` directory or a `.gitkeep` file was provided; the artifact is missing entirely. The implementer must create the directory (using `mkdir -p`) and add a `.gitkeep` file (e.g., via `touch .gitkeep`).
- **T001e** — No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/utils/` directory or a `.gitkeep` file inside is present; the artifact list is empty, so the initialization task has not been demonstrated.
- **T001f** — No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/` directory or a `.gitkeep` file was provided; the artifact is missing.
- **T002** — No evidence was provided that the files `README.md` and `run_pipeline.sh` actually exist in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`; the response contains only the task description without any file listings or contents. The required placeholder files are therefore missing.
- **T003** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T004** — No `utils/config.py` file or its contents were provided; without the actual module defining paths, random seeds, and constants, we cannot confirm that the required artifact exists or meets the specification. The implementer must add the file with the appropriate definitions.
- **T005** — declared artifact(s) missing/empty/invalid: data/metadata.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: tests/test_metrics.py
- **T035** — No `utils/validate_resources.py` file or any code that measures and logs total runtime and peak memory usage is provided. Consequently, the required artifact is missing, so the task’s requirement is not satisfied.
- **T011** — declared artifact(s) missing/empty/invalid: data/download_ebd.py, data/raw/ebd_train.csv, data/metadata.yaml
- **T012** — declared artifact(s) missing/empty/invalid: data/download_nlcd.py, data/raw/nlcd_2019.zip, data/metadata.yaml
- **T008a** — declared artifact(s) missing/empty/invalid: data/download_guild_source.py, data/metadata.yaml, data/raw/guild_source.csv
- **T008b** — declared artifact(s) missing/empty/invalid: data/generate_guild_mapping.py, data/raw/guild_source.csv, data/processed/guild_mapping.csv
- **T013** — declared artifact(s) missing/empty/invalid: data/merge_and_buffer.py, data/raw/ebd_train.csv, data/processed/top_25_species_ids.json, data/raw/nlcd_2019.zip, data/raw/nlcd_2019_fallback.zip, data/processed/guild_mapping.csv, data/processed/merged_observations.csv
- **T015** — The file `data/merge_and_buffer.py` does not exist, so the required `validate_schema()` function cannot be present. The test suite `tests/test_data_contract.py` defines a different helper (`validate_schema_compliance`) and lacks a `test_validate_schema` method; moreover the file is truncated and does not actually invoke the new function. Both the implementation and the specific unit test are missing.
- **T010** — The provided `test_data_contract.py` does not actually load or validate the real `merged_observations.csv` against a schema, and the required `contracts/dataset.schema.yaml` file is missing entirely, so the test cannot perform the intended schema compliance check. The task’s requirement is therefore not satisfied.
