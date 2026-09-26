# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): The provided `code/logging_config.py` is present but its implementation is truncated and does not show the logic that actually writes the header row to `results/quality_report.csv`. Moreover, the required files `code/logs/preprocess.log` and `results/quality_report.csv` are absent, and no test/assertion evidence of their creation and correct columns is supplied. The task therefore remains unfinished.
- `T002d` (rejected 1x): declared artifact(s) missing/empty/invalid: state/test_artifacts.yaml
- `T013` (rejected 1x): The repository lacks a `config.yaml` file, so the script cannot be configured as required. Moreover, the provided `load_data.py` excerpt shows functions for loading and normalizing data but does not include any code that writes the unified CSV (`timestamp`, `x`, `y`, `pupil_diameter`) to `data/processed/unified_eye_tracking.csv` or demonstrates using the config to locate source files. These essential pieces are missing.
- `T016` (rejected 1x): The repository contains a `code/analysis/correlations.py` file, but the shown content is truncated and does not demonstrate implementation of Benjamini‑Hochberg FDR correction or CSV output. Moreover, the required `results/correlations.csv` file is absent. Consequently, the task’s deliverables are not fully present.
- `T017` (rejected 1x): The repository contains `code/preprocessing/filter.py` with helper functions for initializing and appending to `results/quality_report.csv`, but there is no evidence that these functions are actually invoked, and the expected `results/quality_report.csv` file is absent. Consequently the required quality‑report generation is not demonstrated.
- `T023` (rejected 1x): No code, script, or output implementing the likelihood‑ratio test for comparing nested models is present; the only material is the task description and specifications, with no concrete artifact to verify. The required implementation artifact is missing.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: config.yaml
- `T029` (rejected 1x): The `results/limitations.md` file correctly contains the required limitation note, but the required `results/classification_metrics.csv` file is missing, so the status column cannot be set to `UNVALIDATED` as specified. The implementer must add this CSV (with a `status` column set to `UNVALIDATED`).
- `T032` (rejected 1x): No artifact (e.g., plot, CSV, or script) showing the continuous correlation between predicted probability and search time is present; the only material is the task description, which does not satisfy the requirement for a concrete output. The implementer must provide the actual correlation output (e.g., a figure or data file).

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

