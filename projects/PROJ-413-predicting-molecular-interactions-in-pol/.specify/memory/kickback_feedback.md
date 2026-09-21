# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/curated/curated_dataset.csv
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: data/curated/curated_dataset.csv, data/processed/descriptors.csv
- `T019` (rejected 1x): The required `data/curated/curated_dataset.csv` does not exist, so no hash can be computed, and `code/utils/hash_state.py` contains only generic utility functions without any code that actually calculates and records the SHA256 of that specific CSV file. The task’s core requirement is therefore unmet.
- `T024` (rejected 1x): The required input CSV (`data/curated/curated_dataset.csv`) and the generated output file (`data/processed/graphs.pt`) are both missing, and the provided `graph_build.py` is incomplete (truncated) and does not demonstrate writing the PyG `Data` objects to the expected `.pt` file. The task therefore is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

