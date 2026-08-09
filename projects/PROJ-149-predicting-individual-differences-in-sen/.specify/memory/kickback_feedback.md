# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim/behavioral_metrics.csv, data/interim/behavioral_exclusion_log.csv
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim/eeg_psd.csv, data/interim/behavioral_metrics.csv, data/interim/features_relative.csv, data/processed/features.csv
- `T016` (rejected 1x): The required artifact `data/processed/features.csv` does not exist, so no schema validation (no‑null check, column verification, RT range check) could be performed. The task lacks the essential input file.
- `T017` (rejected 1x): The repository contains `code/04_modeling.py`, but the required input `data/processed/features.csv` is absent, and the expected output files `data/interim/split_indices.json` and `data/processed/model_results.json` were not generated or provided. Without these artifacts the modeling step cannot be executed or verified.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/features.csv
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim/split_indices.json, data/processed/model_results.json
- `T018` (rejected 1x): No code, script, notebook, or output files implementing LASSO regression with lambda tuning and reporting RMSE are present; the only provided material is the task description and specification excerpt, which does not constitute the required artifact. The implementer must supply the actual implementation and its results.
- `T019` (rejected 1x): The required artifact `data/processed/model_results.json` does not exist, so the adjusted R² and optimal lambda have not been logged as specified. The task therefore remains unfinished.
- `T021` (rejected 1x): No code, script, output file, or any other artifact demonstrating that a Bonferroni correction (0.05/6 = 0.0083) was applied and significant results were flagged is present. The claim cannot be verified because the required evidence is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

