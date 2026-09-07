# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No evidence of the required `data/raw/`, `data/processed/`, or `results/` directories (or accompanying `.gitkeep` files) was provided; without these artifacts the task’s requirement is not satisfied.
- `T009` (rejected 1x): No `tests/unit/` or `tests/integration/` directories (or any test files) are present in the repository, so the required scaffolding does not exist. The implementer must add these folders and populate them with appropriate placeholder test modules.
- `T013b` (rejected 1x): No artifact (e.g., test script, log output, or verification report) was provided showing that the `[DATA_UNAVAILABLE]` log format and the 3‑attempt limit behavior were examined and that the log output matches the exact required format. Consequently the task’s requirement is not satisfied.
- `T017` (rejected 1x): The provided `code/data/download.py` is truncated and does not show any call that validates data against `contracts/dataset.schema.yaml` before GB construction, and the required schema file (`contracts/dataset.schema.yaml`) is missing from the repository. Without the schema and a demonstrated validation step, the task is not fulfilled.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/preprocessing_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

