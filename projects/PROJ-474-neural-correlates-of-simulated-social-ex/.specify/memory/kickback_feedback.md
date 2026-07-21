# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): No code artifacts (e.g., Python modules, utility functions, or custom exception classes) are present to verify that base utility modules and custom exceptions have been implemented. The provided information only describes higher‑level user stories and contains no concrete implementation files, so the required deliverables are missing.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/qc.py
- `T036` (rejected 1x): declared artifact(s) missing/empty/invalid: src/stats.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

