# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025` (rejected 1x): The `filter_pool` function is only partially shown and ends abruptly without reading, filtering, or writing the CSV; the required input file `data/raw/raw_pool.csv` and the output `data/processed/filtered_pool.csv` are both absent. Consequently the filtering logic is not fully implemented nor can it be executed.
- `T026` (rejected 1x): The repository lacks the required `data/processed/filtered_pool.csv`, `data/processed/test_set_indices.csv`, and `data/processed/descriptors_pool.csv` files, and the shown `code/data_ingestion.py` does not contain any implementation of descriptor generation with `ElementalPropertyFeatureExtractor` or the logic to exclude test indices before imputation. Consequently, the task’s functional requirements are not met.
- `T027` (rejected 1x): The repository lacks the required `data/processed/test_set_indices.csv`, the log file `data/results/ingestion_log.json`, and the final output `data/processed/full_pool_final.csv`. Moreover, the provided `code/data_ingestion.py` excerpt shows no imputation, row‑dropping, or logging logic, so the core functionality is not implemented.
- `T031` (rejected 1x): The repository lacks the required input data (`full_pool_final.csv` and `test_set_indices.csv`) and the expected output (`rss_pool.csv`). Moreover, the provided `code/sparsity_generation.py` is truncated and does not show the implementation of stratified sampling and CSV writing, so the task’s functional requirement is not fulfilled. The missing files and incomplete script must be added for the task to be considered complete.
- `T033` (rejected 1x): The required output file `data/metadata/stratification_report.json` does not exist, and the provided snippet does not show code that writes the validation metrics to this JSON or raises an error when Jensen‑Shannon divergence exceeds 0.05. The implementation must create and populate the report file and enforce the failure‑blocking behavior.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

