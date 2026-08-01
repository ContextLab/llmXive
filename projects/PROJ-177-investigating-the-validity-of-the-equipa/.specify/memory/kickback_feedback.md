# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`code/`, `data/`, `artifacts/`, `tests/`) is provided; the claim lacks any artifact listing or file tree confirming their existence. The task therefore remains unverified.
- `T016` (rejected 1x): No code, script, or notebook was provided that adds a `pot_incomplete` boolean column to the output DataFrame or emits the required warning log when the z‑axis data is missing. Consequently the required artifact is absent.
- `T017` (rejected 1x): No `energy_samples.csv` file was presented in the evidence, nor any listing of its location under `data/derived/`. Consequently the required output file with the specified columns is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

