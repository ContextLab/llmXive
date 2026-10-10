# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The repository contains `src/utils/logger.py` and `src/utils/timeout_wrapper.py`, but no evidence of their contents or of unit‑test execution showing that the timeout wrapper enforces a 6 h limit, writes to `logs/timeout.log`, exits with code 143, or that the logger emits correctly‑formatted JSON lines. Provide the actual source code and test results to confirm the required behavior.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

