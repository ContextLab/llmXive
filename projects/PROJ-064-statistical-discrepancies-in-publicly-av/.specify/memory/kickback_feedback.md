# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listing was provided showing that `projects/PROJ-064-statistical-discrepancies-in-publicly-av/` with the required subfolders (`code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`, `config/`) actually exists; without concrete evidence the claim cannot be verified.
- `T004` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `state/`) within `projects/PROJ-064-statistical-discrepancies-in-publicly-av/` was provided; the claim cannot be confirmed without actual filesystem artifacts.
- `T005` (rejected 1x): No files or code implementing a base logging system or an error‑handling framework were found in the `code/` directory; the only artifacts described relate to election‑data ingestion and statistical testing, which do not satisfy the logging‑infrastructure requirement. The task therefore remains unfinished.
- `T009a` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/verify_reproducible.yml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

