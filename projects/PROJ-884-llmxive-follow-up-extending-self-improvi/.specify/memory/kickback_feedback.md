# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `data/` directory, nor the required `data/raw` and `data/processed` sub‑directories, is provided, and there is no proof that they have been created or are writable. The implementer’s claim lacks the actual filesystem artifacts needed to satisfy the task.
- `T001b` (rejected 1x): No evidence of a `code/` directory with the required subfolders (`dataset`, `symbolic`, `bes`, `analysis`, `utils`) is presented, nor any check that they are writable. The implementer’s claim cannot be confirmed without these artifacts.
- `T004` (rejected 1x): No evidence of the `data/raw` and `data/processed` directories being created, nor any code or logs that verify they exist and are writable, was provided. The required artifact (the directory structure and its verification) is missing.
- `T036` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/distribution_validation.json, data/processed/validation_gate.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

