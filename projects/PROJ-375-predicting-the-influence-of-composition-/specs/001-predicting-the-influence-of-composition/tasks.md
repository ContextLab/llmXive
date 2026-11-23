# Tasks: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  
The goal is to implement a fully reproducible, CPU‑only pipeline that ingests real metallic‑glass data, extracts the required compositional descriptors, trains and validates predictive models, and produces verifiable result tables, figures, and documentation.

---

## Phase 0 – Data Ingestion, Metadata Capture & Power / Coverage Analysis  

- [X] T000 [US1] Document the overall Phase 0 workflow and ensure it is referenced in the execution order.  
  - **File**: `docs/phase0_overview.md` – outlines ingestion, metadata capture, power analysis, and coverage checks.  
  - **Verification**: The markdown exists and contains headings for each sub‑step; CI checks its presence.

- [ ] T001 [US1] Create a quick‑start guide and runnable command that executes a minimal end‑to‑end run on the first 100 rows of the curated CSV.   <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/pipeline/run.py exit=1 -->
  - **File**: `docs/quickstart.md` – includes the command `python -m pipeline.run --sample 100`.  
  - **Verification**: Running the command creates `results/sample_output.parquet` containing the columns required by `mg_dataset.schema.yaml` and passes JSON‑Schema validation; the command exits with status 0.

- [ ] T002 [US1] Implement robust data ingestion, amorphous filtering, descriptor calculation, and **mandatory** coverage enforcement.  
  - **Script**: `code/ingestion/fetch_data.py`  
    1. Load `data/raw/curated_metallic_glass.csv`.  
    2. Query the Materials Project API (`pymatgen.ext.matproj.MPRester`) for entries whose `description` contains the word “glass”; retrieve `material_id` and `composition`.  
    3. Query the AFLOWlib REST endpoint for additional “glass” compositions; if the endpoint is unreachable, log a warning and continue (no synthetic fallback).  
    4. De‑duplicate on `material_id` and merge with the CSV.  
    5. Keep only rows flagged as amorphous (CSV flag or MP/AFLOW description contains “glass”) and with a non‑missing `cte`.  
    6. Parse each `composition` with `pymatgen.Composition`; obtain elemental radius, electronegativity, and valence‑electron count from the `mendeleev` package and compute:  
       - weighted mean atomic radius  
       - electronegativity variance (weighted)  
       - valence electron concentration (VEC)  
       - atomic size coefficient of variation (σ/μ)  
    7. Add a per‑row SHA‑256 `checksum` of the raw JSON record and a boolean `thermal_history_flag` (True if the original CSV supplies thermal‑history metadata).  
    8. Write the enriched table to `data/processed/clean_alloy_data.parquet`.  
    9. Compute `coverage = retrieved / CSV entries`. Write `results/ingestion_coverage.json` with fields `{coverage, total_entries, status}`. **If** `coverage < 0.95` **or** `total_entries < 500`, the script exits with status 1, causing the pipeline to fail (enforcing FR‑001).  
    10. Log progress to `logs/ingestion.log`.  
  - **Verification**:  
    - `data/processed/clean_alloy_data.parquet` validates against `specs/001-predicting-the-influence-of-composition/contracts/mg_dataset.schema.yaml`.  
    - `results/ingestion_coverage.json` must report `coverage ≥ 0.95` and `total_entries ≥ 500`; otherwise the script fails and CI marks the task as failed.  
    - Unit test `tests/unit/test_ingestion.py` checks that all descriptor columns exist, contain no NaNs, and that the `checksum` matches a recomputed hash.

