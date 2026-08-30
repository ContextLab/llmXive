# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The provided `fetch_google_trends.py` contains the fetch and retry logic but does not include code that writes the retrieved data to `data/raw/google_trends.csv` nor records its MD5 checksum, and the expected CSV file is absent from the repository. The task’s core output (the CSV file and its checksum) is therefore missing.
- `T019` (rejected 1x): No `preprocess.py` file or code snippet was provided, and there is no evidence that z‑score normalization after stationarity testing has been implemented. The required artifact is missing, so the task is not satisfied.
- `T020` (rejected 1x): No `preprocess.py` file (or any code) was provided showing the implementation of z‑score normalization after stationarity checks; without the artifact we cannot confirm the required functionality exists. The next implementer must add or supply the updated `preprocess.py` containing the normalization step.
- `T022` (rejected 1x): No code, script, or test artifact was provided showing that a validation check was added to abort with the message “Insufficient data for Granger causality” when the time‑series length is under 20. Without a concrete implementation or evidence of the new behavior, the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

