# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The provided `tests/contract/test_schemas.py` contains tests for a model results schema, not a `test_merged_dataset_schema_validates_columns` function, and it references `contracts/model_results.schema.yaml` instead of the required `contracts/dataset.schema.yaml`. Moreover, the `contracts/dataset.schema.yaml` file is missing entirely. The task’s required test and schema are absent.
- `T014` (rejected 1x): No code, script, or configuration file was provided that actually inspects the PlantPheno dataset for `phosphorus` and `nitrogen` columns, raises the required `ValueError` when they are absent, or sets a global `p_n_available=True` flag when present. Without such artifacts, the task’s acceptance criteria cannot be verified.
- `T015b` (rejected 1x): No evidence of an `artifacts/deviations.json` file was provided, nor any content showing that the required JSON object for FR‑002 was appended. Without the file or its contents, the task’s requirement cannot be confirmed as satisfied.
- `T015c` (rejected 1x): No `artifacts/deviations.json` file or its contents were presented, so we cannot confirm that the required JSON object was appended. The implementer must provide the actual file with the specified entry.
- `T015` (rejected 1x): The provided `code/data_ingestion.py` only contains helper functions for detecting the data source column, filtering by that column, and (partially) filtering rows with missing nutrients; it does not implement the required species‑count filtering (n < 20) nor does it generate the `artifacts/reports/species_counts.json` file (the file is missing). Additionally, the file ends abruptly (`retu…`) indicating the implementation is incomplete. The task’s core requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

