# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T003b` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml
- `T005e` (rejected 1x): The `capture_metrics()` function is present in `code/src/utils.py`, but the provided snippet ends before any code that records GPU metrics or writes the dictionary to `data/processed/resource_metrics.json`. Moreover, the required JSON file is missing from the repository. The task’s core requirement—to save the captured metrics to that file—is therefore not satisfied.
- `T012d` (rejected 1x): The provided `entropy.py` is truncated, lacks a `write_entropy_results` implementation (and the `log_exclusions` function is only a placeholder), and the required output files `data/processed/entropy_results.csv` and `data/processed/exclusion_log.json` do not exist. The task’s core functionality and artifacts are missing.
- `T013d` (rejected 1x): The provided `inference.py` file does not contain a `write_convergence_results` function (the snippet ends before any such implementation), and the required output file `data/processed/convergence_results.csv` is missing. Consequently, the task of logging convergence results is not fulfilled.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/router_accuracy_test.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

