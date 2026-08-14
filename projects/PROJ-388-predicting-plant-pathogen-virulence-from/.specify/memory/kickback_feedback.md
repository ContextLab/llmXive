# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The `src/data/merge.py` file exists and includes an `align_genomic_phenotypic` function that merges and logs missing rows, but the module is truncated (e.g., an unfinished `detect_aggregation_need` definition) and the required output file `data/processed/merged_raw.parquet` is not present. The pipeline therefore does not produce the specified merged Parquet file.
- `T021` (rejected 1x): The repository contains a `src/data/merge.py` file, but it is truncated and does not show any code that writes the merged DataFrame to `data/processed/merged_dataset.parquet` or generates the required summary report. Moreover, the expected output file `data/processed/merged_dataset.parquet` is absent from the project. These missing pieces mean the task’s core requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

