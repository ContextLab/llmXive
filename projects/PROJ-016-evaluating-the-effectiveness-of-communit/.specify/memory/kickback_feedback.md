# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The required metadata file `data/processed/cbnrm_proxy_metadata.json` is missing, the CSV only contains data for 2000‑2001 (not the full 2000‑2020 range), and there is no evidence that the indicator was verified in the World Bank API or that errors were logged on failure.
- `T009b` (rejected 1x): The `code/data/classify.py` script only defines helper functions (e.g., `validate_proxy_variance`) and does not contain code that loads `data/raw/cbnrm_proxy.csv`, runs the variance check, and writes the results to `data/processed/proxy_validation.json`. Moreover, the required output file `data/processed/proxy_validation.json` is missing entirely. The task’s core requirement—producing the JSON file with the excluded country list—is therefore not satisfied.
- `T014` (rejected 1x): The required input files `data/processed/cbnrm_proxy_metadata.json`, `data/processed/proxy_validation.json`, and the output `data/processed/classified_panel.csv` are all absent, and the provided `classify.py` does not contain logic that checks for missing/empty metadata, raises the specified error message, applies the threshold‑based classification, or writes the classified panel to CSV. The task’s core requirements are therefore not satisfied.
- `T022` (rejected 1x): The repository lacks the required `data/processed/classified_panel.csv` input and the `data/processed/time_invariant_countries.json` output file. Moreover, while `regression.py` contains detection logic, it does not include code that loads the CSV and writes the JSON, so the end‑to‑end diagnostic is not realized.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

