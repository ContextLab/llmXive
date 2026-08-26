# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): No coherence matrix files, validation logs, or test scripts were provided to demonstrate that `connectivity.py` actually produced coherence matrices for the 10‑20 electrode system, nor any evidence that the output was checked for correctness. The required artifact is missing.
- `T018c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/sensitivity_summary.json
- `T027b` (rejected 1x): No `power_analysis.json` file or code implementing the described halt‑check logic is present; without these artifacts we cannot confirm that the warning is logged for missing cognitive data or that the process exits with code 1 for other under‑power reasons. The required implementation and data are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

