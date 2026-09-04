# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025` (rejected 1x): No `train.py` file was presented in `code/modeling/`, nor any code snippet showing it loading `clean_mg_data.parquet` and constructing a feature matrix. Without the actual script, we cannot confirm the required artifact exists or meets the specification. The implementer must provide a non‑empty `train.py` that performs the described data loading and feature preparation.
- `T031` (rejected 1x): No model files or metadata were found in a `models/` directory; the implementer provided no serialization artifacts, hyperparameter listings, or cross‑validation scores, so the required output is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

