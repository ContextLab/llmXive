# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The `code/preprocessing.py` file contains a partially shown `perform_construct_validity_check` implementation, but the required output file `data/processed/proxy_validation_report.csv` is missing, and the provided code snippet is truncated before any CSV‑writing or halt‑signalling logic is demonstrated. Without the generated report (and confirmed halt behavior), the task is not fully satisfied.
- `T085` (rejected 1x): The required artifact `data/processed/crosslinker_sensitivity_report.csv` does not exist, and the provided `code/modeling.py` contains only modeling utilities with no implementation that writes or validates a crosslinker sensitivity report. The task’s core requirement is therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

