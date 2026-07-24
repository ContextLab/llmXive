# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listings were provided to demonstrate that the required project folders (e.g., `projects/PROJ-503-predicting-plant-defense-compound-produc/code/`, `.../data/raw/`, etc.) actually exist; the response contains only the task description and no concrete filesystem evidence. The implementer must supply a verified directory listing or screenshots showing the full structure.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-503-predicting-plant-defense-compound-produc/pyproject.toml
- `T004` (rejected 1x): No evidence of the required utility functions or the log files (`logs/data_pairing.json` and `logs/feature_filtering.csv`) was provided; the claim lacks any actual artifacts to verify that the logging logic was implemented per the spec.
- `T006` (rejected 1x): No code files or class definitions were presented for `ExpressionMatrix`, `MetaboliteMatrix`, `FeatureSet`, or `ModelArtifact` in the required `projects/PROJ-503-predicting-plant-defense-compound-produc/code/models/` directory, so the required artifacts are absent. The implementer must add the four model class files (or a module containing them) with proper implementations.
- `T007` (rejected 1x): No code, configuration, or documentation defining the E‑DATASET, E‑PAIRING, E‑TIMEOUT, or E‑POWER error codes (and their handling) is present. The required error‑handling framework and its integration per plan.md are missing, so the task is not satisfied.
- `T009` (rejected 1x): No JSON file at `projects/PROJ-503-predicting-plant-defense-compound-produc/logs/power_analysis.json` was provided, nor any evidence of the power‑analysis calculation (effect size r = 0.5, α = 0.05, power = 0.8) or the required abort behavior when n < 28. The task’s core artifact is missing.
- `T010` (rejected 1x): The implementer provided no code, script, or documentation for a SHA‑256 checksum validation utility, nor any tests or usage examples. The only artifacts described relate to plant‑defense data acquisition and modelling, which do not satisfy the checksum utility requirement. A functional utility (e.g., a script or library that computes and verifies SHA‑256 hashes for files) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

