# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/extract_optical.py, data/processed/features_optical.json
- `T013a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/extract_audio.py, data/processed/features_audio.json
- `T016a` (rejected 1x): The provided `src/models/metrics.py` contains correlation utilities but no code that loads `features_optical.json` / `features_audio.json`, filters `missing_data_flag=True`, or creates and saves the `data/processed/correlation_data.pkl` file. Moreover, the expected `correlation_data.pkl` file is absent from the repository. The task’s core data‑preparation output is therefore missing.
- `T016b` (rejected 1x): The provided `metrics.py` defines Pearson and Spearman functions but never loads `correlation_data.pkl` nor writes `data/processed/correlations_point.csv`. The required output CSV is missing from the repository. Consequently the task’s core requirement is not fulfilled.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: src/reports/generate.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/dimension_viability.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

