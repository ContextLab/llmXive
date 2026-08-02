# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure (`code/`, `tests/`, `data/`, `results/`) was presented or described, and no file listings were provided to confirm their existence or contents. Without concrete evidence of these folders, the task requirement is not satisfied.
- `T004` (rejected 1x): The only artifact present is a note that `schema.yaml` is missing; no dataset schema, download script, checksum verification, or any of the required audit/preprocessing/regression outputs exist. Consequently the error‑handling contract cannot be validated and the task requirements are unmet.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: code/04_update_state.py
- `T008` (rejected 1x): No pytest configuration file (e.g., `pytest.ini` or `conftest.py`) with a fixed random seed, nor any GitHub Actions step that records `GITHUB_JOB_DURATION`, is present. Additionally, the data download scripts referenced in T004 and T011 do not show checksum verification to guarantee deterministic downloads. These required artifacts are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

