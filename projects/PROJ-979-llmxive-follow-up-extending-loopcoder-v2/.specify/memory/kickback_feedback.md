# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/filtered_splits.json, data/processed/convergence_results_core.csv
- `T037` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/correlation_results_final.json
- `T020` (rejected 1x): No `router_accuracy_test.json` file or any comparable output was presented; the response contains only the task description and context, without the required paired t‑test results. The essential artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

