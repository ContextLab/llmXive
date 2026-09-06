# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012` (rejected 1x): The provided `baseline_nn.py` defines a heteroscedastic network with two hidden layers and correctly stays under 10 k parameters, but it lacks any code that computes the total parameter count, asserts the ≤10 000 limit before saving, and actually saves a checkpoint. Consequently the required artifact `results/models/baseline_seed42.pt` is missing. The task’s verification and output steps are not implemented.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: results/uq_predictions_base.csv
- `T016b` (rejected 1x): The repository contains a `code/main.py` file, but it is truncated (the `run_pipeline` function is incomplete) and does not demonstrate the required wait‑for‑T013/T014 logic, global timeout enforcement, or merging of T016a outputs into `results/uq_predictions_base.csv`. Moreover, the expected output file `results/uq_predictions_base.csv` is absent. These missing pieces prevent the task from being considered fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

