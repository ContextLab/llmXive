# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- `T017b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/ingestion_report.json
- `T017` (rejected 1x): The required artifact `data/processed/ingestion_report.json` does not exist, so the task’s requirement of logging the exclusion metrics cannot be satisfied. The missing file must be created and contain the specified keys.
- `T020a` (rejected 1x): The required input `data/processed/cleaned_microbiome_sleep.csv` does not exist, nor does the expected output `data/processed/diversity_results.csv`. Moreover, the provided `src/diversity.py` is truncated and does not show a complete implementation of chunked alpha‑diversity calculation, file‑existence checks, or CSV writing. The task’s deliverables are therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

