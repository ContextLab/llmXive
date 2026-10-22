# Tasks: Predicting the Impact of Strain Rate on the Yield Strength of Metals  

**Inputs**: `spec.md`, `plan.md`, existing `research.md`, `data‑model.md`, and contracts in `specs/001-predicting-the-impact-of-strain-rate-on/`.  

The list below follows the canonical `- [ ] T### [P?] [USx?] description …` format.  Tasks are ordered to respect data‑flow dependencies; parallel‑eligible tasks are marked with **[P]**.  All file paths are relative to the project root.

---  

## Phase 0 – Data Discovery & Feasibility  

- [ ] T001 **[P]** Verify real data sources (NIST, OpenML, Materials Project) and download raw files to `data/raw/raw_input.csv`.  
  *Implementation*: `code/ingestion/fetchers.py` attempts each download; outcomes appended to `data/fetch_log.txt`.  
  *Verification*: `data/fetch_log.txt` contains a line for each source (`SUCCESS` or `FAIL`).  

- [ ] T002 **[ ]** Halt if no real data source succeeded (enforce Constitution Principle II).  
  *Implementation*: Checks `data/fetch_log.txt`; if all entries are `FAIL`, the pipeline raises a fatal error.  

- [ ] T003 **[ ]** Update `research.md` with the verified data source (real URLs or “none”) and a short feasibility note (sample size, RAM estimate).  
  *Verification*: `research.md` contains a **Verified Datasets** table and a **CPU Feasibility** paragraph.  

---  

## Phase 1 – Project Setup  

- [ ] T004 **[P]** Create project directory tree (`code/`, `data/raw/`, `data/processed/`, `data/models/`, `results/`, `tests/`) and a minimal `requirements.txt`.  
  *Verification*: All listed directories exist; `requirements.txt` includes `pandas`, `scikit-learn`, `scipy`, `shap`, `matplotlib`, `pyyaml`, `pytest`.  

- [ ] T005 **[P]** Add `code/config.py` defining seeds, path constants (`DATA_RAW`, `DATA_PROC`, `MODEL_DIR`), unit‑conversion dict, and `IMPUTATION_R_THRESHOLD = 0.3`.  
  *Verification*: Importing `config` in a REPL prints the constants without error.  

- [ ] T006 **[P]** Implement a lightweight CLI entry point `code/main.py` that parses `--phase` (0‑5) and forwards to the corresponding function in `code/pipeline.py`.  
  *Verification*: Running `python -m code.main --phase 0` executes Phase 0 without traceback and prints a summary.  

---  

## Phase 2 – Ingestion & Pre‑processing (User Story 1)  

- [ ] T007 **[US1]** Standardize units, drop records missing `yield_strength_mpa` or `strain_rate_s_inv`, and write `data/raw/standardized.csv`.  
  *Implementation*: `code/ingestion/preprocess.py` reads `data/raw/raw_input.csv`, applies conversions (MPa, s⁻¹, µm), and filters.  
  *Verification*: `data/raw/standardized.csv` conforms to `dataset.schema.yaml` and contains no rows with null `yield_strength_mpa` or `strain_rate_s_inv`.  

- [ ] T008 **[US1]** Preserve the filtered but **pre‑imputation** snapshot as `data/processed/raw_for_sensitivity.csv`.  
  *Implementation*: Immediately after T007, the DataFrame is saved to the path above via `code/ingestion/preserve_snapshot.py`.  
  *Verification*: File exists and passes the same schema (grain size may be null).  

- [ ] T009 **[US1]** Compute Pearson correlation *r* between the joint vector `[composition_vector, strain_rate_s_inv]` and `grain_size_um` on `raw_for_sensitivity.csv`.  
  *Implementation*: `code/ingestion/correlation_check.py` writes `data/processed/correlation_check.log` (contains numeric *r*) and `data/processed/low_confidence_records.csv` (records with `is_low_confidence = true`).  
  *Verification*: Log line matches regex `r = -?\d\.\d+`; low‑confidence file non‑empty only when *r* < 0.3.  

- [ ] T010 **[US1]** Impute missing alloy composition using the average composition of the record’s `alloy_family`.  
  *Implementation*: `code/ingestion/impute_composition.py` writes `data/processed/composition_imputed.csv`.  
  *Verification*: No `null` entries in the `composition_vector` column; schema validation passes; `is_imputed` flag set to `true` for imputed rows.  

