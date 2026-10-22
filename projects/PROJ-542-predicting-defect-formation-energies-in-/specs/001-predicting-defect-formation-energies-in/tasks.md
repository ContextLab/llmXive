# Tasks: Predicting Defect Formation Energies in Perovskites with Machine Learning

**Inputs**: `spec.md`, `plan.md`, the original research idea, existing artifacts, and reviewer feedback.  
All paths are relative to the project root and use the canonical `code/` directory for implementation files.

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T014 [US1] Define and validate a dedicated schema for the feature matrix.  
  *File:* `contracts/features.schema.yaml`  
  *Schema:* Requires the twelve compositional descriptor columns (`A_radius`, `A_electronegativity`, … `X_valence_electrons`) and a numeric `formation_energy`; no additional columns allowed.  
  *Verification:* `code/tests/test_features_schema.py` validates that the schema is syntactically correct and loads without error.

- [ ] T001 [US1] Document the runnable pipeline entry point and verify module wiring.  
  *Files:* `code/quickstart.md`, `code/pipeline/run.py`, `code/data/download.py`, `code/data/featurize.py`  
  *Verification:* Unit test `code/tests/test_pipeline_entry.py` imports `code.pipeline.run` and asserts that `run()` executes without raising an exception and returns a dict containing keys `raw_path`, `features_path`, and `model_path`.

- [ ] T002 [US1] Implement the real data‑acquisition step: fetch perovskite oxygen‑vacancy defect formation energies from the Materials Project API (via `mp_api`).   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  *File:* `code/data/download.py`  
  *Requirements:*  
  • Abort with clear error `"Materials Project API key not provided"` if `MP_API_KEY` env‑var is missing.  
  • Abort with `"No data found for specified filters."` if the API query returns zero records.  
  • If the API cannot be reached, raise the exception (do **not** fall back to synthetic data).  
  • Compute SHA-256 checksum for the output file.  
  *Output:* `data/raw/materials_defects.csv`, `data/checksums/raw_defects.sha256`  
  *Verification:* Script exits with status 0, the CSV validates against `contracts/raw_dataset.schema.yaml`, and the row count is ≥ 500 (SC-005).

- [ ] T003 [US1] Implement featurization using `pymatgen`.  
  *File:* `code/data/featurize.py`  
  *Requirements:*  
  • Compute atomic radius, Pauling electronegativity, oxidation state, and valence electron count for A, B, X sites (12 descriptor columns).  
  • Drop rows where oxidation states cannot be determined; log the count in `featurize.log`.  
  • After dropping, abort with error `"Descriptor gaps detected – see descriptor_gaps.log"` if any descriptor remains missing.  
  • Compute SHA-256 checksum for the output CSV.  
  *Outputs:* `data/processed/features.csv`, `data/processed/featurize.log`, `data/processed/descriptor_gaps.log`, `data/checksums/features.sha256`  
  *Verification:* `features.csv` validates against `contracts/features.schema.yaml` (defined in T014) and contains no missing target values.

- [ ] T004 [US1] Validate the processed dataset and perform a lightweight power‑analysis warning.  
  *File:* `code/data/validate.py`  
  *Requirements:*  
  • Raise `ValueError` with message `"Insufficient rows (<50) for 5‑fold CV"` if the feature matrix has fewer than 50 rows (FR-009).  
  • Log the total row count and, if the count is < 500, emit a warning that the power target (≥ 500 rows) is not met (SC-005).  
  • Compute SHA-256 checksum for the output log.  
  *Output:* `data/processed/validation.log`, `data/checksums/validation.sha256`  
  *Verification:* Log file contains the row count and, when applicable, the warning message; unit test checks for correct handling of both thresholds.

- [ ] T005 [US1] Implement the SHA-256 checksum utility.  
  *File:* `code/utils/checksum.py` (exposes `write_checksum(path: str, out_dir: str)`).  
  *Verification:* pytest `code/tests/test_checksums.py` verifies that the utility correctly hashes files and writes the result to the specified output directory.

- [X] T012 [P] Create a pinned `requirements.txt` for the project.  
  *File:* `code/requirements.txt`  
  *Contents:*  
  ```text
  python==3.11
  pymatgen==2024.6.10
  mp-api==0.33.0
  pandas==2.2.2
  numpy==1.26.4
  scikit-learn==1.5.0
  matplotlib==3.9.0
  seaborn==0.13.2
  pytest==8.2.2
  tqdm==4.66.2
  statsmodels==0.14.2
  ```  
  *Verification:* `pip install -r code/requirements.txt` succeeds in a fresh virtual environment and all imports used in the code resolve.

## Phase 2 – Complete the study and validate its evidence  

- [ ] T006 [US1] Perform a deterministic, composition‑aware train/test split (80 % / 20 %).  
  *File:* `code/models/split.py` (uses `GroupShuffleSplit` with `random_state=42`).  
  *Requirements:* Compute SHA-256 checksums for both output CSVs.  
  *Outputs:* `data/processed/train.csv`, `data/processed/test.csv`, `data/processed/split.log`, `data/checksums/train.sha256`, `data/checksums/test.sha256`  
  *Verification:* Unit test asserts that no `composition` appears in both files and that the split respects the requested proportion.

