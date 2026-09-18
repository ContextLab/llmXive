# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listings were provided; the required `projects/PROJ-181-predicting-species-distribution-shifts-u/` folder with all specified subdirectories is absent from the evidence. The implementer must create and show the full directory structure.
- `T003` (rejected 1x): I could find no linting or formatting configuration files (e.g., .flake8, pyproject.toml with black settings, or a pre‑commit hook) in the provided repository snapshot, nor any documentation indicating that flake8 and black have been set up. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: logs/preprocess_counts.yaml
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

