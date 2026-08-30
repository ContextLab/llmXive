# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012` (rejected 1x): The repository contains `code/models/baseline_nn.py`, but the required output file `results/models/baseline_seed42.pt` is missing, so the training artifact was never saved. Additionally, the implementation does not ensure the model stays ≤10 k parameters (the hidden sizes are fixed but the input dimension could push the total count above the limit). The task is therefore not fully satisfied.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: results/uq_predictions.csv
- `T014` (rejected 1x): The `results/models/mc_dropout_model.pt` file does not exist, and the provided `code/models/mc_dropout.py` contains bugs (e.g., returns undefined `mo`) and lacks a function that performs multiple stochastic forward passes as required. The implementation is therefore incomplete.
- `T022b` (rejected 1x): declared artifact(s) missing/empty/invalid: results/uq_predictions.csv
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: results/calibration_report.csv
- `T025a` (rejected 1x): declared artifact(s) missing/empty/invalid: results/ece_scores_by_seed.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

