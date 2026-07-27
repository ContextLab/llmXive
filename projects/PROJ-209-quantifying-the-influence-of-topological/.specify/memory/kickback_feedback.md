# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository lacks the required `data/state/source_validation.json` file, so the script cannot perform the mandated source‑validity check. Moreover, the provided `code/01_data_acquisition.py` is truncated and shows no code that actually reads or processes that JSON, indicating the Step 3 implementation is absent. The missing JSON and incomplete script must be added/fixed for the task to be satisfied.
- `T013` (rejected 1x): The repository lacks the required `data/state/generation_status.json`, `data/raw/synthetic_train.csv`, and `data/state/synthetic_config.json` files, and the provided `code/01_data_acquisition.py` (truncated) shows no implementation of the synthetic data generation logic described in the task. The script therefore does not fulfill the step‑4 requirements nor produce the guaranteed output files.
- `T016a` (rejected 1x): The required output artifacts `data/state/exclusion_log.json`, `data/state/data_source.json`, and `data/raw/pristine_structures.csv` are absent, and the provided `code/01_data_acquisition.py` snippet is incomplete and does not demonstrate the required validation, filtering, and logging logic. The task’s core functionality is therefore not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