- [ ] T003 [US1] Apply multicollinearity mitigation (VIF) with conditional descriptor dropping and optional PCA fallback, then save the final processed dataset.  
  - **Script**: `code/features/multicollinearity.py`  
    1. Load `clean_alloy_data.parquet`.  
    2. Compute Variance Inflation Factor for each of the four descriptors using `statsmodels`.  
    3. **Retention rule**: Keep `weighted_mean_atomic_radius` regardless of its VIF. Drop any other descriptor **only if** its VIF > 5.0 **after** retaining the mean radius. The atomic size coefficient of variation is dropped only when its VIF exceeds the threshold under this condition.  
    4. If **all** descriptors exceed VIF > 5.0, retain the descriptor with the lowest VIF, perform PCA on the four‑dimensional descriptor matrix, keep the first two principal components (≥ 95 % variance), and store them as `pca_comp_1` and `pca_comp_2`. Train a Ridge regression on these components (fallback model).  
    5. Write the resulting table (including any retained VIF scores) to `data/processed/clean_alloy_data_vif.parquet`.  
    6. Export a human‑readable VIF report to `results/vif_report.csv`.  
  - **Verification**: The output parquet validates against the schema (extra columns are allowed). The VIF report lists each descriptor and its score; if PCA was used, the report notes the fallback.

- [ ] T004 [US2] Generate stratified train/test splits respecting alloy families, with a fallback to random split.  
  - **Script**: `code/features/train_test_split.py`  
    1. Load `clean_alloy_data_vif.parquet`.  
    2. Derive `alloy_family` as the sorted, comma‑separated list of element symbols for each composition.  
    3. Attempt a 5‑fold `GroupKFold` split using `alloy_family` as the grouping key.  
    4. If any family has fewer than 5 samples, fall back to an 80/20 stratified random split (`train_test_split` with `random_state=42`).  
    5. Persist `train.parquet` and `test.parquet` under `data/processed/`.  
  - **Verification**: Both files exist, the split respects the grouping rule (no family appears in both sets when GroupKFold succeeds), and the overall train/test ratio is approximately 80/20 when random split is used.

- [ ] T005 [US2] Build the baseline weighted‑average elemental CTE model using experimental NIST data and evaluate it.  
  - **Script**: `code/modeling/baseline.py`  
    1. Load experimental elemental CTE values from the publicly available NIST CSV.  
    2. For any element missing an experimental value, substitute the DFT‑derived CTE from Materials Project and set `baseline_source_mismatch: true` in the results file.  
    3. Compute a weighted‑average elemental CTE for each alloy using its stoichiometric fractions.  
    4. Fit a simple linear regression (single predictor) on the training split and evaluate on the test split, producing R², MAE, RMSE.  
    5. Write metrics to `results/baseline_metrics.json` and the ΔR² (baseline vs. best model) placeholder will be filled later.  
  - **Verification**: The JSON file contains `r2_test`, `mae_test`, `rmse_test`, and a boolean `baseline_source_mismatch`. Unit test `tests/unit/test_baseline.py` confirms that the fallback to DFT values triggers the flag when appropriate.

- [ ] T006 [US2] Train linear‑regression and random‑forest models with 5‑fold cross‑validation and hyper‑parameter grid search.  
  - **Script**: `code/modeling/train_models.py`  
    1. Load `train.parquet`.  
    2. **Linear Regression** – no hyper‑parameters, evaluate with 5‑fold CV, record mean R², MAE, RMSE.  
    3. **Random Forest** – grid search over `n_estimators=[100,200]`, `max_depth=[None,10,20]`, `min_samples_leaf=[1,2]` using `random_state=42`.  
    4. Select the hyper‑parameter combo with the highest mean R².  
    5. Fit the selected models on the full training data and serialize to `models/linear_regression.pkl` and `models/random_forest.pkl`.  
    6. Write a summary of CV scores and chosen hyper‑parameters to `results/model_cv_summary.json`.  
  - **Verification**: The pickle files exist, the JSON summary contains the expected fields, and a unit test `tests/unit/test_training.py` checks that the selected hyper‑parameters match the highest CV R².

- [ ] T007 [US2] Evaluate the best model on the held‑out test set, enforce ΔR² > 0.05, and compute final performance.  
  - **Script**: `code/modeling/evaluate.py`  
    1. Load `test.parquet` and the serialized best model (the one with higher test R² between linear and random forest).  
    2. Compute R², MAE, RMSE on the test set.  
    3. Load baseline metrics from `results/baseline_metrics.json` and calculate `ΔR² = R²_best – R²_baseline`.  
    4. **Failure condition**: If `ΔR² ≤ 0.05`, the script exits with status 1 and logs an error (enforcing SC‑001).  
    5. Write the final performance record to `results/model_performance.json` (conforms to `model_metrics.schema.yaml`).  
  - **Verification**: The JSON file passes schema validation and contains non‑null metric values; a unit test `tests/unit/test_evaluation.py` asserts that the ΔR² check behaves as specified.

