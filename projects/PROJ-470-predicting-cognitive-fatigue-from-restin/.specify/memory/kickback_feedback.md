# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The `code/preprocess.py` file exists and contains band‑pass and notch filtering logic, but the required input `data/raw/download_manifest.json` is missing, so the script cannot actually read the full dataset as mandated. Without this manifest the implementation cannot be executed or verified.
- `T013` (rejected 1x): The required `data/processed/exclusion_log.csv` file is missing, so the verification condition cannot be met. Without this log (even an empty header‑only file), the task’s requirement of recording epoch rejections is not satisfied. The implementer must ensure the preprocessing code creates `exclusion_log.csv` with the columns `[participant_id, reason, timestamp]` (populated or header‑only).
- `T014` (rejected 1x): The required `data/processed/exclusion_log.csv` file does not exist, and the provided `code/preprocess.py` excerpt shows only the constant `MIN_SEGMENT_DURATION_SEC` without any logic that actually checks segment length or logs rejections. Consequently, the segment‑length validation and logging stipulated by the task are not implemented.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/analysis/vif_diagnostics.log, data/analysis/vif_valid_predictors.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

