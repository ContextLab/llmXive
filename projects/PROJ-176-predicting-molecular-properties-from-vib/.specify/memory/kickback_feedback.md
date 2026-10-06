# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/`, `specs/`) is provided; the implementer’s response contains only the specification text and no actual project structure on disk. The task therefore remains unfinished.
- `T007` (rejected 1x): No evidence of a `data/` directory with the required `raw/`, `preprocessed/`, and `external/` subfolders is provided; the implementer did not supply any filesystem artifacts or screenshots confirming the structure exists. The task remains undone until those directories are created and verified.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T046` (rejected 1x): No test suite output, logs, or any evidence of the `tests/` directory being executed is provided; the claim lacks any artifact confirming that all acceptance scenarios were verified. The required proof of running the tests is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

