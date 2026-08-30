# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/download.py
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_ebsd.parquet
- `T019` (rejected 1x): No code, script, test output, or any other artifact was presented that implements the mass‑balance check (sum of major texture components plus “random” equals 1.0 ± 0.01). Without a concrete implementation or verification results, the requirement is not satisfied. The next implementer must provide the actual function/module and evidence (e.g., unit test logs or example output) showing the mass‑balance condition holds.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

