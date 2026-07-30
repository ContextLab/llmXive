# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): The repository contains `code/02_preprocess_and_parcellate.py`, but the required input file `data/processed/eligible_subjects.csv` is missing, so the script cannot load the subject list or produce the connectivity matrices as specified. The task therefore is not fully satisfied.
- `T019` (rejected 1x): The repository contains `code/03_compute_graph_metrics.py`, but the script is truncated and does not show the part that writes results to `data/processed/graph_metrics.csv`. Moreover, the expected output file `data/processed/graph_metrics.csv` is missing entirely, so the required artifact is not produced. The task is therefore not fully satisfied.
- `T023` (rejected 1x): The repository contains `code/04_train_model.py`, but the required output artifacts (`data/processed/model.pkl`, `data/processed/cv_results.json`, `data/processed/model_params.json`) are absent, indicating the script has not been executed to produce the expected results. Without these files the task’s deliverables are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

