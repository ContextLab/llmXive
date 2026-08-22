# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T020a` (rejected 1x): The test creates a CSV in the temporary `tmp_path` directory instead of saving it to `data/processed/sample_features.csv`, and the required file `data/processed/sample_features.csv` is missing from the repository. Consequently the task’s core requirement is not satisfied.
- `T020b` (rejected 1x): The required input file `data/processed/sample_features.csv` does not exist, and the expected output model file `results/model.pkl` is also missing. No test logs, execution traces, or generated artifacts are provided to show that the training pipeline was run and produced the model file. The task therefore is not satisfied.
- `T020c` (rejected 1x): The required artifact `results/metrics.json` does not exist on disk, so the unit test cannot verify the presence of the file nor the `test_rmse` numeric key. The implementer must create the file with a valid JSON object containing a numeric `test_rmse` entry.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

