# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_data_pipeline.py, data/processed/merged_dataset.csv
- `T012` (rejected 1x): The `fetch_viral_genomes` function in `src/download.py` is a stub that raises `NotImplementedError`, so no real NCBI Virus API query, FASTA parsing, or dict output is produced. Moreover, the required `data/manifest_v1.json` file does not exist, and the manifest generation logic does not compute SHA‑256 checksums or follow the exact key schema. The task’s core functionality and manifest output are missing.
- `T013` (rejected 1x): The `fetch_geo_data` function is still a stub that raises `NotImplementedError`, so no GEO download or parsing occurs, and no dictionary of sample‑to‑strain accessions is produced. Moreover, the required `data/manifest_v2.json` file does not exist (and the manifest generation code leaves the `checksums` field empty). Both the core function and the manifest output are missing, so the task is not satisfied.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/normalized_counts.csv
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/ortholog_map.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

