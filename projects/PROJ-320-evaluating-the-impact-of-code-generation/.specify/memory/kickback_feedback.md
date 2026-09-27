# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T033` (rejected 1x): The repository contains `code/analysis/save_complexity_scores.py`, but the required output file `data/processed/complexity_scores.csv` is missing, and the prerequisite input `data/processed/prs_labeled.csv` does not exist, so the script cannot be executed to produce the expected CSV with the correct columns. The task is therefore not fulfilled.
- `T028` (rejected 1x): The repository lacks the required `data/audit/error_rate.json` and the resulting `data/processed/gate_status.json` files, and the provided `generate_results_report.py` is incomplete (truncated) and writes a key `"gate_status"` instead of the required `"status"` per the JSON schema. The task’s output artifacts are therefore missing or incorrect.
- `T030a` (rejected 1x): The repository only contains an integration test for histogram generation, not the required `test_boxplot_generation`. Moreover, the expected artifact `reports/figures/boxplots.pdf` is missing, so the test cannot verify its existence or correctness. The task’s requirement is therefore not met.
- `T036` (rejected 1x): declared artifact(s) missing/empty/invalid: reports/figures/final_report.pdf
- `T037` (rejected 1x): The `code/analysis/generate_final_report.py` script is present and contains logic to load and abort on a blocked gate status, but the required `data/processed/gate_status.json` file is missing, so the script cannot be exercised to verify the abort behavior. The missing gate status file must be added for the task to be fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

