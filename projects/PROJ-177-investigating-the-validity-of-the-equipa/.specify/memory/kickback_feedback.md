# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/`, `artifacts/`, `tests/`) is provided; the response contains only specification text and no actual project structure artifacts. The implementer must create and show these folders (with at least placeholder files) to satisfy the task.
- `T020a` (rejected 1x): No `artifacts/test_params.json` file was presented, and there is no evidence that a JSON containing the required parameters (Maxwell‑Boltzmann mean = 1.0, scale = 0.1; Pareto shape = 2.0) was created. The implementer must supply the actual JSON file with those fields.
- `T020b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/derived/test_thermal_data.csv, data/derived/test_nonthermal_data.csv
- `T012a` (rejected 1x): The required files `artifacts/manual_baseline.csv` and `artifacts/energy_verification_report.json` are not present in the provided evidence, and no content is shown that demonstrates the synthetic dataset generation, manual energy calculations, or the verification report with the max absolute error. Without these artifacts, the task’s acceptance criteria cannot be confirmed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

