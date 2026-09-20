# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The `metrics.py` file contains a stub `compute_mcnemar_test` but never integrates its result into the benchmark output, and the script’s `main` is incomplete (truncated). Moreover, the required `data/results/benchmark_results.csv` file does not exist, so there is no `p_value` column with float values. The task’s core output is missing.
- `T019b` (rejected 1x): The required `data/results/benchmark_results.csv` file is missing, and the accompanying `benchmark_result.schema.yaml` is also absent. The provided `exclusion_log.json` does not contain the expected keys (`total_scenes` and `excluded_count`) needed for the verification script. Consequently, the task’s output and validation requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

