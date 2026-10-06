# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/code/extract.py
- `T015b` (rejected 1x): No code artifact showing a modified `clone_batch` function with retry and skip logic (or corresponding tests/logs) was provided. Without the actual implementation or evidence that errors are logged and processing continues, the requirement cannot be confirmed. The next implementer must add and expose the updated `clone_batch` code (and optionally tests) demonstrating the retry‑on‑failure behavior.
- `T015c` (rejected 1x): No code artifact for `clone_batch` was provided, and there is no evidence that a check for empty git history was added or that exclusions are logged. The required implementation and logging are missing.
- `T016` (rejected 1x): No `logs/acquisition_stats.json` file or its contents were provided; thus there is no evidence that the required JSON logging of success rate, excluded repos count, and total valid clones was added. The implementer must create this file with the specified statistics.
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: src/code/extract.py, data/processed/comments.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

