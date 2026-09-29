# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-064-statistical-discrepancies-in-publicly-av/` directory tree (with `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`, `config/`) is provided; the claim cannot be verified without the actual filesystem artifacts.
- `T004` (rejected 1x): I looked for the required directory structure (`data/raw/`, `data/processed/`, and `state/`) under the specified project path, but no such folders or any evidence of their creation were provided. The implementer did not supply any artifacts confirming the directories exist, so the task is not satisfied.
- `T005` (rejected 1x): No code files, scripts, or documentation were presented showing a logging implementation in the `code/` directory, nor any evidence of JSON‑formatted logs with the required keys or a `--verify-reproducible` command‑line flag. The required artifact is missing, so the task is not satisfied.
- `T009a` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/verify_reproducible.yml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

