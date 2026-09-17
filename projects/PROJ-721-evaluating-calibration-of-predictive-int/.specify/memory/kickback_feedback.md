# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013a` (rejected 1x): The repository lacks `data/processed/sampling_report.json` entirely, and the shown portion of `code/download.py` contains only download‑related utilities with no implementation of stratified sampling, sample index generation, or representativeness metric calculation. Both required artifacts are missing, so the task is not satisfied.
- `T013b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/sampling_report.json, data/processed/sample_indices_1000.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

