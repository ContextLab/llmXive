# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The `code/00_feasibility_check.py` script is present and contains validation functions, but the required schema file `contracts/dataset.schema.yaml` does not exist, and there is no `logs/schema_validation.log` produced or provided. Both required artifacts are missing, so the task is not fully satisfied.
- `T005a` (rejected 1x): No directory structure is shown in the provided evidence; there is no listing or screenshot confirming that `projects/PROJ-453-.../data/raw`, `data/processed`, `code`, `results/models`, `results/figures`, `tests`, and `contracts` actually exist. The implementer’s claim cannot be verified without these artifacts.
- `T007a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T007b` (rejected 1x): declared artifact(s) missing/empty/invalid: black.toml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T013` (rejected 1x): The test file `tests/contract/test_dataset_schema.py` is present, but it depends on `contracts/dataset.schema.yaml`, which is missing from the repository, causing the test to fail with `FileNotFoundError`. Add the required `contracts/dataset.schema.yaml` (with the expected `required_columns` definitions) so the test can actually validate the schema.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

