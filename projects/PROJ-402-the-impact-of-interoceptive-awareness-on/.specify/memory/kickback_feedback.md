# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was provided that the required top‑level directories (`code/`, `tests/`, `data/`, `results/`) actually exist in the repository; the response contains only the task description and user scenarios, with no file or directory listings. The implementer must create and show these folders (and optionally populate them) to satisfy the task.
- `T002a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T004` (rejected 1x): The repository lacks the required `contracts/dataset.schema.yaml` file, and the provided `schema_validator.py` does not show logic that automatically loads that specific schema or implements the prescribed exit‑code error contract (the snippet is truncated and contains no such handling). Consequently the validation module is not fully implemented as required.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

