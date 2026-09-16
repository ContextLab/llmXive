# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): No code, script, configuration, or output files were provided that demonstrate a validation step enforcing ≥ 80 % subject retention or handling missing behavioral data gracefully. The claim lacks any concrete artifact (e.g., a Python module, unit test, log output, or documentation) showing the required checks and error handling, so the task is not satisfied.
- `T019` (rejected 1x): The required `.npy` connectivity file does not exist, and `code/analysis/centrality.py` contains a stub `extract_connectivity_matrix_for_subject` that raises `NotImplementedError` instead of using `nilearn.connectome.ConnectivityMeasure` to compute and save the matrix. The task’s core functionality is therefore missing.
- `T020` (rejected 1x): The required output file `data/processed/centrality/subject_id_metrics.csv` does not exist, and the `code/analysis/centrality.py` script contains placeholder stubs (e.g., a NotImplementedError in `extract_connectivity_matrix_for_subject` and an incomplete `compute_centrality_metrics` function) with no logic to compute and save degree, betweenness, and eigenvector centralities for all ~90 regions. The implementation therefore does not meet the task’s specifications.
- `T021` (rejected 1x): The required output file `data/processed/behavioral/fd_mean.csv` does not exist, and the provided `code/analysis/centrality.py` contains only placeholder centrality‑related functions with no implementation for reading fMRIPrep confounds TSVs, computing framewise displacement, or writing the mean FD per subject. The task’s core requirement is therefore unmet.
- `T022` (rejected 1x): The repository lacks the required `data/processed/centrality/subject_id_metrics.csv` and the resulting `model_predictors.csv`. The `centrality.py` script is truncated and does not contain any VIF calculation, PCA fallback logic, or code to write the specified output file. Consequently, the task’s functional requirements are not met.
- `T024` (rejected 1x): The required output file `data/processed/regression/linear_model_summary.csv` does not exist, and the provided `regression.py` snippet is truncated before any regression fitting or CSV‑writing logic, so the task’s core requirement (run the model and save its summary) is not satisfied. The next implementer must ensure the script performs the conditional regression and writes the summary to the specified path.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

