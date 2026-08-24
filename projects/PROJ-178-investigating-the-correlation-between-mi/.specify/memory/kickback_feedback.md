# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/processed/mito_aging_dataset.csv
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: code/logs/exclusion_report.txt
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: code/data/processed/mito_aging_dataset.csv
- `T024` (rejected 1x): The repository contains a partially‑implemented `calculate_rank_ols` function (the file is truncated and never writes results), and the required output file `code/data/processed/rank_ols_results.csv` does not exist. Consequently the Rank‑OLS regression is not fully executed nor are the coefficients, p‑values, and adjusted p‑values saved as specified.
- `T044` (rejected 1x): No new test files are present in `code/tests/`; the claim of “additional unit tests for edge cases (zero burden, missing haplogroup)” cannot be verified because the required artifacts are missing. The next implementer must add concrete test cases covering these scenarios to the repository.
- `T045` (rejected 1x): The required artifact `code/logs/runtime_validation.log` does not exist, so the runtime was neither captured nor validated against the 6‑hour limit. The implementer must generate the log file with the recorded runtime and include the assertion check.
- `T046` (rejected 1x): No evidence of any files under `paper/figures/` was provided; the claim does not include the required final figures (linear fit plot and threshold‑sensitivity plot). The implementer must add the actual figure files in the specified directory.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

