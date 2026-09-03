# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/` directory or a `.gitkeep` file was provided; the artifact is missing entirely. The implementer must create the directory (using `mkdir -p`) and add a `.gitkeep` file inside (e.g., via `touch .gitkeep`).
- `T001b` (rejected 1x): No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/models/` directory or a `.gitkeep` file inside is provided; the artifact is missing from the supplied information.
- `T001c` (rejected 1x): No evidence of the `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/` directory or a `.gitkeep` file inside it was provided; the claim cannot be verified. The required directory and placeholder file must be created and shown.
- `T001d` (rejected 1x): No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/` directory or a `.gitkeep` file was provided; the artifact is missing entirely. The implementer must create the directory (using `mkdir -p`) and add a `.gitkeep` file (e.g., via `touch .gitkeep`).
- `T001e` (rejected 1x): No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/utils/` directory or a `.gitkeep` file inside is present; the artifact list is empty, so the initialization task has not been demonstrated.
- `T001f` (rejected 1x): No evidence of the required `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/` directory or a `.gitkeep` file was provided; the artifact is missing.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: requirements.txt
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/test_metrics.py
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: data/download_ebd.py, data/raw/ebd_train.csv, data/metadata.yaml
- `T002` (rejected 1x): No evidence was provided that the files `README.md` and `run_pipeline.sh` actually exist in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`; the response contains only the task description without any file listings or contents. The required placeholder files are therefore missing.
- `T004` (rejected 1x): No `utils/config.py` file or its contents were provided; without the actual module defining paths, random seeds, and constants, we cannot confirm that the required artifact exists or meets the specification. The implementer must add the file with the appropriate definitions.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/merge_and_buffer.py, data/raw/ebd_train.csv, data/processed/top_25_species_ids.json, data/raw/nlcd_2019.zip, data/raw/nlcd_2019_fallback.zip, data/processed/guild_mapping.csv, data/processed/merged_observations.csv
- `T015` (rejected 1x): The file `data/merge_and_buffer.py` does not exist, so the required `validate_schema()` function cannot be present. The test suite `tests/test_data_contract.py` defines a different helper (`validate_schema_compliance`) and lacks a `test_validate_schema` method; moreover the file is truncated and does not actually invoke the new function. Both the implementation and the specific unit test are missing.
- `T010` (rejected 1x): The provided `test_data_contract.py` is truncated (ends with an incomplete method definition) and never loads or asserts anything about `merged_observations.csv`. Moreover, the required `contracts/dataset.schema.yaml` file is missing entirely, so the test cannot even load the schema. Both the test implementation and the schema artifact are absent, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

