# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010a` (rejected 1x): No `test_features.py` file or `test_mixing_enthalpy` unit test is present, nor any test run output showing it passes after T014 & T015. The required artifact (the unit test) is missing, so the task is not satisfied.
- `T016a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/processed_alloys.csv
- `T016b` (rejected 1x): No artifact such as a processed CSV file, ingestion/feature‑engineering script, logs, or any evidence of the required 500‑row dataset with thermodynamic columns and `critical_cooling_rate` was provided. The claim lacks the concrete output needed to verify that the data validation step was completed.
- `T017` (rejected 1x): No code, script, test, or documentation was provided showing that a validation step was added to check that `critical_cooling_rate` has non‑zero variance and at least 500 entries, nor any error handling for the failure case. The required artifact (e.g., updated ingestion/validation module or a test confirming the check) is missing.
- `T020` (rejected 1x): The claim provides only a description of the required train‑test split but no actual artifact (e.g., code, notebook, or resulting split data) is present. There is no `processed_alloys.csv` loaded, no split performed, and no output showing the 80/20 split with `random_state=42`. The required evidence is missing.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/models/random_forest_model.pkl
- `T022b` (rejected 1x): No code, data files, or generated predictions were provided; the implementer only restated the specification without delivering the required null‑model baseline generation script, output CSV, or any prediction results. The task therefore lacks the essential artifacts to be considered complete.
- `T024a` (rejected 1x): No code, data files, or results were supplied; the implementer did not provide the required null‑model statistical test implementation, nor any accompanying scripts, outputs, or documentation. Consequently the task’s deliverable is missing.
- `T024c` (rejected 1x): No data ingestion script, output CSV, feature‑engineering code, model training script, saved model, or metrics report were supplied. Consequently the required artifacts (≥500‑row CSV with thermodynamic columns and critical_cooling_rate, logs, trained Random Forest model, and evaluation metrics) are missing, so the task is not satisfied.
- `T028` (rejected 1x): No `random_forest_model_stable.pkl` or any permutation‑importance results were provided, and the required `feature_importance.json` file is absent. Consequently there is no evidence that permutation importance was computed, p‑values were derived, or that a thermodynamic feature meets the top‑2 / p < 0.05 criterion. The implementer must supply the stable model, the computed importance data, and the JSON output meeting the specified conditions.
- `T031` (rejected 1x): No code, data, notebook, or results were provided for the required “Threshold‑Sweep Sensitivity Analysis.” The claim contains only a placeholder comment (“FAILED: unspecified”) and no artifact (e.g., script, plots, or report) that actually performs the analysis, so the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

