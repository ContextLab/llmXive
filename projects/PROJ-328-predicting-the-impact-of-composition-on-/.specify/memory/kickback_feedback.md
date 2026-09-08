# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or `ls -R` output is provided, so the required `data/`, `code/`, and `tests/` subdirectories (with their specified subfolders) cannot be confirmed to exist. The implementer must supply the actual filesystem layout or command output showing the created directories.
- `T003b` (rejected 1x): No artifact showing a `flake8` run on a sample file is present; there is no output, log, or report confirming that the linting configuration was verified, nor any sample file referenced. The required evidence to prove the task is therefore missing.
- `T009c` (rejected 1x): The `data/config/sources.yaml` file exists but contains placeholder URLs with a comment that they will be replaced after verification, so the verified URLs from `research_verified.md` have not actually been populated. This does not meet the task’s requirement to populate the file with the specific, verified URLs and API endpoints.
- `T012a` (rejected 1x): The repository lacks a `research_verified.md` file, so the required pre‑check cannot be performed, and the provided `aggregator.py` does not contain any logic that verifies this file or raises `ConfigError` when it is absent. Moreover, `data/config/sources.yaml` only contains placeholder URLs and a comment that they will be populated later, meaning the sources are not yet verified as the task demands. Consequently the implementation does not meet the critical pre‑check or the “verified sources” requirement.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/validation_report.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

