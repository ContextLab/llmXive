# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012c` (rejected 1x): The repository lacks a `generate_manifest(accessions, geo_accessions)` function in `src/download.py` and the required `data/manifest.json` file is not present. The existing code only provides placeholder/template functions and a `generate_manifest_v2` that writes separate manifest files, not a single unified manifest as specified.
- `T015a` (rejected 1x): declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/ortholog_map.csv
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/normalized_counts.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

