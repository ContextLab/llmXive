# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The provided `download_gsm8k.py` is truncated and does not show the required logic for enforcing a 500‑example target, issuing a warning when fewer than 500 but ≥10 examples are available, and saving the filtered data to `data/raw/gsm8k_verified.parquet`. Moreover, the expected parquet file is absent, indicating the script either was not executed or does not correctly produce the output. The next implementer should ensure the script contains the full download, filtering, target‑size handling, warning, and saving logic, and that the parquet file is generated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

