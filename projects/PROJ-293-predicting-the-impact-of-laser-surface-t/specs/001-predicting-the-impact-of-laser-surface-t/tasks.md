# Tasks: Predicting the Impact of Laser Surface Texturing on Wear Resistance

**Input**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-predict-lst-wear/contracts/`  
**Prerequisites**: All tasks depend on the repository root layout shown in the plan.  
**Verification**: Each task lists a concrete output file and a pytest‑style verification step that must pass for the task to be considered complete.

---

## Phase 1 – Setup & First End‑to‑End Analysis  

| Goal | Run a minimal, fully‑checked pipeline on mock data to prove that the whole workflow can execute end‑to‑end before any scientific work begins. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T001 Create the project directory tree and a manifest that records the existence of every required top‑level folder.  
  *Implementation*: `scripts/create_structure.py` runs `mkdir -p code data tests state models reports data/raw data/processed` and writes `state/structure_manifest.json` containing a JSON list of the created paths.  
  *Verification*: `tests/unit/test_structure.py::test_manifest_exists` checks that the file exists and that all required directories are listed.

- [ ] T002 Document a reproducible entry‑point in `quickstart.md`.  
  *Content*: The markdown file lives at `specs/001-predict-lst-wear/quickstart.md` and shows the command  
  ```bash
  python -m code.main --config specs/001-predict-lst-wear/quickstart.md
  ```  
  *Verification*: `tests/unit/test_quickstart.py::test_command_present` parses the file and asserts the command string is present.

- [ ] T003 Execute a tiny end‑to‑end run on the deterministic mock dataset and write a sample result file.  
  *Run*: `python -m code.main --config specs/001-predict-lst-wear/quickstart.md --sample`  
  *Output*: `data/results/sample_output.csv` (contains the columns `material_class`, `predicted_wear_rate`).  
  *Verification*: `tests/integration/test_sample_run.py::test_sample_output_schema` loads the CSV and checks column names and that at least one row is written.

---

## Phase 2 – Foundational (Research‑source validation & Core utilities)

- [ ] T004 Generate `research.md` with **static, verified** dataset identifiers.  
  *Location*: `specs/001-predict-lst-wear/research.md`.  
  *Details*: Includes three sources – an OpenML dataset ID, a HuggingFace dataset name, and a DOI‑linked literature supplement. No dynamic search logic is present.  
  *Verification*: `tests/unit/test_research.py::test_static_sources` ensures each entry has a non‑empty `url` and `dataset_id` field.

- [ ] T005 Produce a deterministic mock raw dataset for CI.  
  *File*: `data/raw/mock_lst_data.csv` (≥ 150 rows, all required columns, random seed 42).  
  *Verification*: `tests/unit/test_mock_data.py::test_schema_compliance` validates the CSV against `dataset.schema.yaml` and confirms the presence of a mix of missing `contact_load` / `sliding_speed`.

- [ ] T006 Create `code/config/schema_map.json` that maps every possible source column name to the canonical schema (e.g., `"power": ["laser_power","avg_power"]`).  
  *Verification*: `tests/unit/test_schema_map.py::test_all_canonical_keys_present` asserts that each mandatory canonical key appears in the JSON.

- [ ] T007 Verify that `research.md` contains **no** dynamic lookup code.  
  *Implementation*: `code/verify_research.py` scans the file for patterns like `requests.get` or `search(`.  
  *Verification*: `tests/unit/test_verify_research.py::test_no_dynamic_logic` fails if any prohibited pattern is found.

- [ ] T008 Implement deterministic seed handling in `code/seed.py`.  
  *Effect*: Sets `numpy`, `random`, and `torch` seeds (if torch is installed).  
  *Verification*: `tests/unit/test_seed.py::test_repeatability` runs a simple random number generator twice and checks identical outputs.

- [ ] T009 Implement data‑hygiene helpers (MD5 checksums, `state/artifact_hashes.yaml`) in `code/hygiene.py`.  
  *Verification*: `tests/unit/test_hygiene.py::test_checksum_consistency` computes a checksum on a known file and compares it to the stored value.

- [ ] T010 Define the core data‑model classes (`LSTRecord`, `ModelPerformance`, `FeatureImportance`) in `code/models.py`.  
  *Verification*: `tests/unit/test_models.py::test_dataclass_fields` inspects the classes and ensures required attributes match the contract schemas.

- [ ] T011 Set up logging in `code/logging_config.py` to write INFO‑level messages to `logs/pipeline.log` and raise `ValueError` on missing real data (no synthetic fallback).  
  *Verification*: `tests/unit/test_logging.py::test_missing_data_error` triggers the error path and checks the log entry.

---

## Phase 3 – User Story 1: Aggregate & Preprocess LST Wear Data (Priority P1)

- [ ] T012 Implement **fetch_sources** in `code/ingest.py`  
  *Behaviour*: Reads the three static source IDs from `research.md`, downloads each CSV via `requests` (or `datasets.load_dataset` for HuggingFace), and writes the concatenated raw file `data/raw/aggregated_raw.csv`. If any real download fails, the script aborts with a clear error (no synthetic fallback).  
  *Verification*: `tests/integration/test_fetch_sources.py::test_all_sources_downloaded` asserts that the output file exists and that its `source_id` column contains three distinct values.

- [ ] T013 Implement **map_schema** (already completed) – maps source columns to the canonical names using `schema_map.json` and writes `data/intermediate/mapped.csv`.  
  *Verification*: `tests/unit/test_map_schema.py::test_all_columns_mapped`.

- [ ] T014 Implement **handle_missing_values** in `code/ingest.py`  
  *Logic*: Drops any row missing a required predictor (`pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`). Rows missing only `contact_load` or `sliding_speed` are retained and flagged later. Writes `data/processed/aggregated_dropped.csv`.  
  *Verification*: `tests/unit/test_ingest.py::test_missing_predictor_handling` loads the output CSV and checks that no required predictor column contains `NaN`.

- [ ] T015 Implement **archard_normalization** in `code/ingest.py`  
  *Steps*:  
  1. Convert `wear_rate` to volume V using `density` and `contact_area` (FR‑018).  
  2. Apply Archard’s law `K = V / (contact_load * sliding_distance)` when both `contact_load` and `sliding_speed` are present.  
  3. Add column `normalization_method` = `"normalized"` for successful calculations, otherwise `"raw"` (FR‑009).  
  4. Output `data/processed/aggregated_clean.csv`.  
  *Verification*: `tests/unit/test_archard.py::test_k_calculation` confirms that rows marked `"normalized"` have a non‑null `K` and that `"raw"` rows keep the original `wear_rate`.

- [ ] T016 Split the cleaned dataset into normalized‑only and raw‑only subsets.  
  *Implementation*: `code/ingest.py::split_dataset` reads `aggregated_clean.csv` and writes:  
  - `data/processed/normalized_only.csv` (records where `normalization_method=="normalized"`),  
  - `data/processed/raw_only.csv` (records where `"raw"`),  
  - `data/processed/split_summary.json` containing `{ "normalized_count": N, "raw_count": R, "total_count": N+R }`.  
  *Verification*: `tests/unit/test_split.py::test_split_summary` loads the JSON and checks that the counts match the CSV lengths.

- [ ] T017 Create a **held‑out test split** from the normalized‑only data.  
  *Procedure*: `code/ingest.py::split_test_set` performs a stratified split (20 % test) using the fixed seed from `seed.py`. Writes `data/processed/test_split.csv` and `state/test_split_indices.npy`.  
  *Verification*: `tests/unit/test_split.py::test_held_out_indices` ensures the indices file length equals the number of rows in the test CSV and that there is no overlap with the training rows.

- [ ] T018 Count records and write a summary.  
  *File*: `data/processed/record_counts.json` with fields `total_records`, `normalized_count`, `raw_count`.  
  *Verification*: `tests/unit/test_counts.py::test_counts_match_split_summary` cross‑validates against `split_summary.json`.

- [ ] T019 Enforce **data‑sufficiency thresholds** (SC‑004, SC‑006).  
  *Logic*: `code/ingest.py::compare_thresholds` reads `record_counts.json` and writes `reports/pre_check.json` with keys `status` (`"pass"`, `"pilot_warning"`, or `"insufficient_error"`), `reason`, and `study_scope` (`"full_study"`, `"pilot_study"`). It exits with code 0, 2, or 1 respectively.  
  *Verification*: `tests/unit/test_thresholds.py::test_threshold_exit_codes` runs the function on three synthetic count files and asserts the correct status and exit code.

- [ ] T020 Validate the **number of distinct data sources** (FR‑012).  
  *Implementation*: `code/ingest.py::validate_source_count` reads `research.md`, counts unique `source_id`s, writes `reports/source_validation.json`. If `< 1` → error; if `< 3` → warning flag `data_source_limitation: true`.  
  *Verification*: `tests/unit/test_source_validation.py::test_warnings_and_errors` checks both branches.

- [ ] T021 Perform a **statistical power analysis** (FR‑014).  
  *Tool*: Uses `statsmodels.stats.power.FTestPower`. Reads `normalized_count` and the number of predictors, assumes a medium effect size (f² = 0.15), α = 0.05. Writes `reports/power_analysis.json` with fields `power`, `warning` (boolean), and `status`.  
  *Verification*: `tests/unit/test_power_analysis.py::test_power_below_threshold` feeds a low‑count scenario and asserts `warning=True`.

---

## Phase 4 – User Story 2: Train & Validate Regression Models (Priority P2)

- [ ] T022 Build a **scikit‑learn Pipeline** in `code/train.py::preprocess_pipeline` that performs one‑hot encoding of `pattern_geometry`, standard scaling of numeric features, and optional VIF‑based feature dropping (calls `preprocess.run_vif_diagnostics`). The pipeline is stored as `models/pipeline.pkl`.  
  *Verification*: `tests/unit/test_pipeline.py::test_pipeline_components` loads the pickle and checks that the steps are present and ordered correctly.

- [ ] T023 Define the **grid‑search space** (≥ 10 combos) and outer CV split configuration.  
  *File*: `code/train.py::define_grid_search` writes `state/cv_split_config.json` containing the train/test indices used for the outer split (as produced by T017).  
  *Verification*: `tests/unit/test_grid_config.py::test_grid_config_consistency`.

- [ ] T024 Run **grid search** within the training fold only (no leakage).  
  *Execution*: `code/train.py::run_grid_search` reads the outer split, fits `LinearRegression`, `RandomForestRegressor`, and `GradientBoostingRegressor` over the defined grid, uses 5‑fold inner CV, and writes the best model to `models/best_model.joblib` plus `reports/grid_search_summary.json`.  
  *Verification*: `tests/unit/test_grid_search.py::test_best_model_saved` checks that the joblib file exists and that the JSON lists at least 10 evaluated combos.

- [ ] T025 **Evaluate** the selected model on the held‑out test set (`data/processed/test_split.csv`).  
  *Output*: `reports/model_performance.json` adhering to `model_output.schema.yaml`.  
  *Verification*: `tests/unit/test_evaluation.py::test_metrics_match_schema`.

- [ ] T026 Implement **Leave‑One‑Material‑Class‑Out (LOMO) CV** with fallback logic (FR‑006).  
  *File*: `code/train.py::lomo_split_config` writes `reports/lomo_split_config.json` indicating whether LOMO was used, whether fallback to K‑Fold occurred, and any class‑size downgrades.  
  *Verification*: `tests/unit/test_lomo_fallback.py::test_fallback_conditions`.

- [ ] T027 Run the **LOMO validation** (or K‑Fold fallback) and record results in `reports/lomo_validation.json`. Also update `reports/scope_status.json` with `fallback_active` and possibly shift `research_question` wording to “within‑material prediction” when LOMO cannot be performed.  
  *Verification*: `tests/unit/test_lomo_validation.py::test_scope_flag`.

- [ ] T028 Compute the **transferability ratio** (`test_R²_loo / test_R²_standard`) and flag `transferability_failure` if < 0.8. Updates `reports/model_performance.json` with the new fields (`loo_r2_ratio`, `transferability_failure`).  
  *Verification*: `tests/unit/test_transferability.py::test_ratio_and_flag`.

- [ ] T029 Conduct the **sensitivity analysis** (FR‑011) comparing the model trained on `normalized_only.csv` vs. the model trained on the full dataset (`aggregated_clean.csv`). Writes `reports/sensitivity_analysis.json` with differences in R² and MAE.  
  *Verification*: `tests/unit/test_sensitivity.py::test_delta_computation`.

- [ ] T030 Save the final best model (already done in T024) and generate a deterministic mock fallback model (`models/mock_best_model.joblib`) for CI when real training cannot run.  
  *Verification*: `tests/unit/test_mock_model.py::test_mock_loadable`.

---

## Phase 5 – User Story 3: Interpret Feature Importance & Interactions (Priority P3)

- [ ] T031 Compute **SHAP values** for the best model.  
  *Output*: `data/processed/shap_values.npy` and `reports/shap_values.pkl` (pickled list).  
  *Verification*: `tests/unit/test_shap.py::test_shap_array_shape`.

- [ ] T032 Generate **SHAP summary** and **dependency** plots (power vs. scanning_speed).  
  *Files*: `reports/shap_summary.png`, `reports/shap_dependency_power_speed.png`.  
  *Verification*: `tests/unit/test_shap_plots.py::test_images_created`.

- [ ] T033 Detect **non‑linear interactions** using SHAP interaction values or a degree‑2 polynomial fit (FR‑005).  
  *Output*: `reports/interaction_analysis.json` with a boolean `significant_interaction` per feature pair and the R² of the polynomial fit.  
  *Verification*: `tests/unit/test_interaction.py::test_interaction_detection`.

- [ ] T034 Run **VIF diagnostics** and resolve collinearity (FR‑010, FR‑015).  
  *Outputs*: `reports/vif_report.json` (initial VIFs) and `reports/vif_resolution.json` (list of dropped features).  
  *Verification*: `tests/unit/test_vif.py::test_vif_below_threshold`.

- [ ] T035 Perform **conditional permutation significance testing** (≥ 2000 permutations, FR‑008).  
  *File*: `reports/feature_significance.json` containing `feature_name`, `p_value_perm`, `permutation_count`, and a top‑level flag `unstable_significance` if variance > 0.05.  
  *Verification*: `tests/unit/test_permutation.py::test_pvalue_structure`.

- [ ] T036 Attempt to **load an external validation dataset** (if referenced in `research.md`).  
  *Output*: `reports/external_validation_status.json` with `validation_target_unavailable: true/false`.  
  *Verification*: `tests/unit/test_external_load.py::test_status_flag`.

- [ ] T037 Apply the **physical plausibility check** (SC‑002, FR‑007).  
  *Logic*: If external validation is unavailable, compare SHAP sign of `contact_load` and `sliding_speed` against Archard’s law; set `physical_plausibility_failure: true` when contradictions are found. Writes `reports/validation_status.json`.  
  *Verification*: `tests/unit/test_physical_check.py::test_plausibility_flag`.

- [ ] T038 Aggregate all numeric metrics, flags, and scope information into a single JSON for easy consumption.  
  *File*: `data/processed/aggregated_metrics.json`.  
  *Verification*: `tests/unit/test_aggregation.py::test_all_keys_present`.

- [ ] T039 Produce the **final research report** (partial) with associational framing, known‑limitations section, and links to all generated artifacts.  
  *File*: `reports/final_report.md`.  
  *Verification*: `tests/unit/test_final_report.py::test_disclaimer_and_links`.

---

## Phase 6 – Runtime, Tests & Polish  

- [ ] T040 Instrument the **pipeline runtime** (FR‑016). `code/pipeline.py::instrument_runtime` records start/end timestamps, writes `reports/runtime_metrics.json`, and aborts with exit 1 if total wall‑time > 6 h.  
  *Verification*: `tests/unit/test_runtime.py::test_timeout_enforced`.

- [ ] T041 Add **unit tests** for the core user‑story functions that are not already covered (e.g., `handle_missing_values`, `archard_normalization`, `run_lomo_cv`). All tests live under `tests/unit/`.  
  *Verification*: CI must run `pytest -q` and achieve 100 % pass.

- [ ] T042 Add an **integration test** that runs the full pipeline (`python -m code.main`) and asserts that the final artifacts `reports/final_report.md` and `models/best_model.joblib` are produced.  
  *Verification*: `tests/integration/test_full_pipeline.py::test_end_to_end_success`.

- [ ] T043 Refactor code to keep **cyclomatic complexity** of `code/ingest.py::main` below 10 (using `radon`). No functional change, only style.  
  *Verification*: `tests/unit/test_complexity.py::test_complexity_limit`.

---

### Dependency Summary  

| Task | Depends on |
|------|------------|
| T012 | T004, T005, T006 |
| T014 | T013 |
| T015 | T014 |
| T016 | T015 |
| T017 | T016 |
| T018 | T016 |
| T019 | T018 |
| T020 | T004 |
| T021 | T018 |
| T022 | T012‑T019 (needs clean data) |
| T023 | T022 |
| T024 | T023 |
| T025 | T024 |
| T026‑T028 | T025 |
| T029 | T025 |
| T031‑T039 | T025, T028, T029 (require best model & performance files) |
| T040‑T043 | All previous tasks (they operate on final artifacts) |

---

**Checkpoint**: After Phase 3 (User Story 1) the verifier must find all files listed in T012‑T019, and all associated unit tests must pass. Subsequent phases build on those artifacts.

---
