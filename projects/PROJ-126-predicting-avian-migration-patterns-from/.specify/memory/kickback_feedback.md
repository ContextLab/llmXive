# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No `config.py` file or its contents were provided; thus there is no evidence that paths, a random seed of 42, Lake Powell bounding‑box coordinates, and the required hyperparameters were actually defined. The task’s required artifact is missing.
- `T011` (rejected 1x): The `code/data_loader.py` contains only a stubbed fetch using a placeholder URL and does not implement a real download or raise `ConnectionError` on failure, and the required output file `data/raw/ebd_subset.csv` is missing. The task’s core requirements (actual data download, filtering, checksum verification, and file creation) are not satisfied.
- `T014` (rejected 1x): The repository contains a partially implemented `calculate_first_arrival_sweep` function that matches the required logic, but the expected output file `data/processed/first_arrival_sweep.csv` is missing, and the `save_first_arrival_results` function is truncated with no evidence it writes the results to the required path. The task is therefore not fully completed.
- `T015` (rejected 1x): The required output file `data/processed/first_arrival_sweep.csv` does not exist, and the provided `preprocessing.py` is incomplete (truncated save function) and never generates or validates that CSV. Consequently the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

