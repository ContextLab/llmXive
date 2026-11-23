# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015c` (rejected 1x): The required `data/processed/sample_info.json` file does not exist, so the explicit sample size declaration is not present. Consequently the verification command (`python -c "import json; d=json.load(open('data/processed/sample_info.json')); assert 'subjects_used' in d"`) would fail. The implementation must create this JSON file with the specified schema during dataset download.
- `T019a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

