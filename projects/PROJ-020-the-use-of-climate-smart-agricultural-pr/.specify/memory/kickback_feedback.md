# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): `code/main.py` exists and checks for `specs/001-csa-food-security/data-model.md`, but it does **not** perform a pre‑run existence check for `data/processed/merged_sample.parquet` as required, and the referenced `merged_sample.parquet` file is absent. The script therefore fails the enforcement clause.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

