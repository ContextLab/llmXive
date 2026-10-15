# Tasks: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers  

**Inputs**: `spec.md`, `plan.md`, reviewer feedback, and any existing artifacts.

The tasks below constitute a complete, end‑to‑end research pipeline that satisfies every functional requirement (FR‑001 – FR‑015) and success criterion (SC‑001 – SC‑006).  They are ordered to respect data flow and computational dependencies.  All paths are project‑owned and will be created under `code/`, `data/`, `figures/`, `models/`, or `reports/`.

---

## Phase 0 – Feasibility & Data‑source Verification  

- [ ] **T001** [S1] [US1] Verify that at least one openly downloadable dataset contains **all** required variables (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`, `treatment_type`, `pair_id`). <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_data_source.py exit=1 -->
  - *Implementation*: `code/verify_data_source.py` queries the NIST, Zenodo, and Materials Project APIs, downloads the dataset headers, and checks column presence.  
  - *Verification*: script writes a JSON report `data/source/availability_report.json` listing datasets that satisfy the requirement; CI fails if the list is empty, prompting a scope revision before any downstream work.

---

## Phase 1 – Data Acquisition & Integrity  

- [ ] **T002** [S1] [US1] Download the verified raw dataset(s) identified by T001 and record SHA‑256 checksums.
  - *Implementation*: `code/download_data.py` uses `wget`/`curl` with the concrete URLs from the availability report and saves files under `data/raw/<source>.csv`.  
  - *Verification*: script writes `data/raw/checksums.txt` (one line per file) and exits with status 0 only if every download succeeds and the computed checksum matches the recorded value.

- [ ] **T003** [S1] [US1] Generate per‑source unit‑metadata JSON files and validate unit consistency.  
  - *Implementation*: `code/generate_units_metadata.py` reads each raw CSV, creates `data/raw/<source>_units.json` mapping columns to declared SI units, and raises `UnitMismatchError` on any inconsistency.  
  - *Verification*: successful execution produces the JSON files; any raised error aborts the pipeline.

---

## Phase 2 – Ingestion & Pre‑processing  

- [X] **T004** [S1] [US1] Parse raw files, convert all numeric fields to SI, canonicalise `treatment_type`, one‑hot encode categorical fields (`treatment_type`, `pair_id`), median‑impute missing numeric values *per substrate class*, and flag low‑coverage columns.
  - *Implementation*: `code/preprocess.py` produces a single cleaned file `data/cleaned/cleaned.csv`.  
  - *Verification*:  
    - `data/cleaned/cleaned.csv` must contain exactly the columns defined in the `TreatmentRecord` schema with **no missing values** in required fields.  
    - Imputation details are recorded in `data/cleaned/imputation_log.json`.  
    - Field‑coverage percentages are stored in `data/cleaned/field_coverage.json`; any column < 80 % is marked `"low_coverage": true`.

---

## Phase 3 – Train‑Validation‑Test Split  

- [ ] **T005** [S2] [US2] Perform a grouped split by `pair_id` (70 % train, 15 % validation, 15 % test). Exclude polymer‑substrate groups with fewer than 5 records (FR‑011).  
  - *Implementation*: `code/split_dataset.py` writes `data/split/train.csv`, `data/split/val.csv`, and `data/split/test.csv`.  
  - *Verification*: each split respects the 70/15/15 proportion within 1 % tolerance and contains the `pair_id` column; a summary `data/split/split_summary.json` is generated.

---

## Phase 4 – Model Training & Selection  

- [ ] **T006** [S2] [US2] Grid‑search ≤ 50 hyper‑parameter combinations across three regressors (Random Forest, Gradient Boosting, Linear Regression) on the training set, evaluate on the validation set, and record validation R², RMSE, and 95 % bootstrapped CI.  
  - *Implementation*: `code/train_models.py` saves every trained model under `models/` (e.g., `models/rf_001.pkl`) and writes `models/grid_search_results.json`.  
  - *Verification*: script finishes within the 3.5 h CPU limit; `grid_search_results.json` contains the full list of combos and their metrics.

- [ ] **T007** [S2] [US2] Compute k‑fold cross‑validated R² for each model (using the same folds as the split), then select the **best** model: the model with the highest mean CV R² (no abort on low performance). Record its type, hyperparameters, validation metrics, CV R² statistics, and a `null_result` flag if mean CV R² < 0.5 in `models/best_model.json`.  
  - *Verification*: `best_model.json` must exist; CI checks that the required fields are present and that a `null_result` flag is set when appropriate.

- [ ] **T008** [S2] Compute test‑set metrics (R², RMSE, MAE) for **all three** trained models and emit a `ModelArtifact` JSON for each under `models/` (e.g., `models/rf_artifact.json`).
  - *Verification*: each JSON validates against `contracts/model_artifact.schema.yaml`; the best model’s test metrics are also copied into `models/best_model.json`.

---

## Phase 5 – Statistical Significance  

- [ ] **T009** [S3] Run a permutation test with exactly **1,000 shuffles** of the target on the best model’s test set to obtain an empirical p‑value for the observed R².  
  - *Implementation*: `code/perm_test.py` writes the p‑value to `results/permutation_p_value.txt`.  
  - *Verification*: CI asserts that the file exists and that the numeric value is `< 0.05`. If the p‑value ≥ 0.05, the pipeline proceeds (null‑finding will be reported later).

---

## Phase 6 – Interpretability & Stability  

- [ ] **T010** [S3] Generate SHAP values for the best model, produce a summary plot PNG, and save a feature‑ranking JSON. Use `shap.TreeExplainer` for tree models; fall back to `shap.LinearExplainer` or `shap.KernelExplainer` for linear models (FR‑015).  
  - *Implementation*: `code/shap_analysis.py` outputs `figures/shap_summary.png` and `results/shap_feature_ranking.json`.  
  - *Verification*: CI checks that both files exist, the PNG is a valid image, and the JSON conforms to a simple schema (feature → mean | abs SHAP).

- [ ] **T011** [S3] Assess SHAP‑value stability across the k‑fold CV used in Phase 5; compute the standard deviation of mean absolute SHAP values across folds and require `< 0.1`.  
  - *Implementation*: `code/shap_stability.py` writes `results/shap_stability.json`.  
  - *Verification*: CI checks the `std_mean_shap` field against the threshold.

- [ ] **T012** [S3] Produce the four required visualizations for the best model:  
  1. Predicted‑vs‑actual scatter (`figures/predicted_vs_actual.png`)  
  2. Residual histogram (`figures/residual_histogram.png`)  
  3. SHAP summary plot (already generated in T010)  
  4. Parameter‑response curves (`figures/parameter_response_curves.png`)  
  - *Implementation*: `code/visualizations.py` creates all PNGs in a single run.  
  - *Verification*: each file exists, is a valid PNG, and its size > 0 bytes.

- [ ] **T017** [S3] Compute per‑predictor significance (p < 0.05) using linear model coefficients (where a linear model is available) and output `results/per_predictor_significance.json`.  
  - *Implementation*: `code/per_predictor_significance.py` reads the linear model from `models/linear_regression.pkl`, extracts coefficients, computes p‑values via standard errors, and writes the JSON.  
  - *Verification*: CI validates that the JSON maps each feature name to a numeric p‑value.

---

## Phase 7 – Report Assembly & Contract Validation  

- [ ] **T013** [S3] Assemble the final analysis report in both JSON (`reports/analysis_result.json`) and Markdown (`reports/analysis_result.md`). The JSON must conform exactly to `contracts/analysis_result.schema.yaml`; the Markdown must embed hyperlinks to all four PNG visualizations and summarize R² (with 95 % CI), RMSE, MAE, permutation p‑value, top‑3 SHAP predictors, per‑predictor significance (from T017), and indicate a null‑result if `null_result` is true.  
  - *Verification*: CI runs JSON‑schema validation and checks that the Markdown contains the required sections, image links, and the null‑result notice when appropriate.

- [ ] **T014** [S1] Validate **all** output artifacts against their respective contracts and generate a consolidated SHA‑256 manifest.  
  - *Implementation*: `code/validate_and_checksum.py` writes `state/project_checksum_report.yaml`.  
  - *Verification*: script exits with status 0 only if every artifact passes schema validation and the recorded checksums match the computed values.

- [ ] **T015** [S1] Measure total wall‑clock time for the entire pipeline and assert it does not exceed 6 hours.  
  - *Implementation*: `code/measure_runtime.py` wraps the full run, writes elapsed seconds to `data/runtime/total_seconds.txt`.  
  - *Verification*: CI fails if the recorded time > 21600 seconds.

- [ ] **T016** [S3] Create `docs/quickstart.md` with a reproducible command (`python -m llmxive_toolkit.run_all`) and a post‑run checksum verification step for `reports/analysis_result.json`.  
  - *Verification*: after running the command, the documentation’s checksum comparison must succeed; CI runs the command in a fresh environment and checks the result.
