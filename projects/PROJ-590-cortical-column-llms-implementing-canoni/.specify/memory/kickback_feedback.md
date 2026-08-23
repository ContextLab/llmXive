# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008c` (rejected 1x): The repository lacks the required `generate_polynomial_test_data` implementation (no such function appears in `src/data/benchmarks.py`) and the expected output file `data/results/test_data_polynomial.npy` is absent. Both the code artifact and the generated data file are missing, so the task is not fulfilled.
- `T010b` (rejected 1x): The repository lacks a `log_gradient_norms` function in `src/training/homeostasis.py` (the file is truncated and does not define it), and the required output file `data/logs/gradient_norms.json` does not exist. Consequently the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