- [ ] T007 [US2] Train baseline models (Random Forest and Gradient Boosting) with 5‑fold GroupKFold cross‑validation on `train.csv`.  
  *File:* `code/models/train.py`  
  *Requirements:*  
  • `n_jobs=1`, `random_state=42`.  
  • Write per‑model mean ± std metrics to `data/processed/cv_metrics.json`.  
  • Compute SHA-256 checksum for the metrics JSON.  
  • Serialize the fitted models to `models/rf_cv.pkl` and `models/gb_cv.pkl`.  
  *Verification:* `cv_metrics.json` conforms to the `cv_metrics` portion of `contracts/model_performance.schema.yaml`; a pytest checks the JSON structure and that both model files exist.

- [ ] T008 [US3] Evaluate the best‑performing model on the held‑out test set and produce a full performance report.  
  *File:* `code/models/evaluate.py`  
  *Steps:*  
  1. Load the model with the lowest mean CV RMSE.  
  2. Predict on `test.csv` and compute RMSE, MAE, R².  
  3. Bootstrap 10,000 resamples of the residuals to obtain a 95 % confidence interval for RMSE.  
  4. Perform a paired two‑sided t‑test (α = 0.05) between predictions and DFT values.  
  5. Write `data/processed/performance.json` containing **cv_metrics**, **test_metrics**, **bootstrap_ci**, **paired_ttest**, and a placeholder `feature_importances`.  
  6. Compute SHA-256 checksum for the performance JSON.  
  7. Generate `figures/pred_vs_actual.png` (scatter with 1:1 line).  
  *Decision rule:* If **RMSE > 0.5 eV** **or** **R² < 0.70**, set a flag `fallback_needed=True` inside the JSON; otherwise `fallback_needed=False`.  
  *Verification:* JSON validates against the full `contracts/model_performance.schema.yaml`. The task **MUST fail** if the paired t-test p-value is ≤ 0.05 (SC-003).

- [ ] T009 [US3] Populate the feature‑importance section of the performance report and finalize the importance figure.  
  *File:* `code/models/feature_importance.py` (reads the selected model’s `feature_importances_`, normalises to sum = 1, sorts descending).  
  *Outputs:* Updated `data/processed/performance.json` (adds `feature_importances` array), updated `data/checksums/performance.sha256`, and `figures/feature_importance.png` (bar chart).  
  *Verification:* The JSON now passes the `feature_importances` schema; the PNG file exists and the test `code/tests/test_feature_importance.py` confirms that the top‑3 features match the model’s ranking.

- [ ] T015 [US3] Implement structural‑descriptor augmentation (fallback pathway, FR‑012).  
  *File:* `code/data/augment_structural.py`  
  *Trigger:* Executed only when `fallback_needed=True` in `performance.json`.  
  *Requirements:* Compute for each composition: coordination numbers, average bond lengths, and crystal‑symmetry class using `pymatgen`. Compute SHA-256 checksum for the output.  
  *Output:* `data/processed/features_augmented.csv`, `data/checksums/features_augmented.sha256`  
  *Verification:* The CSV contains all original columns plus the new ones; it validates against an expanded version of the feature schema.

- [ ] T016 [US3] Re‑run the modelling pipeline using the augmented feature set.  
  *Procedure:*  
  1. Replace `features.csv` with `features_augmented.csv`.  
  2. Re‑execute T006 → T007 → T008 → T009 automatically from a driver script `code/pipeline/run_fallback.py`.  
  3. Overwrite `data/processed/performance.json` and figure files with the updated results.  
  *Verification:* Final `performance.json` reflects metrics computed on the augmented model; the fallback flag is now `fallback_needed=False`. All contract tests pass.

- [ ] T010 [US1] Assemble the reproducible Jupyter notebook that orchestrates the full pipeline end‑to‑end, including optional fallback.  
  *File:* `code/pipeline.ipynb`  
  *Requirements:*  
  • Import utilities and set fixed random seeds.  
  • Run `download.py` → `featurize.py` → `validate.py` → `split.py` → `train.py` → `evaluate.py` → `feature_importance.py`.  
  • Conditional block that calls `augment_structural.py` and repeats modelling steps if needed.  
  • Generate `data/logs/runtime.log` containing the total wall-clock time for the entire execution.  
  *Verification:* Executing the notebook from a clean environment reproduces **all** artefacts. The verification script `code/tests/test_pipeline_audit.py` must assert: (1) `runtime.log` ≤ 1800s (SC-004), and (2) random seeds in the notebook match the seeds used in the scripts (FR-010).

- [ ] T011 [US1] Write the methods & results markdown that will be handed off to the paper‑stage.  
  *File:* `paper/methods_results.md`  
  *Contents:*  
  • Summary of data source (Materials Project API) with API version and MP IDs.  
  • Description of descriptor calculation (list of 12 compositional descriptors, plus structural descriptors if fallback triggered).  
  • Table of cross‑validation metrics and held‑out test metrics (copied from `performance.json`).  
  • Figures `pred_vs_actual.png` and `feature_importance.png` embedded via relative links.  
  • Explicit statement whether the fallback augmentation was required.  
  *Verification:* A pytest `code/tests/test_methods_results.py` parses the markdown and checks that all required sections and figure links are present.