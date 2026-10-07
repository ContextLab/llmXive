# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T027` (rejected 1x): No code, configuration, or log files were provided that demonstrate the addition of logging for null‑hypothesis rejection flags (p < 0.01). The implementer’s claim lacks any concrete artifact (e.g., modified source files, unit tests, or example log output) to verify that the required logging was actually implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

