# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository contains a partially‑implemented `src/data/collectors/survey_collector.py`, but the required fallback module `src/data/generators/structural_validation_generator.py` is absent, and the expected output files `data/raw/survey_raw.csv` and `data/raw/filtered_survey.csv` were not generated. Consequently the task’s full specifications are not satisfied.
- `T016` (rejected 1x): The provided `remote_sensing_collector.py` does not implement Sentinel‑2 download, cloud‑cover filtering, caching to `data/raw/sentinel2/`, nor does it invoke the missing `structural_validation_generator.py` for synthetic NDVI generation. Additionally, the required generator file is absent entirely.
- `T017` (rejected 1x): The provided `src/data/processing/spatial_join.py` is only a partial stub and never reads `buffer_size_km` from `src/config/constants.py`, performs a geodesic buffer, extracts mean NDVI, or writes the required `data/processed/spatial_joined_data.csv` and `data/logs/linkage_validation.json`. Both mandatory output files are missing from the repository.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/processing/feature_engineering.py, data/processed/raw_ndvi_timeseries.parquet
- `T017c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/logs/linkage_validation.json, data/raw/survey_raw.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

