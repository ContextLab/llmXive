# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): The `Subject` model with the required attributes and custom validation is present, but the referenced `contracts/subject.schema.yaml` file is missing, so the validation cannot be verified against the actual schema. The task’s mandatory requirement to ensure instances match that schema is therefore not satisfied. Provide the missing schema file (or load it in the validation logic) to complete the task.
- `T013` (rejected 1x): The provided `tests/integration/test_ingestion.py` defines `test_full_ingestion`, but it checks a temporary file (`tmp_path / "subjects_cleaned.csv"`) instead of asserting the existence of `'data/processed/subjects_cleaned.csv'` as required, and therefore does not contain the exact assertions specified in the task. Moreover, the expected output file `data/processed/subjects_cleaned.csv` is missing from the repository. The task’s requirement is not genuinely satisfied.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/subjects_cleaned.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

