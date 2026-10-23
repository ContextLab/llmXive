# Tasks: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers  

**Inputs**: `spec.md`, `plan.md`, reviewer feedback, and any existing artifacts.

The tasks below constitute a complete, end‑to‑end research pipeline that satisfies every functional requirement (FR‑001 – FR‑015) and success criterion (SC‑001 – SC‑006).  They are ordered to respect data flow and computational dependencies.  All paths are project‑owned and will be created under `code/`, `data/`, `figures/`, `models/`, or `reports/`.  Every task is unchecked; tasks that previously failed (T001‑T004) have been reopened with corrected specifications.

---

## Phase 0 – Feasibility, Data‑source Verification & Early Smoke Test  

- [ ] T001 [P?] [US1] **Download and verify required open datasets** (NIST, Zenodo, Materials Project).   <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 -->
  - **Implementation**: `code/download_and_verify.py` uses `wget`/`curl` to fetch each dataset, checks that all required columns (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`, `treatment_type`, `pair_id`) are present, writes each raw CSV to `data/raw/nist.csv`, `data/raw/zenodo.csv`, `data/raw/materials_project.csv`, and records a JSON verification report `data/source/availability_report.json`.  
  - **Verification**: CI fails if any dataset is missing a required column; otherwise the task passes.

- [ ] T002 [P?] [US1] **Merge verified raw datasets into a unified file**.  
  - **Implementation**: `code/merge_raw.py` reads the three raw CSVs produced by T001, adds a `source` column, concatenates them into `data/raw/adhesion_raw.csv`, and updates the checksum manifest `data/raw/checksums.txt`.  
  - **Verification**: `adhesion_raw.csv` must exist, be non‑empty, and its SHA‑256 hash must match the entry in `checksums.txt`.

- [ ] T003 [P?] [US1] **Generate unit‑metadata JSON and enforce consistency**.  
  - **Implementation**: `code/generate_units_metadata.py` parses `data/raw/adhesion_raw.csv`, produces `data/raw/adhesion_units.json` mapping each numeric column to its declared SI unit, and raises `UnitMismatchError` on any inconsistency.  
  - **Verification**: `adhesion_units.json` must be present and the script must exit with status 0 (no exception).

- [ ] T004 [P?] [US1] **Run a synthetic smoke‑test end‑to‑end** on the first 100 rows of `adhesion_raw.csv`.  
  - **Implementation**: `code/run_smoke_test.py` executes the full preprocessing, split, quick‑model training, and evaluation pipeline on the subset, writes the cleaned subset to `data/cleaned/cleaned_subset.csv`, the predictions to `data/results/smoke_test_output.csv`, and logs imputation details to `data/cleaned/imputation_log.json`.  
  - **Verification**:  
    - `smoke_test_output.csv` exists with columns `pair_id`, `actual_adhesion_strength_mj_m2`, `predicted_adhesion_strength_mj_m2`.  
    - `cleaned_subset.csv` contains **no missing values** in any required fields and reflects unit conversion and categorical canonicalisation.  
    - `imputation_log.json` is present.  
    - Script exits with status 0.

---

## Phase 1 – Full Data Acquisition & Integrity  

- [ ] T005 [P?] [US1] **Re‑run unit‑metadata generation** (if new data were added) and enforce unit consistency across the **merged** dataset.  
  - **Implementation**: Same script as T003; re‑run to ensure any newly added data are validated.  
  - **Verification**: `data/raw/adhesion_units.json` exists and no `UnitMismatchError` is raised.

- [ ] T006 [P?] [US1] **Verify checksums of all raw files** against `data/raw/checksums.txt` to guarantee data provenance.  
  - **Implementation**: `code/verify_checksums.py` recomputes SHA‑256 hashes and compares them to the manifest.  
  - **Verification**: Script exits with status 0 only if every hash matches.

---

## Phase 2 – Ingestion & Pre‑processing  

- [ ] T007 [P?] [US1] Parse raw files, convert all numeric fields to SI units, canonicalise `treatment_type` using the taxonomy defined in the spec, one‑hot encode categorical fields (`treatment_type`, `pair_id`), median‑impute missing numeric values *per substrate class*, and flag low‑coverage columns.  
  - **Implementation**: `code/preprocess.py` writes the cleaned dataset `data/cleaned/cleaned.csv`.  
  - **Verification**:  
    - `cleaned.csv` contains exactly the columns defined in `contracts/treatment_record.schema.yaml` with **no missing values** in required fields.  
    - Imputation details are recorded in `data/cleaned/imputation_log.json`.  
    - Field‑coverage percentages are stored in `data/cleaned/field_coverage.json`; any column < 80 % is marked `"low_coverage": true`.

---

## Phase 3 – Grouped Train/Validation/Test Split  

- [ ] T008 [P?] [US2] Perform a **grouped** split by `pair_id` (70 % train, 15 % validation, 15 % test) while **excluding** any polymer‑substrate group with fewer than 5 records (FR‑011). Write the splits to `data/split/train.csv`, `data/split/val.csv`, `data/split/test.csv` and a summary `data/split/split_summary.json`.  
  - **Verification**:  
    - Each split respects the 70/15/15 proportion within 1 % tolerance.  
    - No excluded group appears in any split.  
    - `split_summary.json` reports record counts, number of excluded groups, and confirms that `val.csv` contains ≥ 30 records.

---

## Phase 4 – Model Training, Hyper‑parameter Search & Selection  

- [ ] T009 [P?] [US2] Grid‑search ≤ 50 hyper‑parameter combinations across three regressors (Random Forest, Gradient Boosting, Linear Regression) on the **training** set; evaluate each on the **validation** set; compute validation R², RMSE, and a **95 % bootstrapped confidence interval** for R².  
  - **Implementation**: `code/train_models.py` saves every trained model under `models/` (e.g., `models/rf_001.pkl`) and writes `models/grid_search_results.json` containing metrics and CI bounds.  
  - **Verification**:  
    - Script finishes within the 3.5 h CPU limit.  
    - Every entry in `grid_search_results.json` includes non‑null `validation_r2`, `validation_rmse`, and `r2_ci_95` (two‑element list).

- [ ] T010 [P?] [US2] Compute **grouped k‑fold (by `pair_id`) cross‑validated R²** for each model, then select the **best** model. Selection criteria: highest mean CV R² **and** validation‑R² lower‑CI ≥ 0.5. **If no model meets the CI threshold, the task fails** (non‑zero exit). Write `models/best_model.json` with all relevant fields (`model_type`, `hyperparameters`, `validation_r2`, `validation_rmse`, `cv_r2_mean`, `cv_r2_std`).  
  - **Verification**: `best_model.json` must exist, be valid JSON, and contain the listed fields. Task fails if CI < 0.5 for all candidates.

- [ ] T011 [P?] [US2] Evaluate **all three** trained models on the **test** set; produce a `ModelArtifact` JSON for each under `models/` (e.g., `models/rf_artifact.json`). Copy the best model’s test metrics into `models/best_model.json`.  
  - **Verification**: Each artifact JSON validates against `contracts/model_artifact.schema.yaml`. The best‑model entry in `best_model.json` matches the corresponding artifact’s `test_r2`, `test_rmse`, and `test_mae`.

---

## Phase 5 – Statistical Significance & Predictor‑level Tests  

- [ ] T012 [P?] [US3] Run a permutation test with exactly **1 000 shuffles** of the target on the best model’s test set to obtain an empirical p‑value for the observed R².  
  - **Implementation**: `code/perm_test.py` writes the numeric value to `results/permutation_p_value.txt`.  
  - **Verification**: The file must exist, contain a floating‑point number **< 0.05**; the task fails otherwise.

- [ ] T013 [P?] [US3] Compute per‑predictor significance (p < 0.05) using linear‑model coefficients (when a Linear Regression model is available) and write `results/per_predictor_significance.json`.  
  - **Implementation**: `code/per_predictor_significance.py` extracts coefficients, estimates standard errors via `statsmodels`, and records p‑values per feature.  
  - **Verification**: JSON maps each feature name to a numeric p‑value; CI checks that at least one feature meets p < 0.05 when the overall model is significant.

---

## Phase 6 – Interpretability & Stability  

- [ ] T014 [P?] [US3] Generate SHAP values for the best model, produce a summary plot PNG, and save a feature‑ranking JSON. Use `shap.TreeExplainer` for tree‑based models; fall back to `shap.LinearExplainer` or `shap.KernelExplainer` for linear models (FR‑015).  
  - **Implementation**: `code/shap_analysis.py` outputs `figures/shap_summary.png` and `results/shap_feature_ranking.json`.  
  - **Verification**: Both files must exist, the PNG must be a valid image, and the JSON must list features with their mean absolute SHAP values.

- [ ] T015 [P?] [US3] Assess SHAP‑value stability across the k‑fold CV folds used in T010; compute the standard deviation of mean absolute SHAP values across folds. **The task fails** if `std_mean_shap` is missing or ≥ 0.1. Write `results/shap_stability.json`.  
  - **Verification**: The JSON contains a key `std_mean_shap` with a numeric value < 0.1; otherwise the task exits with error.

- [ ] T016 [P?] [US3] Produce the four required visualizations for the best model:  
    1. Predicted‑vs‑actual scatter (`figures/predicted_vs_actual.png`)  
    2. Residual histogram (`figures/residual_histogram.png`)  
    3. SHAP summary plot (already generated in T014)  
    4. Parameter‑response curves (`figures/parameter_response_curves.png`)  
  - **Implementation**: `code/visualizations.py` creates all PNGs in a single run.  
  - **Verification**: Each PNG must exist, be readable, and have file size > 0 bytes.

---

## Phase 7 – Report Assembly & Contract Validation  

- [ ] T017 [P?] [US3] Assemble the final analysis report in both JSON (`reports/analysis_result.json`) and Markdown (`reports/analysis_result.md`). The JSON must conform exactly to `contracts/analysis_result.schema.yaml`; the Markdown must embed hyperlinks to the four PNG visualizations, summarize R² (with 95 % CI), RMSE, MAE, permutation p‑value, top‑3 SHAP predictors, per‑predictor significance (from T013), and include a clear “null‑result” notice when the pipeline fails a hard threshold.  
  - **Verification**: CI runs JSON‑schema validation against `analysis_result.schema.yaml` and checks that the Markdown contains the required sections and image links.

- [ ] T018 [P?] [S1] Validate **all** output artifacts against their respective contracts and generate a consolidated SHA‑256 manifest `state/project_checksum_report.yaml`.  
  - **Implementation**: `code/validate_and_checksum.py` iterates over every artifact (CSV, JSON, PNG, PKL), validates schema where applicable, computes SHA‑256 hashes, and writes the manifest.  
  - **Verification**: Script exits with status 0 only if every artifact passes schema validation and the recorded hashes match the computed values.

- [ ] T019 [P?] [S1] Measure total wall‑clock time for the entire pipeline and assert it does not exceed **6 hours**.  
  - **Implementation**: `code/measure_runtime.py` wraps the full run (e.g., via `python -m llmxive_toolkit.run_all`) and writes elapsed seconds to `data/runtime/total_seconds.txt`.  
  - **Verification**: CI fails if the recorded value > 21600 seconds.

---

## Phase 8 – Reproducibility & Seed Management  

- [ ] T021 [P?] [S1] **Enforce fixed random seeds** in all stochastic scripts (`preprocess.py`, `train_models.py`, `perm_test.py`, `shap_analysis.py`, etc.) and record the seed used in `data/seed_record.txt`.  
  - **Implementation**: `code/set_fixed_seeds.py` writes a constant seed (e.g., `42`) to `data/seed_record.txt` and updates each script to import a common `seed_manager` that sets `numpy`, `random`, and any library‑specific RNGs.  
  - **Verification**: Each script, when run, logs the seed value; the task fails if any script does not report the expected seed.

---

*All unchecked tasks must be completed and pass their verification steps before the project can advance to the paper‑hand‑off stage.*  