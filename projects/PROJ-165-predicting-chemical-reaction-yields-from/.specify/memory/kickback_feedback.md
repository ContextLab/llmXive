# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/loaders.py
- `T019` (rejected 1x): No evidence of a `data/` directory with the required `raw/`, `processed/`, and `artifacts/` subfolders is shown, nor any code or log demonstrating checksum logging in a `state/` location. The implementer’s claim lacks the necessary artifacts to verify that the directory structure was created and that checksum logging was implemented.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/artifacts/leakage_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

