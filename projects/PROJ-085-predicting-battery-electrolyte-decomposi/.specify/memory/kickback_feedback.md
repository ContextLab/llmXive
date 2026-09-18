# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No logging configuration file, code snippet, or documentation was provided that sets up a logging infrastructure to emit warnings for missing geometric data or metallic behavior outliers. The required artifact is missing, so the task is not satisfied.
- `T009` (rejected 1x): No configuration artifact (e.g., a `.env`, `config.yaml`, or Python module) defining random seeds and dataset URLs is present in the provided evidence, nor any documentation describing such setup. Consequently the requirement to establish environment configuration management is not satisfied.
- `T017` (rejected 1x): No code, script, or test output was provided showing that a validation step was added to check for missing values in the feature matrix before it is written out. Without an artifact (e.g., a function, unit test, or log demonstrating the check), we cannot confirm the requirement was implemented. The next implementer must add and commit the validation logic and supply the corresponding code or test evidence.
- `T024` (rejected 1x): No code, data, or report was provided that implements the required logic to find descriptors that enter the top‑3 importance at the high‑potential (4 V) bin but are absent from the low‑potential (0‑2 V) bin, nor any documentation explicitly referencing the spec’s 3‑5 V range and the known 4 V mapping limitation. The implementer must supply the actual implementation (e.g., a script or notebook) and its output demonstrating the identified descriptors and the required spec commentary.
- `T025` (rejected 1x): declared artifact(s) missing/empty/invalid: data/validation/feature_importance_heatmap.png

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

