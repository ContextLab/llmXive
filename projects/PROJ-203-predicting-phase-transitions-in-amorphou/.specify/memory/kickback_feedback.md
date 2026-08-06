# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/final_dataset.parquet
- `T015` (rejected 1x): The `train.py` file is present but truncated (the shown code ends abruptly and does not include any train/test split logic), and the required dataset file `data/processed/final_dataset.parquet` is missing from the repository. Both the core functionality (stratified split) and the prerequisite data are absent, so the task is not genuinely completed.
- `T018` (rejected 1x): The `train.py` file is present but the provided excerpt ends abruptly and shows no actual k‑fold cross‑validation logic or model‑saving code, and the required model files `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl` are absent from the repository. Both the functional implementation and the saved artifacts are missing.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

