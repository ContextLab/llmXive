# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T031` (rejected 1x): The repository contains `code/eval/sensitivity.py`, but the shown portion stops before any implementation of the configurable `--sweep-factor`, the median ± k·std threshold sweep, or CSV writing logic. Moreover, the required output file `results/sensitivity_analysis.csv` is absent. The task’s core functionality and expected result artifact are therefore not present.
- `T032` (rejected 1x): The required output files `results/predictions.csv` (with `ci_lower` and `ci_upper` columns) and `results/uncertainty_calibration.json` are absent, and the provided `code/eval/predictor.py` is truncated and does not show the percentile CI calculation, CSV augmentation, or coverage logging. The task’s core requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

