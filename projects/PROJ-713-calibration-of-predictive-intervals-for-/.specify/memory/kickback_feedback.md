# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): The provided `code/evaluation/runner.py` file exists, but the excerpt stops before showing any logic that writes `results/coverage.csv` and `results/distributional_metrics.csv` with the required columns, nor does it demonstrate the specified error‑handling behavior. Moreover, the expected result CSV files are absent from the repository, so we cannot confirm that the implementation fulfills the output requirements. The next implementer should ensure the script writes the two CSVs with the exact column set and implements the per‑series vs. global error handling as described.
- `T032` (rejected 1x): The repository lacks a `write_significance_results` function in `code/evaluation/runner.py` (the provided excerpt ends before any such implementation) and the required output file `results/significance_test.csv` does not exist. Both the code artifact and the serialized results are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

