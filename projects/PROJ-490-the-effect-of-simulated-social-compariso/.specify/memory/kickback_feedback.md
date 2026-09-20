# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T002b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T002c` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011a` (rejected 1x): No code, configuration, or log files were provided that demonstrate the implementation of the fallback trigger logic described in T011a. The required artifact (e.g., a script or module that checks for real data presence, IRB/consent status, and required variables and then calls T010 to generate synthetic data) is missing, so the task cannot be confirmed as completed.
- `T011c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/synthetic_seed.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

