# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `projects/PROJ-324-predicting-molecular-properties-from-ope/` directory (or any files within it) was provided; the implementer’s claim cannot be verified without seeing the actual folder structure. The required artifact is missing.
- `T001b` (rejected 1x): No evidence was presented that the required `code/`, `data/`, and `tests/` subdirectories actually exist (or contain any files). The implementer only supplied a feature specification, not the filesystem artifacts needed to verify the task.
- `T001c` (rejected 1x): No evidence was provided showing that the `data/raw`, `data/processed`, and `data/derived` subdirectories actually exist in the repository (e.g., a directory listing or commit showing their creation). Without such proof, the requirement cannot be confirmed as satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a `ruff` section, or a pre‑commit hook file) were presented, nor any evidence that `ruff` and `black` have been installed or integrated into the project. The required artifacts are missing, so the task is not satisfied.
- `T009` (rejected 1x): The required output file `data/derived/data_quality_report.csv` does not exist, so the logging of excluded entries (including a `missing_covariate` column) is not realized. Moreover, the visible portion of `code/data/preprocess.py` shows only confidence filtering and generic missing‑value handling, with no evident logic for detecting missing covariates (e.g., temperature, pH) and recording them in the quality report. The task’s FR‑008 requirement is therefore unmet.
- `T031` (rejected 1x): The `data/raw/dataset_metadata.json` file does not exist, and the shown `code/data/download.py` contains no logic to record experimental source, measurement conditions, or source confidence in that metadata file. Both the required artifact and the necessary code enhancements are missing.
- `T014` (rejected 1x): The repository contains `code/models/baseline.py`, but the file is truncated in the provided view and there is no `data/derived/baseline_predictions.csv` generated (the file is missing). Since the task explicitly requires the script to compute Crippen contributions for all molecules **and** write the predictions to `data/derived/baseline_predictions.csv`, the essential output artifact is absent, so the requirement is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

