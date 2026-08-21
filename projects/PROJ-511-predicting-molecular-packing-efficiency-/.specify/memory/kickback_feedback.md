# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): The repository lacks the required `data/dataset_filtered.csv` and the resulting `data/dataset.csv` files, so the script cannot be run or produce the specified output columns. Moreover, the provided `add_3d_descriptors.py` is truncated and does not show implementation of asphericity calculation, CIF‑existence checks, or the final merge step. These missing artifacts and functionality mean the task is not genuinely completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

