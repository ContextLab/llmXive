# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T023` (rejected 1x): The `process_batch` function in `code/metrics.py` is cut off before the CSV writing step (`output_file = Path(outpu`), so it never writes the required `metrics.csv`. Consequently the expected output file does not exist, and the integration test cannot pass. The implementation and/or test need to be completed.
- `T029` (rejected 1x): The `code/evaluator.py` file is truncated (ends with “lo” and does not contain the full `run_stratified_split` implementation), and the `tests/unit/test_evaluator.py` file is also cut off (missing the end of the second test and thus is syntactically invalid). Because the core function and its verification test are incomplete, the required behavior of writing `train_metrics.csv` and `test_metrics.csv` with correct label balance is not demonstrably satisfied. The missing/partial artifacts must be completed and the tests fixed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

