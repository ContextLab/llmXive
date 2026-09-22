# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The required artifacts `data/processed/sampled_dataset.parquet` and `data/processed/sampling_report.json` are absent, so the sampling logic and reporting have not been produced. Additionally, `MAX_MOLECULES` is not defined in `code/config.py`, preventing the conditional behavior from being exercised. The task therefore remains unfinished.
- `T014#1` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/atom_count_success_report.json, data/processed/atom_count_failure_report.json
- `T014#2` (rejected 1x): The required output files `data/processed/conformer_params.json` and `data/processed/graphs_with_features.parquet` are absent, and the shown portion of `code/data/preprocess.py` does not contain the filtering, 2D feature extraction, molecular weight calculation, logging of excluded molecules, or embedding of conformer parameters into Parquet metadata as specified. The task therefore remains unfinished.
- `T015b` (rejected 1x): The required output file `data/processed/descriptors.parquet` does not exist, and the shown portion of `code/data/preprocess.py` contains only conformer‑generation utilities – it lacks any SASA calculation, 3D descriptor computation, or code that writes the described Parquet file. Consequently the task’s deliverables are not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

