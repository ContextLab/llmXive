# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure or file listing is provided as evidence; the required folders (`code/utils`, `data/raw`, `data/processed`, `data/results`, `data/metadata`, `tests/unit`, `tests/integration`, `docs`) are not shown to exist or contain any content. The implementer must supply a concrete proof (e.g., a directory tree snapshot) that the specified structure has been created.
- `T024` (rejected 1x): The repository contains a `code/data_ingestion.py` file, but it only contains a placeholder `fetch_material_data` that expects `data/raw/raw_pool.csv` to already exist and does not perform any API download or exponential‑backoff logic. Moreover, the required `data/raw/raw_pool.csv` file is missing entirely. Consequently, the implementation does not meet the specification of downloading the data and producing the CSV with the required columns.
- `T025` (rejected 1x): The `filter_pool` function correctly implements the filtering criteria, but the script never writes the filtered DataFrame to `data/processed/filtered_pool.csv`, and the expected CSV file is absent from the repository. The task requires both the filtering logic **and** the saved output file, which are not present.
- `T026` (rejected 1x): The `code/data_ingestion.py` file is truncated and does not contain a complete implementation that creates the `ElementalPropertyFeatureExtractor` with the required properties nor writes the resulting descriptors to `data/processed/descriptors_pool.csv`. Moreover, the expected output file `data/processed/descriptors_pool.csv` is absent. The task therefore remains unfinished.
- `T027` (rejected 1x): The `code/data_ingestion.py` file does not contain any mean‑imputation, row‑dropping, or logging logic (the relevant sections are missing/truncated). The required `data/results/ingestion_log.json` file is absent, and the produced `full_pool_final.csv` contains only 10 rows (far fewer than the >100 000 rows expected) with no indication that missing numeric descriptors were mean‑filled. These core requirements are not satisfied.
- `T020` (rejected 1x): The repository contains a partially shown `code/test_split.py`, but the file is truncated (e.g., `save_metadata` is incomplete) and no `data/processed/test_set.csv` was generated. The required output artifact is missing, so the task is not fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

