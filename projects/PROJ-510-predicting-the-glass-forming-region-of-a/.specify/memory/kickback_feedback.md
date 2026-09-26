# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): The repository lacks the required `data/logs/fetch_error.log` file, and the provided `ingestion.py` snippet is truncated before any `except` clause that would catch fetch failures and write to that log. Consequently the error‑handling behavior specified in the task is not demonstrably present.
- `T010a` (rejected 1x): No `test_features.py` file or `test_mixing_enthalpy` unit test is present in the provided artifacts, so the required unit test does not exist or is empty. The implementer has not supplied the test code that should run after T014.
- `T010b` (rejected 1x): No `test_features.py` file or the specific `test_size_mismatch` unit test is present; the only evidence is a high‑level feature specification, not the required test code or its execution results. The task demands a concrete unit test artifact, which is missing.
- `T016a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/processed_alloys.csv
- `T020` (rejected 1x): No code, notebook, script, or output file showing that `processed_alloys.csv` was loaded and split with `random_state=42` and `test_size=0.2` is present. The required artifact (e.g., a Python script, Jupyter notebook, or saved train/test CSVs) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

