# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The provided `code/ingestion.py` shows only DGP‑related utilities and does not contain logic that scans `data/raw/` for ARFF/CSV files, validates required columns, or writes `data/processed/data_source_flag.json`. Moreover, the flag file is absent from the repository. Consequently the real‑data ingestion requirements are not satisfied.
- `T014` (rejected 1x): The repository lacks the required `data/processed/data_source_flag.json` file, and the shown `code/ingestion.py` does not contain logic that creates three distinct CSV files of 500 participants, logs the exact DGP parameters, or writes the flag JSON with the SHA‑256 hash. These essential artifacts are missing, so the task is not fully satisfied.
- `T016` (rejected 1x): The required `data/processed/model_config.json` file is not present, and the provided `code/ingestion.py` does not contain logic to compute missingness for `age`/`gender`, decide on reduced‑model flagging, or perform mean imputation as specified. The task’s core requirements are therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

