# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024a` (rejected 1x): The repository contains a partially shown `metadata_stats.py` that does not include a complete `compute_cardinality` implementation (the file is truncated and the function is unfinished). Moreover, the required output file `data/processed/metadata_stats_cardinality.csv` is absent. Both the functional code and the expected CSV output are missing, so the task is not satisfied.
- `T024b` (rejected 1x): The repository lacks the required output file `data/processed/metadata_stats_missingness.csv`, and the provided `metadata_stats.py` does not contain a complete implementation of `compute_missingness` (the file is truncated before such a function appears). Consequently, the task of computing missingness for all datasets and writing the summary CSV has not been fulfilled.
- `T024c` (rejected 1x): The repository contains a partially shown `metadata_stats.py` but the `compute_sparsity` function is not present (or is incomplete) and the required output file `data/processed/metadata_stats_sparsity.csv` does not exist. Consequently the task of computing sparsity for all datasets and writing the summary CSV has not been fulfilled.
- `T024d` (rejected 1x): The repository lacks the required `data/processed/metadata_stats_variance.csv` file, and the provided `metadata_stats.py` does not contain a completed `compute_variance` implementation (the file is truncated before such a function appears). Both the function and its expected output are missing, so the task is not satisfied.
- `T024e` (rejected 1x): The required output file `data/processed/metadata_stats_summary.csv` is missing from the repository, so the task’s core deliverable (a merged and sorted CSV containing the selected subset) was not produced. Without this artifact, the task’s requirement is not satisfied.
- `T024f` (rejected 1x): The `code/pipelines/normalize_tabular.py` script is present but its content is truncated and does not show the logic that writes `data/processed/normalized_tabular_features.parquet`. Moreover, the required Parquet file is absent from the repository. The pipeline therefore has not produced the mandated output. The next implementer must complete the script to load all raw tabular data, apply the `normalize_features` function globally, handle missing values, and write the combined normalized DataFrame to the specified Parquet file.
- `T045` (rejected 1x): The required input `data/processed/metadata_stats_summary.csv` is absent, and the expected output `data/artifacts/data_integrity_report.json` was not generated. Without these files the pipeline cannot perform the integrity checks or produce the required report.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

