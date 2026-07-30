# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009c` (rejected 1x): No `data-model.md` file or its contents were presented, so we cannot verify that it references the new contract files or defines `run_id` propagation. The required documentation artifact is missing.
- `T016` (rejected 1x): No code, tests, or documentation were presented showing that logic was added to detect zero‑variance columns or missing image/text fields and to skip or impute them. Without any artifact (e.g., updated data preprocessing module, unit tests, or commit diff) the requirement is not demonstrated. The implementer must provide the actual implementation and evidence that it runs correctly on such edge‑case datasets.
- `T017` (rejected 1x): No evidence of a Parquet file at `data/processed/embeddings_{run_id}.parquet` was provided, nor any code or description showing that such a file is created with the required `run_id` and metadata. The required serialization artifact is missing.
- `T018` (rejected 1x): No code, test, or documentation artifact was provided showing that a validation step was added to guarantee that gradient tracking is disabled during inference. Without a concrete implementation (e.g., a function/assertion in the inference pipeline, unit tests, or a commit diff), the requirement cannot be confirmed as satisfied. The next implementer must add the validation code and supply the corresponding source file or test results.
- `T024` (rejected 1x): The provided `metadata_stats.py` is truncated (ends mid‑function) and does not contain the logic to iterate over all datasets, compute the four statistics, and write `data/processed/metadata_stats_summary.csv`. Moreover, the required summary CSV file is absent from the repository. Both the implementation and the output artifact are missing.
- `T026` (rejected 1x): No code, script, or documentation was provided showing that logic for handling edge cases such as zero‑variance features was added (e.g., skipping those columns or imputing constant values). Without an artifact demonstrating the implementation (and any associated tests), the requirement cannot be confirmed as met. The next implementer should add the necessary code changes and include the updated files or a diff as evidence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