- [ ] T011 **[US1]** Impute missing `grain_size_um` via K‑Nearest‑Neighbors (k = 5) using **imputed composition** and `strain_rate_s_inv` as predictors.  
  *Implementation*: `code/ingestion/impute_grain_size.py` writes `data/processed/imputed.csv` and sets `is_imputed = true` for filled grain sizes.  
  *Verification*: `imputed.csv` contains no nulls in `grain_size_um` where possible; `is_imputed` column present; schema validation passes.  

- [ ] T012 **[US1]** Encode the 10‑dimensional elemental fraction vector for every record and write `data/processed/encoded_features.csv`.  
  *Implementation*: `code/ingestion/encode_features.py` ensures each row sums to 1 ± 0.01.  
  *Verification*: All rows have exactly 10 float entries; a sanity check confirms the sum constraint.  

- [ ] T013 **[US1]** Perform a stratified train‑test split (70 %/30 %) by `alloy_family`, **excluding families with < 20 samples**.  
  *Implementation*: `code/ingestion/split.py` writes `data/processed/train.csv` and `data/processed/test.csv`.  
  *Verification*: Both CSVs exist, contain the same columns as `imputed.csv`, and the low‑sample families are absent from `train.csv`.  

- [ ] T029 **[US2]** Create a minimal stratified split (`data/processed/min_train.csv`, `data/processed/min_test.csv`) for independent testing of User Story 2.  
  *Implementation*: `code/ingestion/split_minimal.py` samples 200 records preserving alloy‑family distribution.  
  *Verification*: Files exist and pass schema validation.  

---  

## Phase 3 – Modeling & Baseline Comparison (User Story 2)  

- [ ] T014 **[US2]** Train ML regressors (Random Forest, Gradient Boosting, Ridge, Linear) with grid‑search hyper‑parameter tuning on `train.csv` **using at least three random seeds**; record metric variance across seeds; serialize each model to `data/models/ml_<model>.pkl`.  
  *Implementation*: `code/modeling/train_ml.py` performs grid‑search, repeats training for seeds 0, 1, 2, and writes a `results/ml_seed_variance.json`.  
  *Verification*: All four `.pkl` files exist; `results/ml_metrics.json` contains `r2`, `mae`, `rmse` for each model **and** a `grid_search_log.txt` confirming hyper‑parameter search.  

- [ ] T015 **[US2]** Fit empirical Johnson‑Cook and Zerilli‑Armstrong models on `train.csv` using `scipy.optimize`.  
  *Implementation*: `code/modeling/train_empirical.py` writes `data/models/empirical_params.yaml`.  
  *Verification*: YAML contains parameter dicts for both models and a recorded training R² (`fit_r2`).  

- [ ] T016 **[US2]** Evaluate every trained model on `test.csv`, compute R², MAE, RMSE, and store results in `results/model_evaluation.json` adhering to `model_output.schema.yaml`.  
  *Verification*: JSON validates against the schema; each entry lists `model_name`, `model_type`, `metrics`, and `statistical_tests` placeholders.  

---  

## Phase 4 – Interpretation & Validation (User Story 3)  

- [ ] T017 **[US3]** **Sensitivity analysis** – retrain the best‑performing ML model on the *raw* (no‑imputation) dataset `raw_for_sensitivity.csv` and on the *imputed* dataset `imputed.csv`; compute the R² difference and write `results/sensitivity_analysis.json`.  
  *Verification*: JSON contains fields `sensitivity_analysis_r2_diff` and `baseline_saturation`.  

- [ ] T018 **[US3]** Compute SHAP values for the best ML model; assert that the top‑3 features match the expectations defined in `contracts/literature_expectations.yaml`.  
  *Implementation*: `code/interpretation/shap_analysis.py` writes `results/feature_importance.json`.  
  *Verification*: The JSON lists the top‑3 features; a script exits with status 0 only if they appear in the literature expectations contract.  

- [ ] T019 **[US3]** Perform a Wilcoxon signed‑rank test comparing absolute errors of the ML ensemble (average of RF & GB) versus the empirical models across all alloy families; store `results/statistical_tests.json` with `wilcoxon_p_value`.  
  *Verification*: JSON field `wilcoxon_p_value` is < 0.05; the test script returns a pass flag.  

