# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No `setup_dirs.sh` script was provided, nor any evidence (file listing, script contents, or execution output) showing that it creates the required directory tree and is executable. The task’s core deliverable is therefore missing.
- `T023` (rejected 1x): No code, data files, training logs, performance metrics, statistical test results, or interpretability analyses were provided. The required artifacts (ingestion/preprocessing pipeline, model training/evaluation outputs, and ablation study results) are missing, so the task is not satisfied.
- `T025b` (rejected 1x): No code, data, or report implementing a post‑hoc power analysis was provided, and the supplied project excerpt only describes data ingestion, model training, and interpretability—not a power‑analysis component. Consequently the required artifact is missing and the task’s core requirement is not met.
- `T031` (rejected 1x): No artifact (e.g., a generated comparative report, notebook, PDF, or data file) was provided that maps GNN‑identified substructures to the Random Forest descriptor importance. Without such a document or output, the requirement of FR‑009 is not satisfied. The implementer must produce the comparative report containing the mapping and any supporting visualizations or tables.
- `T032` (rejected 1x): No evidence of any files in `results/figures/` was provided; the claim lacks the required heatmap or bar‑chart visualizations of feature importance. The implementer must add the actual figure files (non‑empty images) in the specified directory.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

