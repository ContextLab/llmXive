# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T054` (rejected 1x): No updated README.md file is provided; there is no evidence that explicit instructions for obtaining UK Biobank data, the required placement in data/raw/, or the specific microbiome, cognitive, and dietary fields have been added. The required documentation artifact is missing.
- `T014a` (rejected 1x): The `code/data_ingestion.py` only defines `check_dqs_availability()` which logs a warning and returns `False` when `data/raw/dietary_data.csv` is absent; it does **not** raise a fatal error nor does it verify required columns such as ‘fruit’ or ‘vegetable’. Consequently the task’s requirement to perform an existence/column check and raise a fatal error (per T014b) is not satisfied, and the required dietary data file is also missing. The implementation must be updated to raise an error and validate required columns.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

