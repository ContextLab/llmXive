# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): The required output files `data/processed/eligible_subjects.csv` and `data/processed/excluded_subjects.log` are missing, and the generated `data/artifacts/data_gate_status.json` records a download error (failed DNS resolution) with zero eligible/excluded counts, indicating the script never completed the filtering and output steps. The task’s core requirements are therefore not satisfied.
- `T018` (rejected 1x): The repository lacks the required `data/processed/eligible_subjects.csv` file, so the script cannot load the subject list as specified. Moreover, the provided `code/02_preprocess_and_parcellate.py` is truncated and shows no implementation of normalization, atlas fetching, or connectivity matrix calculation/output. These missing pieces mean the task’s functional requirements are not met.
- `T019` (rejected 1x): The repository contains `code/03_compute_graph_metrics.py`, but the script is truncated and does not show the logic that iterates over subjects, computes the required metrics, monitors peak RAM, and writes the results to `data/processed/graph_metrics.csv`. Moreover, the expected output file `data/processed/graph_metrics.csv` is absent. The required CSV output and full implementation are missing.
- `T024` (rejected 1x): The repository contains `code/05_evaluate_model.py`, but the file is truncated and does not show the logic that computes ROC‑AUC, accuracy, F1‑score per fold and writes the results. Moreover, the required output `data/processed/performance_report.json` is absent. The task’s core deliverable is therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

