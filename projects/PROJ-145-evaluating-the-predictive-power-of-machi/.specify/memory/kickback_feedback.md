# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017a` (rejected 1x): The required output file `data/raw/aflow_raw.parquet` does not exist, and the provided `code/data_ingestion.py` loads a different HuggingFace dataset (`hmao/all_apis_for_multiapi`) rather than `foundry-ml/dataset_thermodynamics_aflow`. No checksum retrieval or verification is implemented.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/true_novel.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

