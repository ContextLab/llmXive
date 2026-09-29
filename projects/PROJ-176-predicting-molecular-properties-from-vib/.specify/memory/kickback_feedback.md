# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/`, `specs/`) being present in the repository is provided; the artifact list is empty, so the project structure has not been demonstrated. The implementer must create and show these folders with at least placeholder files to satisfy the task.
- `T007` (rejected 1x): No evidence was provided that a `data/` directory (with `raw/`, `preprocessed/`, and `external/` subfolders) actually exists in the project; the implementer did not supply any file listings or screenshots confirming the required directory structure. The task therefore remains unverified.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T017` (rejected 1x): No code, configuration, or log files were provided to demonstrate that logging was added to the data ingestion pipeline or that mismatch counts are recorded. Without such artifacts, we cannot confirm the requirement was implemented. The next implementer must supply the modified ingestion script (or related module) showing logging statements and, ideally, example log output indicating mismatch counts.
- `T030` (rejected 1x): The `evaluate.py` script is truncated (the `if __name__ == "__main__":` call is incomplete) and the required output file `results/evaluation_metrics.json` does not exist, so the task of loading the model, running inference on the test set, and generating the JSON metrics has not been fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

