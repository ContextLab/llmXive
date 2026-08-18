# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The repository lacks the required `data_manifest.yaml` file, so the download module cannot obtain an accession list as specified. Moreover, the provided `download.py` is truncated and does not show the logic that (a) performs the query `"plant AND disease resistance AND (SNP OR metabolite)"`, (b) retries three times and then switches to synthetic generation, or (c) bypasses T019 halt logic when `source == SIMULATED`. These essential behaviors are absent or unverifiable.
- `T019` (rejected 1x): The provided `code/main.py` is present but the required `data_manifest.yaml` file is missing, so the integrity‑checking logic cannot be exercised. Moreover, the truncated implementation does not clearly show the unified error handling or the exact conditional order mandated by the task. The missing manifest file must be added (with appropriate fields) and the script verified to raise the specified error codes in the correct priority order.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/metrics.json
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/selection_frequency.csv
- `T027` (rejected 1x): The repository contains a partially‑implemented `biomarker_report.py` (the file is truncated and never writes a `top_features.csv`). Moreover, the required output file `artifacts/reports/top_features.csv` does not exist. The task’s core requirement—producing a CSV of top features with p‑values and effect sizes—is therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

