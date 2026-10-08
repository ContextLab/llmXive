# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No configuration files, scripts, or documentation for managing Dryad/AnAge API keys or setting random seeds were provided; the claim lacks any tangible artifact demonstrating that environment configuration management has been implemented.
- `T011` (rejected 1x): The required artifact `tests/test_ingest.py` does not exist on disk, so no unit test for Dryad URL parsing and CSV loading is present. The task cannot be considered completed until this file is created with appropriate test code.
- `T017` (rejected 1x): The repository contains a partially‑implemented `code/03_clean_merge.py`, but the script is truncated and does not show the required merge, missing‑record logging, or schema validation logic. Moreover, the expected output file `data/processed/merged_data.csv` is absent, so the task’s core deliverable is not present. The next implementer must complete the merge implementation, ensure unmatched records are logged to `logs/missing_data_log.csv`, add validation for the specified columns, verify the wild‑caught filter, and produce the `merged_data.csv` file.
- `T022` (rejected 1x): The required input file `data/processed/merged_data.csv` is missing, so the script cannot extract unique species. Moreover, the provided `code/04_model_pglS.py` is truncated (the R code block ends abruptly) and does not contain a complete implementation to fetch and save the Newick tree. Both the essential data and a functional script are absent.
- `T025` (rejected 1x): The repository lacks the required `results/model_summary.csv` file, and the provided `code/04_model_pglS.py` is truncated before any logic that would save model results or log the phylogenetic signal (lambda). Consequently, the task’s core requirements are not fulfilled.
- `T026` (rejected 1x): The `code/R/02_sensitivity.R` script exists but is truncated and does not demonstrate writing a CSV with the required columns (`species_id`, `coefficient`, `se`, `p_value`, `method_justification`). Moreover, the expected output file `results/sensitivity_log.csv` is absent from the repository. Both the artifact and its output are missing or incomplete, so the task is not satisfied.
- `T036` (rejected 1x): declared artifact(s) missing/empty/invalid: results/moderator_plot.png

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

