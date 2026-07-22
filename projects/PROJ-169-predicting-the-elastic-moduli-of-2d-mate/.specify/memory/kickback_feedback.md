# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013d` (rejected 1x): The `code/ingest/pipeline.py` file is truncated, contains syntax errors, and does not implement the full download‑parse‑filter‑save workflow nor the required error handling. The separate `validate_schema.py` script is absent, and the expected output file `data/processed/graphs_v1.parquet` does not exist. These missing or broken artifacts prevent the task from being satisfied.
- `T013e` (rejected 1x): The `code/ingest/pipeline.py` file is truncated, contains syntax errors, and does not include the required post‑processing check that counts unique entries and exits on ≤ 1000. Additionally, the required data file `data/processed/graphs_v1.parquet` is absent. Both the code change and the data artifact needed to satisfy the task are missing.
- `T013f` (rejected 1x): The repository contains `code/ingest/split_generator.py`, but the file is truncated and does not clearly show a complete implementation that loads structures, uses `StructureMatcher` to compute `family_id`, performs a stratified `train_test_split` with `random_state=42`, asserts no family overlap, and writes the split to `data/processed/split_indices.json`. Moreover, the required output file `data/processed/split_indices.json` is missing entirely. The task’s primary deliverable is therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

