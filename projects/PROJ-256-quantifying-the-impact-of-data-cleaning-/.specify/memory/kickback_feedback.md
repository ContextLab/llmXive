# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The required artifact `data/processed/baseline_metrics.json` does not exist, so no baseline metrics have been recorded (let alone with ≥3‑decimal precision for ≥10 datasets). The task’s core deliverable is missing.
- `T023` (rejected 1x): The required output file `data/processed/cleaned_metrics.json` does not exist, so the task’s deliverable is missing. Without this JSON containing the re‑run t‑test and regression metrics, the implementation does not satisfy the stated requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

