# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014a` (rejected 1x): The repository lacks the required `data/results/test_data_polynomial.npy` file, and the `src/experiments/baseline_runner.py` source shown does not contain an implementation of the `load_test_data` function (or any code that loads that file). Consequently the task’s core requirement—providing a working `load_test_data` that returns `X_test, y_test` from the specified NumPy file—is not satisfied. The missing data file and absent function must be added for the task to be complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

