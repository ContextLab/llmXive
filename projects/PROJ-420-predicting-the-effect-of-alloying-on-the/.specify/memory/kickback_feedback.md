# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024` (rejected 1x): The provided `code/modeling.py` does not contain any logic that creates the `models/` directory or calls `joblib.dump(model, ..., compress=3, protocol=3)` to write `rf_model.pkl`, and the expected output file `models/rf_model.pkl` is absent from the repository. Consequently the task’s serialization requirement is not satisfied.
- `T023c` (rejected 1x): The provided `code/modeling.py` does not contain any logic that computes `cv_mae`, compares it to 0.05, sets a `mae_flag`, logs the required warning, or writes the specified JSON file. Moreover, `data/processed/model_metrics.json` is absent from the repository. Both the flagging implementation and the required output artifact are missing.
- `T025b` (rejected 1x): The required `data/processed/model_metrics.json` file does not exist, and the provided `code/modeling.py` excerpt shows no implementation that writes a JSON with the specified schema (`cv_mae`, `test_mae`, `std_dev`, `mae_flag`, `threshold`). Consequently the task’s logging requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

