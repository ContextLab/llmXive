# Tasks: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers  

**Inputs**: `spec.md`, `plan.md`, reviewer feedback, and any existing artifacts.

The tasks below constitute a complete, end‑to‑end research pipeline that satisfies every functional requirement (FR‑001 – FR‑015) and success criterion (SC‑001 – SC‑006).  They are ordered to respect data flow and computational dependencies.  All paths are project‑owned and will be created under `code/`, `data/`, `figures/`, `models/`, or `reports/`.

---

## Phase 0 – Feasibility & Data‑source Verification  

- [ ] T001 [P?] [US1] Verify that **each** required open dataset (NIST, Zenodo, Materials Project) contains **all** required variables (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`, `treatment_type`, `pair_id`).   <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 -->
  - **Implementation**: `code/verify_data_source.py` loads the three datasets via their public URLs (wget/curl), inspects column sets, and writes a JSON report `data/source/availability_report.json`.  
  - **Verification**: CI fails if any dataset is missing one or more required columns; otherwise the task passes.

---

## Phase 1 – Data Acquisition & Integrity  

- [ ] T002 [P?] [US1] Download the three verified raw datasets and store each as a canonical CSV (`data/raw/nist.csv`, `data/raw/zenodo.csv`, `data/raw/materials_project.csv`). Then merge them into a unified file `data/raw/adhesion_raw.csv`.   <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 -->
  - **Implementation**: `code/download_data.py` reads `availability_report.json`, streams each source, writes individual CSVs, concatenates them (adding a `source` column), and creates a SHA‑256 checksum file `data/raw/checksums.txt`.  
  - **Verification**: All three source CSVs and the merged `adhesion_raw.csv` must exist, be non‑empty, and their checksums must match entries in `checksums.txt`.  

- [ ] T003 [P?] [US1] Generate per‑source unit‑metadata JSON files and enforce unit consistency across the merged dataset.  
  - **Implementation**: `code/generate_units_metadata.py` parses `adhesion_raw.csv`, produces `data/raw/adhesion_units.json` mapping each numeric column to its declared SI unit, and raises `UnitMismatchError` on any inconsistency.  
  - **Verification**: The JSON file must be present and the script must exit with status 0 (no exception).  

---

## Phase 2 – Ingestion & Pre‑processing  

- [ ] T004 [P?] [US1] Parse raw files, convert all numeric fields to SI, canonicalise `treatment_type`, one‑hot encode categorical fields (`treatment_type`, `pair_id`), median‑impute missing numeric values *per substrate class*, and flag low‑coverage columns.   <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 -->
  - **Implementation**: `code/preprocess.py` writes the cleaned dataset `data/cleaned/cleaned.csv`.  
  - **Verification**:  
    - `cleaned.csv` contains exactly the columns defined in the `TreatmentRecord` schema with **no missing values** in required fields.  
    - Imputation details are recorded in `data/cleaned/imputation_log.json`.  
    - Field‑coverage percentages are stored in `data/cleaned/field_coverage.json`; any column < 80 % is marked `"low_coverage": true`.  

---

## Phase 3 – Train‑Validation‑Test Split  

- [ ] T005 [P?] [US2] Perform a **grouped** split by `pair_id` (70 % train, 15 % validation, 15 % test) while **excluding** any polymer‑substrate group with fewer than 5 records (FR‑011). If the resulting validation set contains fewer than 30 records, **re‑sample** from the training set to meet a minimum validation size of 30 records (ensuring a usable CI).  
  - **Implementation**: `code/split_dataset.py` writes `data/split/train.csv`, `data/split/val.csv`, `data/split/test.csv`, plus a summary `data/split/split_summary.json`.  
  - **Verification**:  
    - Each split respects the 70/15/15 proportion within 1 % tolerance (after any necessary re‑sampling).  
    - No group with < 5 records appears in any split.  
    - The summary JSON reports record counts, number of excluded groups, and confirms that `val.csv` has ≥ 30 records.  

---

## Phase 4 – Model Training, Hyper‑parameter Search & Selection  

- [ ] T006 [P?] [US2] Grid‑search ≤ 50 hyper‑parameter combinations across three regressors (Random Forest, Gradient Boosting, Linear Regression) on the **training** set; evaluate each on the **validation** set; compute validation R², RMSE, and a **95 % bootstrapped confidence interval** for R².  
  - **Implementation**: `code/train_models.py` saves every trained model under `models/` (e.g., `models/rf_001.pkl`) and writes `models/grid_search_results.json` containing metrics and CI bounds.  
  - **Verification**:  
    - The script finishes within the 3.5 h CPU limit.  
    - Every entry in `grid_search_results.json` includes non‑null `validation_r2`, `validation_rmse`, and `r2_ci_95` (a two‑element list of numbers).  

- [ ] T007 [P?] [US2] Compute **grouped k‑fold (by `pair_id`) cross‑validated R²** for each model, then select the **best** model. Selection criteria: highest mean CV R² **and** validation‑R² lower‑CI ≥ 0.5. If no model meets the CI threshold, set `"null_result": true` with reason `"validation CI < 0.5"`. Write `models/best_model.json` with all relevant fields (`model_type`, `hyperparameters`, `validation_r2`, `validation_rmse`, `cv_r2_mean`, `cv_r2_std`, `null_result`, `reason?`).  
  - **Verification**: `best_model.json` must exist, be valid JSON, and contain the fields listed above. When `null_result` is true, the file must also include the `reason` field.  

- [ ] T008 [P?] [US2] Evaluate **all three** trained models on the **test** set; produce a `ModelArtifact` JSON for each under `models/` (e.g., `models/rf_artifact.json`). Copy the best model’s test metrics into `models/best_model.json`.  
  - **Verification**: Each artifact JSON validates against `contracts/model_artifact.schema.yaml`. The best‑model entry in `best_model.json` matches the corresponding artifact’s `test_r2`, `test_rmse`, and `test_mae`.  

---

## Phase 5 – Statistical Significance  

- [ ] T009 [P?] [US3] Run a permutation test with exactly **1 000 shuffles** of the target on the best model’s test set to obtain an empirical p‑value for the observed R².  
  - **Implementation**: `code/perm_test.py` writes the numeric value to `results/permutation_p_value.txt`.  
  - **Verification**: The file must exist, contain a floating‑point number, and CI asserts that the value is **< 0.05** for a “significant” finding; if ≥ 0.05 the final report must flag a null result.  

- [ ] T010 [P?] [US3] Compute per‑predictor significance (p < 0.05) using linear‑model coefficients (when a Linear Regression model is available) and write `results/per_predictor_significance.json`.  
  - **Implementation**: `code/per_predictor_significance.py` extracts coefficients, estimates standard errors via `statsmodels`, and records p‑values per feature.  
  - **Verification**: JSON maps each feature name to a numeric p‑value; CI checks that at least one feature meets p < 0.05 when the overall model is significant.  

---

## Phase 6 – Interpretability & Stability  

- [ ] T011 [P?] [US3] Generate SHAP values for the best model, produce a summary plot PNG, and save a feature‑ranking JSON. Use `shap.TreeExplainer` for tree‑based models; fall back to `shap.LinearExplainer` or `shap.KernelExplainer` for linear models (FR‑015).  
  - **Implementation**: `code/shap_analysis.py` outputs `figures/shap_summary.png` and `results/shap_feature_ranking.json`.  
  - **Verification**: Both files must exist, the PNG must be a valid image, and the JSON must list features with their mean absolute SHAP values.  

- [ ] T012 [P?] [US3] Assess SHAP‑value stability across the k‑fold CV folds used in T007; compute the standard deviation of mean absolute SHAP values across folds. If the number of folds with valid SHAP values is < 3, record `"std_mean_shap": null` and note that stability could not be assessed. Otherwise require `< 0.1`. Write `results/shap_stability.json`.  
  - **Verification**: The JSON contains a key `std_mean_shap`; CI passes when the value is `< 0.1` or is `null` with an explanatory note.  

- [ ] T013 [P?] [US3] Produce the four required visualizations for the best model:  
    1. Predicted‑vs‑actual scatter (`figures/predicted_vs_actual.png`)  
    2. Residual histogram (`figures/residual_histogram.png`)  
    3. SHAP summary plot (already generated in T011)  
    4. Parameter‑response curves (`figures/parameter_response_curves.png`)  
  - **Implementation**: `code/visualizations.py` creates all PNGs in a single run.  
  - **Verification**: Each PNG must exist, be readable, and have file size > 0 bytes.  

---

## Phase 7 – Report Assembly & Contract Validation  

- [ ] T014 [P?] [US3] Assemble the final analysis report in both JSON (`reports/analysis_result.json`) and Markdown (`reports/analysis_result.md`). The JSON must conform exactly to `contracts/analysis_result.schema.yaml`; the Markdown must embed hyperlinks to the four PNG visualizations, summarize R² (with 95 % CI), RMSE, MAE, permutation p‑value, top‑3 SHAP predictors, per‑predictor significance (from T010), and include a clear “null‑result” notice when `null_result: true`.  
  - **Verification**: CI runs JSON‑schema validation against `analysis_result.schema.yaml` and checks that the Markdown contains the required sections and image links.  

- [ ] T015 [P?] [S1] Validate **all** output artifacts against their respective contracts and generate a consolidated SHA‑256 manifest `state/project_checksum_report.yaml`.  
  - **Implementation**: `code/validate_and_checksum.py` iterates over every artifact (CSV, JSON, PNG, PKL), validates schema where applicable, computes SHA‑256 hashes, and writes the manifest.  
  - **Verification**: Script exits with status 0 only if every artifact passes schema validation and the recorded hashes match the computed values.  

- [ ] T016 [P?] [S1] Measure total wall‑clock time for the entire pipeline and assert it does not exceed **6 hours**.  
  - **Implementation**: `code/measure_runtime.py` wraps the full run (e.g., via `python -m llmxive_toolkit.run_all`), writes elapsed seconds to `data/runtime/total_seconds.txt`.  
  - **Verification**: CI fails if the recorded value > 21600 seconds.  

---

## Phase 8 – Documentation & Reproducibility  

- [ ] T017 [P?] [S1] Write `docs/quickstart.md` containing a reproducible command (`python -m llmxive_toolkit.run_all`) and a post‑run checksum verification step for `reports/analysis_result.json`. The document must also list the required Python version and package versions (as in `requirements.txt`).  
  - **Verification**: After a fresh clone, running the command described in `quickstart.md` must complete successfully and the checksum comparison must succeed (CI executes the command in an isolated environment).  

---  

*All unchecked tasks must be completed and pass their verification steps before the project can advance to the paper‑hand‑off stage.*  