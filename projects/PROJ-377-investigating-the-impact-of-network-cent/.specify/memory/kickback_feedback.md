# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No code, script, or documentation was provided that implements the required power‑check logic (i.e., testing N < 85, logging the specific warning, proceeding with caution, and flagging the issue in the final report). Consequently the artifact the task demands is missing.
- `T017` (rejected 1x): The required output file `data/processed/behavioral/subject_scores.csv` does not exist, so the behavioral metric extraction and saving step has not been delivered. The raw metadata is present, but the processed CSV with the specified columns (including `improvement_score`) is missing.
- `T019` (rejected 1x): No code, test scripts, or log output were provided to demonstrate that validation for ≥ 80 % subject retention and graceful handling of missing behavioral data was added and that appropriate logging occurs. The claim lacks any concrete artifact confirming the required functionality.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/logs/exclusion_log.csv
- `T041` (rejected 1x): No updated files were presented in `docs/` or `README.md`; the evidence section contains no artifacts, so the required documentation changes are missing. The implementer must add the revised documentation files with the appropriate content.
- `T042` (rejected 1x): No downloadable scripts, preprocessing pipelines, centrality calculation code, regression outputs, or figures were provided. The claim lacks any actual artifacts (e.g., CSV dataset, Python notebooks, or image files) required to demonstrate that the data ingestion, centrality analysis, and validation steps were completed.
- `T043` (rejected 1x): No code, data files, CSV outputs, regression tables, or figures were provided; the claim lacks any tangible artifacts demonstrating that the dataset was downloaded/preprocessed, centrality metrics computed, or models fitted as required. The required deliverables are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

