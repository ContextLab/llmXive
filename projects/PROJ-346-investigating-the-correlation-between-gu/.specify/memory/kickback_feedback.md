# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T017a` (rejected 1x): The repository contains a fully‑implemented `code/07_gap_report.py`, but the required output file `data/processed/data_gap_report.json` is absent, so the script has not been run to produce the mandated artifact. The missing JSON report means the task’s core deliverable is not satisfied.
- `T017b` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/data_gap_report.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

