# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): No `quickstart.md` file was presented in the evidence, nor any excerpt or link confirming its existence in `specs/001-compression-impact-gw-reconstruction/`. Without the required document, the task’s deliverable is missing.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/main.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

