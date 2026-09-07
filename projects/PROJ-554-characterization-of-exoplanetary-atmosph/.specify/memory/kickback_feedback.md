# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025c` (rejected 1x): The repository lacks a `bootstrap_kendall_tau` implementation in `code/analysis.py` (the file ends before such a function appears) and the required output files `data/processed/bootstrap_ci.json` and `data/processed/water_mixing_ratio_samples.npy` are not present. Consequently the task’s deliverables are missing.
- `T027` (rejected 1x): The required output file `data/processed/regression_results.json` does not exist, and the provided `code/analysis.py` excerpt shows no implementation of the `fit_tobit_model` function (the file is truncated before any such logic). Both the artifact and the core functionality are missing.
- `T045` (rejected 1x): declared artifact(s) missing/empty/invalid: results/spectral_resolution_report.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

