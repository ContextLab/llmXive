# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004b` (rejected 1x): The required file `src/data/verify_provenance.py` does not exist, so no provenance‑checking logic, JSON output, or exit‑code behavior is present. The task cannot be considered fulfilled until this script is created and implements the specified checks.
- `T019` (rejected 1x): The provided `src/models/evaluate.py` only defines generic MSE/RMSE helpers and a CSV writer, but it does not compute per‑dimension baseline results, does not calculate R², does not implement the validation against the best model from T015, nor does it exit with code 1 on failure. Moreover, the required output file `data/baseline_results.csv` is missing. The task’s core requirements are therefore unmet.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: src/reports/generate.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/dimension_viability.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

