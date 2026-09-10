# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or screenshots were provided to confirm that the required folders (`code/`, `data/`, `tests/`, `state/`, `models/`, `data/raw/`, `data/processed/`, `reports/`) actually exist on disk. Without concrete evidence of these directories, the task cannot be considered completed.
- `T009` (rejected 1x): No directory listings, creation scripts, or verification output were provided, so there is no evidence that `data/raw/`, `data/processed/`, `models/`, and `reports/` actually exist or were checked. The required artifacts are missing.
- `T039` (rejected 1x): No `research.md` file content or verification output was provided, so we cannot confirm that it contains only static, pre‑verified URLs/IDs and lacks any dynamic search logic as required. The artifact is missing or empty.
- `T012` (rejected 1x): No code, script, or dataset artifact was provided that demonstrates dropping records with missing predictor values while retaining those missing `contact_load`/`sliding_speed` and setting `normalization_method='raw'`. The required preprocessing implementation and its output (e.g., cleaned CSV and `missing_record_count` metric) are missing.
- `T018` (rejected 1x): No code, notebook, script, or output showing a GridSearchCV with ≥10 distinct hyperparameter combinations and proper nested or separate‑training‑split 5‑fold CV is present. The evidence provided is only the task description and requirements, without any implementation artifact to verify the grid search or leakage prevention.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