- [ ] T008 [US3] Perform a permutation‑test significance analysis with ≥ 1 000 iterations.  
  - **Script**: `code/modeling/permutation_test.py`  
    1. Load the best model and the original training data.  
    2. For 1 000 iterations (seed = 42), shuffle the target `y_train`, retrain the model on the shuffled data, and compute R² on the original test set.  
    3. Build the null distribution of R² values, compute a two‑sided p‑value as `prop(null_R² ≥ observed_R²)`.  
    4. If the observed R² < 0.3, set `p_value: null` and `null_result_flag: true`; otherwise record the numeric p‑value and `null_result_flag: false`.  
    5. Append these fields to `results/model_performance.json` and also save the full null distribution to `results/permutation_null.npy`.  
  - **Verification**: The JSON entry contains `p_value` (or null) and the flag; a test `tests/unit/test_permutation.py` checks the length of the null array and that the p‑value lies in [0,1] when applicable.

- [ ] T009 [US3] Compute feature‑importance rankings using SHAP for linear regression and permutation importance for random forest, plus correlation diagnostics.  
  - **Script**: `code/modeling/feature_importance.py`  
    1. Load the trained best model and the training data.  
    2. **Linear Regression**: compute SHAP values (using `shap.LinearExplainer`) and derive importance scores as mean absolute SHAP values per feature.  
    3. **Random Forest**: extract `feature_importances_` (or use `shap.TreeExplainer` for permutation‑style importance).  
    4. Produce a ranked CSV `results/feature_importance.csv` with columns `feature_name, importance_score, rank`.  
    5. Compute Pearson correlation between each descriptor and CTE on the training data, rank descriptors by absolute correlation, and calculate Spearman ρ and Kendall‑τ between the importance rank and the absolute‑correlation rank.  
    6. Store the two correlation coefficients in `results/correlation_diagnostics.json`.  
  - **Verification**: The CSV and JSON files exist; a unit test `tests/unit/test_feature_importance.py` verifies that Spearman ρ and Kendall‑τ are within the valid range (‑1 to 1).

- [ ] T010 [US1] Conduct sensitivity analysis for missing metadata (> 20 % rows lacking `source_method` or `thermal_history`).  
  - **Script**: `code/analysis/metadata_sensitivity.py`  
    1. Load `clean_alloy_data_vif.parquet` and compute the proportion of rows with missing `source_method` or `thermal_history_flag`.  
    2. If the proportion exceeds 0.20, create `metadata_complete.parquet` containing only rows with complete metadata.  
    3. Retrain the best model on this subset and compute `ΔR²_metadata = R²_complete – R²_full`.  
    4. Write the results to `results/metadata_sensitivity.json` (fields: `missing_fraction`, `delta_r2_metadata`, `performed`).  
  - **Verification**: The JSON file is present; a test `tests/unit/test_metadata_sensitivity.py` ensures that `performed` is true only when the missing fraction threshold is crossed.

- [ ] T011 [US2] Perform a statistical power analysis based on the final usable sample size.  
  - **Script**: `code/analysis/power_analysis.py`  
    1. Read the number of rows in `clean_alloy_data_vif.parquet`.  
    2. Using `statsmodels.stats.power.FTestPower`, compute the achieved power for detecting an effect size `f² = 0.15` at α = 0.05.  
    3. Write a human‑readable report to `results/power_analysis.txt` including the sample size, computed power, and a recommendation (e.g., “Power ≥ 0.8 – sufficient” or “Power = 0.62 – limitation”).  
  - **Verification**: The text file contains a numeric power value; unit test `tests/unit/test_power_analysis.py` checks that the reported power matches the calculation.