- [ ] T020 **[US3]** Generate partial dependence plots of `yield_strength_mpa` vs. `strain_rate_s_inv` for three representative alloy families (e.g., `AA-6061`, `AISI-4340`, `Ti-6Al-4V`).  
  *Implementation*: `code/visualization/pdp.py` writes PNGs to `results/plots/pdp_<family>.png`.  
  *Verification*: All three PNG files exist and are non‑empty.  

- [ ] T021 **[US3]** Detect any non‑monotonic regimes in the PDPs (e.g., sign changes in the derivative) and record them in `data/processed/failure_regimes.csv`.  
  *Verification*: CSV contains rows `alloy_family, strain_rate_range, monotonic_flag`.  

- [ ] T030 **[US3]** Train a minimal ML model on the minimal split (from T029) to enable independent verification of User Story 3 without the full pipeline.  
  *Implementation*: `code/modeling/train_ml_minimal.py` produces `data/models/ml_minimal.pkl` and a small `results/minimal_feature_importance.json`.  
  *Verification*: Files exist and pass schema validation.  

---  

## Phase 5 – Reporting & Handoff  

- [ ] T022 **[ ]** Compile a concise methods‑results markdown report `paper/001-report.md` that references every generated artifact (metrics JSON, plots, sensitivity analysis, failure‑regime table).  
  *Verification*: The report includes hyperlinks to each file and a summary table of R² values for all models.  

- [ ] T023 **[ ]** Run the full pipeline end‑to‑end using the CLI (`python -m code.main --phase all`) and confirm that it completes within the 6‑hour CPU budget (the script logs total runtime to `state/run_time.log`).  
  *Verification*: `state/run_time.log` shows a duration ≤ 6 h and the final line reads `PIPELINE SUCCESS`.  

---  

## Contract Generation  

- [ ] T024 **[ ]** Generate `contracts/dataset.schema.yaml` from the specification and place it under `specs/001-predicting-the-impact-of-strain-rate-on/contracts/`.  
  *Implementation*: `code/contracts/generate_dataset_schema.py`.  
  *Verification*: File exists and validates against JSON‑Schema draft‑07.  

- [ ] T025 **[ ]** Generate `contracts/model_output.schema.yaml` similarly.  
  *Implementation*: `code/contracts/generate_model_output_schema.py`.  
  *Verification*: File exists and validates.  

- [ ] T026 **[ ]** Generate `contracts/literature_expectations.yaml` encoding expected feature‑importance rankings.  
  *Implementation*: `code/contracts/generate_literature_expectations.py`.  
  *Verification*: File exists and matches the schema defined in the spec.  

---  

## Documentation  

- [ ] T027 **[ ]** Create/refresh `data-model.md` documenting the entities and relationships defined in the spec.  
  *Implementation*: `code/docs/write_data_model.py`.  
  *Verification*: File exists and is up‑to‑date with the spec.  

- [ ] T028 **[ ]** Write a `quickstart.md` guide showing how to run the pipeline on a small example dataset.  
  *Implementation*: `code/docs/write_quickstart.py`.  
  *Verification*: Guide renders correctly in the repository viewer.  

---  

### Dependency Summary  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 (data ingestion) | T001, T002, T007 |
| FR‑002 (unit standardisation) | T007 |
| FR‑003 (imputation & drop) | T007, T010, T011 |
| FR‑004 (ML training) | T014 |
| FR‑005 (empirical fitting) | T015 |
| FR‑006 (partial dependence) | T020 |
| FR‑007 (Wilcoxon test) | T019 |
| FR‑008 (sensitivity analysis) | T017 |
| SC‑001 (R² comparison) | T016 |
| SC‑002 (feature importance) | T018 |
| SC‑003 (statistical significance) | T019 |
| SC‑004 (robustness) | T014 (multi‑seed) |
| SC‑005 (bias from imputation) | T017 |
| Contract files | T024, T025, T026 |
| Documentation | T027, T028 |

---  

*All tasks are unchecked; completed work from prior runs (e.g., already‑validated `requirements.txt`) may be checked off manually after verification.  The list respects the data‑flow order, provides concrete file outputs, and includes deterministic verification steps for each scientific requirement.*  