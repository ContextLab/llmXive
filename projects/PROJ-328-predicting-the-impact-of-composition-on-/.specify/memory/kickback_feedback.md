# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009a` (rejected 1x): I could find no evidence of a `code/utils/` directory or an `__init__.py` file within it; the provided artifacts contain no such scaffolding, so the required file is missing.
- `T014a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/excluded_records.csv, data/processed/solder_hardness_cleaned.csv, data/processed/validation_metrics.yaml
- `T014b` (rejected 1x): The repository contains the `aggregate_final_report.py` script, but the required input files (`data/processed/.ingestion_status.json` and `data/processed/report.yaml`) are absent, and the expected output file (`data/processed/final_aggregated_report.yaml`) was not generated. Without these artifacts the script cannot fulfill its purpose.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/validation_report.yaml
- `T054` (rejected 1x): The `collinearity.py` file defines VIF calculation utilities but does not contain any logic to write a `vif_report.yaml` file, and the expected `data/processed/vif_report.yaml` file is absent from the repository. Consequently the required detailed report is not produced.
- `T016c` (rejected 1x): The required input artifacts `data/processed/.ingestion_status.json` and `validation_metrics.yaml` are missing, and there is no evidence that the script was executed or that a valid `validation_report.yaml` was produced. The integration test therefore was not performed.
- `T023b` (rejected 1x): The repository lacks the required `data/processed/solder_hardness_cleaned.csv` input file and the `data/processed/clr_features.csv` output file. Moreover, `code/features/transformer.py` does not contain any code that reads the cleaned CSV, applies the CLR transform, and writes the resulting matrix to `clr_features.csv`. The task’s core requirement—producing the CLR‑transformed feature file from the specified input—is therefore unmet.
- `T023c` (rejected 1x): The repository contains `code/features/descriptor_engine.py`, but the required input file `data/processed/solder_hardness_cleaned.csv` and the expected output `data/processed/descriptors.csv` are absent, so the descriptor calculations cannot be performed nor saved. The missing files must be provided and the engine must actually write the descriptors to `descriptors.csv`.
- `T027a` (rejected 1x): The `paired_ttest.py` script is present but truncated and never writes the required `t_statistic`, `p_value`, and `significant` keys to `data/processed/paired_ttest_results.yaml` (the YAML file is missing). Additionally, the required `code/evaluation/grid_search_config.py` file does not exist. Both missing artifacts violate the task’s critical requirements.
- `T031` (rejected 1x): No artifacts (code changes, updated visualizations, or revised final report) were provided showing that associational framing warnings were added to model outputs, visualizations, or the report as required by FR‑007. Without concrete evidence of these warnings being implemented, the task cannot be considered completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

