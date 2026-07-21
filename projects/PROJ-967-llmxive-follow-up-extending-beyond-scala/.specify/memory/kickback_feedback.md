# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or screenshots were provided to demonstrate that `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw`, `data/processed`, `code`, `tests`, and `results` actually exist. Without concrete evidence of these folders being created, the task requirement is not satisfied.
- `T001d` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T001e` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/features.json, results/results.json
- `T003` (rejected 1x): The repository contains a `pyproject.toml`, but it does not pin exact versions (uses `>=` ranges) and the required `.ruff.toml` file is missing entirely, so the linting/formatting configuration is incomplete and does not meet the task’s specification.
- `T038` (rejected 1x): The required `contracts/dataset.schema.yaml` file is missing, so the validation step cannot be performed; additionally, no script or code artifact that reads the schema and checks the CSV columns is provided. The implementer must supply the schema file (defining the rubric dimensions and expected CSV columns) and a validation implementation that raises an error on mismatches.
- `T004` (rejected 1x): No ingestion script, feature‑engineering code, or predictive‑modeling implementation (or their outputs) were provided; the claim lacks any concrete artifacts to verify that the Z‑Reward dataset was loaded, entanglement scores computed, and a Random Forest regressor trained and evaluated. The required scripts and results are missing.
- `T039` (rejected 1x): No code, data files, or result artifacts (e.g., ingestion script, JSON feature outputs, Random Forest training logs or model files) are present to demonstrate that the Z‑Reward dataset was loaded, teacher score distributions were processed, entanglement features were computed, and a predictive model was trained and validated. The claim lacks any tangible evidence, so the task requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

