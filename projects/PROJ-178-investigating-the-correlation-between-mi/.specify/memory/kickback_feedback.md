# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): No code, script, or data file implementing the metadata merge logic was provided; there is no artifact (e.g., Python/R script, function, or resulting merged CSV/Parquet) that joins burden, haplogroups, age, sex, population, and PCs as required. The implementer’s claim consists only of a textual description without any concrete implementation or output.
- `T019` (rejected 1x): No code, script, configuration, or log file implementing the exclusion of samples with missing age or failed haplogroup assignment was provided; the evidence on disk is empty, so the required exclusion logic cannot be verified.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/processed/mito_aging_dataset.csv
- `T024` (rejected 1x): The `code/analysis/model.py` file stops mid‑function and never performs the OLS fit, compute adjusted p‑values, or write results to a CSV. Moreover, the required output file `code/data/processed/model_results.csv` does not exist. Both the implementation and the saved results are missing.
- `T028` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/processed/analysis_results.csv
- `T041` (rejected 1x): No `paper/draft.md` file or its contents were provided; without the markdown document showing the required findings and limitations, we cannot confirm that the documentation update was performed. The necessary artifact is missing.
- `T042` (rejected 1x): No cleaned or refactored scripts from the `code/analysis/` directory are present; the implementer provided no code artifacts, diff patches, or documentation indicating that the cleanup was performed. Consequently the required output for task T042 is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

