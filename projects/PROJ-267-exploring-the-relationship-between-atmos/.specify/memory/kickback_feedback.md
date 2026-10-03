# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011a` (rejected 1x): The provided `01_fetch_coefficients.py` never reads `config/urls.yaml` (the file is missing) and the displayed code is truncated before the C20‑fetch block, so it’s unclear if it fully implements the required logic. Moreover, the generated `coeffs/degree1.yaml` and `coeffs/c20.yaml` contain placeholder comments rather than the fetched coefficient values, indicating the script did not produce the expected output. The task therefore remains unfinished.
- `T017b` (rejected 1x): The repository contains `code/02_preprocessing_noaa.py`, but the required output files `data/processed/noaa_preprocessed_target.csv` and `data/processed/noaa_preprocessed_control.csv` are absent, indicating the script does not (or has not been run to) generate the mandated CSVs. Consequently the task’s core deliverable is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

