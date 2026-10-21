# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): The repository contains `code/ingestion/download_real.py` and the integration tests, but the required raw data directories (`data/raw/ace_swics/`, `data/raw/wind_sms/`, `data/raw/omni/`) and the `data/raw/checksums.yaml` file are all missing. Without these artifacts the script cannot fulfill the core requirement of downloading and preserving the real CDF files.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

