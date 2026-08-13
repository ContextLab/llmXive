# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T026` (rejected 1x): No model files (e.g., `gpr_model.pkl` and `linear_regression.pkl` or similar) are present in the `results/models/` directory, nor any evidence (logs, screenshots, or code) showing that the trained GPR model and Linear Regression baseline were saved there. The required artifacts are missing.
- `T030` (rejected 1x): No code, notebook, script, data file, or results related to a permutation importance correlation analysis were provided. The task required an implementation (e.g., a function or script that computes permutation importance for model features and correlates it with processing parameters), but there is no artifact to verify its existence or correctness. The implementer must supply the actual implementation and any accompanying output (e.g., a CSV or plot) demonstrating the analysis.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

