# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012a` (rejected 1x): The repository lacks the required data files (`data/processed/filtered_splits.json`, `exclusion_log.json`, and the output `entropy_results.csv`). Moreover, the provided `entropy.py` is truncated and does not contain the full pipeline (clustering, entropy calculation, logging, and direct CSV output). These missing artifacts and incomplete implementation mean the task is not genuinely completed.
- `T019` (rejected 1x): The repository lacks the required input CSVs (`entropy_results.csv`, `convergence_results.csv`) and the expected output files (`router_model.pkl`, `router_metrics.json`). Moreover, the provided `analysis.py` is truncated and does not contain the logistic regression training, model saving, or metric generation logic required by the task.
- `T022` (rejected 1x): The required `data/processed/router_results.csv` file does not exist, so the integration cannot be verified. Moreover, the provided `code/src/analysis.py` snippet shows no implementation that reads or reports on a CSV with the schema `{task_id, predicted_k, actual_k, accuracy, flops_saved}`. Both the data artifact and the corresponding code update are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

