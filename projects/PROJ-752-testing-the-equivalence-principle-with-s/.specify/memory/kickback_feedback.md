# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No `utils/logging.py` file (or any non‑empty implementation) was presented in the evidence. Without the required module containing the standardized error handling and progress‑logging code, the task is not satisfied. The next implementer must add a functional `utils/logging.py` with the specified logging utilities.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: data/ingestion.py
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/ingestion.py
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/ingestion.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/preprocessing.py
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/preprocessing.py
- `T018` (rejected 1x): No code, configuration, or documentation showing that 403 HTTP errors are caught and handled, nor any logic that detects and warns when a dataset contains fewer than 500 points, was provided. The required error‑handling implementation and associated tests or logs are missing.
- `T019` (rejected 1x): The required `data/processed/cleaned_slr_data.csv` file does not exist, and the accompanying `.checksums.json` contains a placeholder hash rather than a real SHA‑256 checksum of the CSV. Both the output file and a valid checksum are missing, so the task is not satisfied.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: models/dynamics.py
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: models/estimator.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

