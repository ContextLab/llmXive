# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T015a` (rejected 1x): The required output files `data/processed/conformer_params.json`, `data/processed/failure_report.csv`, `data/processed/conformers.parquet` (and the state file `conformer_state.json`) are absent from the repository, so the conformer generation and logging steps have not been realized. The implementation in `code/data/preprocess.py` does not contain code that creates these artifacts.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

