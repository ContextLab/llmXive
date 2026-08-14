# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T050a` (rejected 1x): The implementer supplied only a feature specification for bird‑migration data processing; no schema definition, file, or code for a “Deviation Whitelist Schema” was presented. Consequently the required artifact is missing, so the task is not satisfied.
- `T050b` (rejected 1x): No preprocessing, modeling, or verification scripts, datasets, or result files were provided; the claim lacks any tangible artifact to confirm that the plan and spec verification steps were implemented. The required code and output artifacts are missing.
- `T003b` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