- [ ] T012 [US2] Record runtime, peak memory, and enforce the free‑tier resource limits (≤ 2 CPU cores, ≤ 7 GB RAM).  
  - **Script**: `code/analysis/resource_monitor.py`  
    1. Wrap the entire pipeline (from ingestion to evaluation) with timing (`time.perf_counter`) and memory profiling (`psutil`).  
    2. At the start, query the runner’s CPU core count and available memory; if cores > 2 or memory > 7 GB, log an error and exit with status 1.  
    3. After the pipeline finishes, write `results/computational_efficiency.json` containing `runtime_seconds`, `memory_peak_mb`, `cores_used`, and `limits_passed` (boolean).  
  - **Verification**: The JSON file is generated and `limits_passed` is true on the CI runner; a test `tests/unit/test_resource_monitor.py` simulates an over‑limit condition and expects a non‑zero exit code.

- [ ] T013 [US1] Verify that **all** stochastic operations across the codebase use the fixed seed 42.  
  - **Script**: `code/utilities/seed_check.py`  
    1. Scan every pipeline script for `np.random.seed`, `random.seed`, or explicit `random_state` arguments.  
    2. Import each script in a fresh Python process and assert that the global NumPy and Python random seeds equal 42.  
    3. Exit with status 0 if all checks pass; otherwise print the offending file and exit with status 1.  
  - **Verification**: CI runs this script **before** any other task; unit test `tests/unit/test_seed_check.py` confirms that a deliberately mis‑seeded script causes failure.

- [ ] T014 [US1] Write a concise methods‑and‑results document that links every claim to concrete artifacts.  
  - **File**: `docs/research_report.md` – includes sections for data ingestion, descriptor computation, model training, baseline comparison, permutation test, feature importance, power analysis, and resource usage, each referencing the exact result files (e.g., `results/model_performance.json`).  
  - **Verification**: Manual reviewer check that every metric mentioned in the narrative appears in a corresponding JSON/CSV file; a lightweight script `code/utilities/links_check.py` asserts that all referenced paths exist.

- [ ] T015 [US1] Perform a full reproducibility run from a clean repository state using the quick‑start command and confirm deterministic regeneration of all artifacts.  
  - **Procedure**:  
    1. Delete the `data/processed/`, `models/`, and `results/` directories.  
    2. Execute `python -m pipeline.run` (the command documented in `docs/quickstart.md`).  
    3. Compute SHA‑256 hashes of every generated artifact and compare them to the hashes stored in `state/projects/PROJ-375-predicting-the-influence-of-composition-.yaml` (artifact‑hash map).  
    4. Record the outcome (pass/fail) in `docs/reproducibility.md`.  
  - **Verification**: The reproducibility markdown contains a table of artifact paths and a boolean `identical` column; CI fails if any artifact differs.

- [ ] T016 [US2] Validate model output metadata against `model_output.schema.yaml`.  
  - **Script**: `code/validation/model_output_validator.py`  
    1. Load each model metadata file (`results/model_output_<type>.json`).  
    2. Validate against `specs/001-predicting-the-influence-of-composition/contracts/model_output.schema.yaml` using `jsonschema`.  
    3. Exit with status 0 if all files pass; otherwise log validation errors and exit with status 1.  
  - **Verification**: CI runs this validator after model training; unit test `tests/unit/test_model_output_schema.py` checks that a deliberately malformed metadata file triggers a failure.

## Execution Order (respecting data flow)

1. **T013** – Seed check (must run before any stochastic operation)  
2. **T001** – Quick‑start guide (sample run)  
3. **T002** – Data ingestion & mandatory coverage enforcement (Phase 0)  
4. **T003** – Multicollinearity mitigation (VIF & PCA fallback)  
5. **T004** – Train/Test split (Phase 2)  
6. **T005** – Baseline model construction and evaluation  
7. **T006** – Model training with CV and hyper‑parameter search  
8. **T007** – Evaluation & ΔR² enforcement (SC‑001)  
9. **T008** – Permutation‑test significance analysis  
10. **T009** – Feature‑importance (SHAP & permutation) & correlation diagnostics  
11. **T010** – Metadata sensitivity analysis (FR‑009/FR‑012)  
12. **T011** – Power analysis (FR‑011)  
13. **T012** – Resource monitoring & limits verification  
14. **T016** – Model output schema validation (contract compliance)  
15. **T014** – Methods‑and‑results documentation linking artifacts  
16. **T015** – Full reproducibility run (final verification)

All tasks are unchecked until their implementations pass the verification steps described above. Once a task’s artifact validates, the platform will automatically check the box.
