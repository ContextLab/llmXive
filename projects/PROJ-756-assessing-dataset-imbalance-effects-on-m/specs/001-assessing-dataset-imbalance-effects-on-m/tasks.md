# Tasks: Assessing Dataset Imbalance Effects on Materials Property Predictions  

**Input**: `spec.md`, `plan.md`, existing research artifacts, contracts, and reviewer feedback.  

The checklist below follows the platform’s task‑template.  Tasks are grouped by **research phase** and **user story**.  Checked boxes (`[x]`) indicate work that has already passed verification; unchecked boxes (`[ ]`) are pending or have been reopened for correction.  Every task lists the exact artifact paths it creates or modifies and the verification steps required to prove completion.

## Phase 1 – Project bootstrap & entry point  

- [ ] T001 **[ ]** Create project directory skeleton under `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` with sub‑folders `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`, `logs/`. Add placeholder files (`__init__.py`, `.gitkeep`, `run.sh`).  
  **Verification**: `tree projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` shows all directories and placeholder files.  

- [X] T001b **[ ]** Implement `code/main.py` CLI with flags `--full-pipeline`, `--include-mp`, `--fallback-mode`, `--streaming`.
  **Verification**: `python -m code.main --help` prints usage; unit test `tests/unit/test_main_cli.py::test_cli_parsing` passes.  

- [X] T002 **[ ]** Add `code/requirements.txt` pinning exact versions (`pandas==2.2.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `magpie==0.2.*`, `datasets==2.19.*`, `numpy==1.26.*`, `scipy==1.13.*`, `pyyaml==6.0.*`, `cvxpy==1.5.*`).  
  **Verification**: fresh venv `pip install -r code/requirements.txt` succeeds without warnings.  

- [X] T003 **[ ]** Add `pyproject.toml` sections for `ruff` and `black`.  
  **Verification**: `ruff check .` and `black --check .` both exit with code 0.  

## Phase 2 – Data ingestion, descriptor computation, and schema generation  

- [ ] T006a **[US1]** Implement `code/ingestion.py::check_mp_availability` – probes the Materials Project API with a lightweight request, sets global `MP_AVAILABLE` flag, and logs a warning if missing/unauthorized.  
  **Verification**: unit test `tests/unit/test_mp_check.py::test_flag` asserts correct flag for both success and failure scenarios.  

- [ ] T004a **[US1]** Add exponential‑backoff retry logic in `code/ingestion.py::log_api_error` (base 1 s, max 60 s, multiplier 2.0, max 5 retries). Log each attempt as a JSON line to `logs/api_errors.log`.  
  **Verification**: mock a failing endpoint, run ingestion, and assert 5 retries are recorded in the log.  

- [ ] T004c **[US1]** Implement `code/ingestion.py::fail_loudly` that raises `DataFetchError` after retries for OQMD/AFLOW and switches to fallback mode for MP as required by FR‑008.  
  **Verification**: integration test confirms exception is raised and fallback flag is set.  

- [ ] T006b **[US1]** Implement `code/downloaders.py::fetch_oqmd` – streams OQMD dataset via `datasets.load_dataset(..., streaming=True)` into `data/raw/oqmd.parquet`.  
  **Verification**: file exists, size ≤ 5 GB, and a SHA‑256 checksum file `data/raw/oqmd.parquet.sha256` is generated.  

- [ ] T006e **[US1]** Implement `code/downloaders.py::fetch_aflow` – streams AFLOW dataset to `data/raw/aflow.parquet`.  
  **Verification**: same as above.  

- [ ] T006d **[US1]** Implement `code/downloaders.py::fetch_mp` – streams MP dataset to `data/raw/mp.parquet` **only if** `MP_AVAILABLE` is True; otherwise logs warning and skips.  
  **Verification**: presence/absence of the file matches the flag.  

- [ ] T006c‑OQMD **[US1]** Implement `code/downloaders.py::generate_checksum` for `oqmd.parquet` and write SHA‑256 to `data/raw/oqmd.parquet.sha256`.  
  **Verification**: checksum file matches actual file hash.  

- [ ] T006c‑AFLOW **[US1]** Same as above for `aflow.parquet`.  

- [ ] T006c‑MP **[US1]** Same as above for `mp.parquet` (if the file exists).  

- [ ] T006f **[US1]** Implement `code/ingestion.py::merge_datasets` – merges the available raw Parquet files into `data/merged/merged_raw.parquet`.  
  **Verification**: merged file exists and its row count equals the sum of the inputs.  

- [ ] T007a **[US1]** Implement `code/descriptors.py::preprocess_data` – handles missing values, L2‑normalizes numeric columns, writes `data/processed/preprocessed_data.parquet`.  
  **Verification**: no NaNs remain; file size reasonable.  

- [ ] [ ] T007 **[US1]** Implement `code/descriptors.py::compute_magpie` – computes **all 14 L2‑normalized Magpie compositional descriptors** for each material and writes `data/processed/descriptors.parquet`.  
  **Verification**: Parquet contains columns `material_id` plus exactly 14 descriptor columns; a unit test `tests/unit/test_descriptors.py::test_magpie_l2_normalization` checks that each descriptor vector has unit L2 norm.  

- [ ] T007b **[US1]** Implement `code/descriptors.py::extract_schema` – extracts column names/types from `data/processed/descriptors.parquet` and writes JSON schema to `data/processed/descriptor_schema.json`.  
  **Verification**: JSON lists 15 columns (id + 14 descriptors) and matches parquet schema.  

- [ ] T008a **[US1]** Implement `code/imbalance.py::calculate_target_imbalance` – computes the Gini coefficient of each target property distribution (skipping properties with < 100 samples) and writes `results/target_imbalance_scores.csv`.  
  **Verification**: CSV has columns `property,gini`; missing‑sample properties are omitted and a warning is logged.  

- [ ] T008b **[US1]** Implement `code/imbalance.py::calculate_compositional_imbalance` – performs K‑Means clustering (`k=50`) on the 14 Magpie descriptors, computes the Gini coefficient of cluster sizes, and writes `results/compositional_imbalance_score.csv`.  
  **Verification**: CSV contains a single row with column `gini`; a unit test asserts that the Gini value lies in `[0,1]`.  

- [ ] T010b **[US1]** Implement `code/generate_schemas.py::save_dataset_schema` – writes a **YAML** file `contracts/dataset.schema.yaml` that exactly matches the specification under `specs/001-assessing-dataset-imbalance-effects-on-m/contracts/dataset.schema.yaml`.  
  **Verification**: file exists, is valid YAML (passes `yamllint`), and its content is byte‑for‑byte identical to the spec file.  

- [ ] T012 **[US1]** Write contract test `tests/contract/test_dataset_schema.py::test_dataset_schema_validation` that loads `contracts/dataset.schema.yaml` and validates `data/processed/descriptors.parquet` using `jsonschema`.  
  **Verification**: test passes on the current descriptor file.  

- [ ] T006c‑agg **[US1]** After all checksum tasks complete, aggregate the generated SHA‑256 values and write the consolidated `artifact_hashes` map into `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml`.  
  **Verification**: state file contains entries for `oqmd.parquet`, `aflow.parquet`, and (if present) `mp.parquet` with correct hashes.  

## Phase 3 – User Story 1: Baseline models on skewed data (Priority P1)  

- [ ] T014 **[US1]** Implement `code/training.py::train_rf` and `code/training.py::train_gb` – train Random Forest and Gradient Boosting regressors on the **skewed** training set (the full merged dataset) with identical hyper‑parameters. Save models to `artifacts/baseline_rf.pkl` and `artifacts/baseline_gb.pkl`.  
  **Verification**: both pickle files exist; a unit test checks that `model.feature_importances_` is non‑empty.  

- [ ] T015 **[US1]** Implement `code/evaluation.py::evaluate_model` – evaluate each baseline model on a **stratified test set** that preserves the original imbalance. Write global metrics (MAE, RMSE, R²) to `results/baseline_metrics.json`.  
  **Verification**: JSON contains keys `mae`, `rmse`, `r2` for both models and values are numeric.  

- [ ] T016 **[US1]** Implement `code/evaluation.py::generate_baseline_report` – collate baseline metrics into a CSV `results/baseline_report.csv` with columns `property,model_type,mae,rmse,r2`.  
  **Verification**: CSV header matches specification; row count equals 2 × (number of target properties).  

- [ ] T019 **[US1]** Add verification script `code/verify_baseline.py` that runs contract test `tests/contract/test_dataset_schema.py` and integration test `tests/integration/test_baseline_pipeline.py` before allowing report generation.  
  **Verification**: script exits with code 0 only when both tests pass.  

## Phase 4 – User Story 2: Resampling, balanced training, and statistical analysis (Priority P2)  

- [ ] T023 **[US2]** Implement `code/resampling.py::resample_dataset` – perform **equal‑frequency binning into 20 bins**, enforce **real‑data CV ≤ 0.10**; if > 20 % data loss or empty bins, automatically switch to **cost‑sensitive learning** (`class_weight='balanced'`) or **SMOTE for regression** (synthetic portion ≤ 30 %). Raise `ValidationException` if synthetic > 30 % or combined CV > 0.30. Output balanced dataset to `data/processed/balanced_dataset.parquet`.  
  **Verification**: file exists; test `tests/unit/test_resampling.py::test_cv_constraints` checks CV values and fallback behavior.  

- [ ] T024 **[US2]** Add explicit CV assertions inside `resample_dataset` that raise `ValidationException` when constraints are violated.  
  **Verification**: unit test confirms exception is raised on a deliberately imbalanced mock input.  

- [ ] T025 **[US2]** Implement `code/training.py::train_balanced_models` – train RF and GB on `balanced_dataset.parquet` using the same hyper‑parameters as baseline. Save to `artifacts/balanced_rf.pkl` and `artifacts/balanced_gb.pkl`.  
  **Verification**: model files exist and `model.n_estimators` matches baseline.  

- [ ] T026 **[US2]** Implement `code/evaluation.py::isolate_minority_subset` – identify the **bottom 10 th percentile** of each target property (configurable quantile in `config/research_params.yaml`). Save subset to `data/processed/minority_subset.parquet` and document the threshold choice in `results/minority_threshold_justification.md`.  
  **Verification**: subset file contains ≤ 10 % of rows per property; justification file is non‑empty.  

- [ ] T027 **[US2]** Implement `code/evaluation.py::calculate_degradation` – compute `MAE_skewed_minority - MAE_balanced_minority` per property and write `results/performance_degradation.csv`.  
  **Verification**: CSV contains columns `property,mae_skewed,mae_balanced,degradation`.  

- [ ] T027a **[US2]** Implement `code/evaluation.py::calculate_percentage_degradation` – compute the **absolute percentage change** in MAE for the minority subset: `100 * (MAE_skewed_minority - MAE_balanced_minority) / MAE_skewed_minority` and append a column `pct_degradation` to `results/performance_degradation.csv`.  
  **Verification**: the CSV now includes `pct_degradation` with numeric values between 0 and 100.  

- [ ] T028 **[US2]** Implement `code/evaluation.py::run_power_analysis` – perform a power analysis (Cohen’s d = 0.5, α = 0.05, power ≥ 0.8) to determine the minimum number of random seeds. Write seed count to `results/power_analysis.json`.  
  **Verification**: JSON field `seed_count` is an integer ≥ 5.  

- [ ] T029 **[US2]** Implement `code/evaluation.py::run_statistical_tests` – for the seed count from T028, run a **paired t‑test** (fallback to Wilcoxon if normality fails) comparing skewed vs. balanced MAE on the minority subset. Write results to `results/statistical_test_results.csv` (`test_type,p_value,effect_size,seed_count`).  
  **Verification**: p‑value column numeric and ≤ 1.  

- [ ] T030 **[US2]** Implement `code/evaluation.py::compute_correlation_compositional` – Pearson correlation between **Compositional Imbalance Score** (from T008b) and **performance degradation** (from T027). Append to `results/correlation_analysis.csv` (`property,score_type,r,p_value`).  
  **Verification**: correlation values within [‑1, 1].  

- [ ] T031 **[US2]** Implement `code/evaluation.py::compute_correlation_target` – same as T030 but using **Target Imbalance Score** (from T008a).  
  **Verification**: same as above.  

- [ ] T033 **[US2]** Add contract test `tests/contract/test_resampling_logic.py::test_cv_constraint` and integration test `tests/integration/test_statistical_significance_logic.py::test_power_analysis_seed_count`. Both must pass before T032 runs.  
  **Verification**: test suite exits with code 0.  

- [ ] T032 **[US2]** Implement `code/evaluation.py::generate_comparison_report` – combine baseline and balanced metrics, degradation, statistical significance, and effect sizes into `results/comparison_report.csv`.  
  **Verification**: each property appears with both strategies and all required columns.  

- [ ] T034 **[US3]** Write contract test `tests/contract/test_shap_schema.py::test_rank_shift_schema` that validates `results/shap_analysis/rank_shift.csv` against `specs/001-assessing-dataset-imbalance-effects-on-m/contracts/shap_comparison.schema.yaml`.  
  **Verification**: test passes on the generated CSV.  

- [ ] T035 **[US3]** Write integration test `tests/integration/test_shap_validation.py::test_ground_truth_accuracy` that runs the synthetic‑ground‑truth pipeline (T036a → T037 → T038 → T039) and asserts that `shap_validation.json` reports `consistent == true`.  
  **Verification**: test exits with code 0.  

## Phase 5 – User Story 3: SHAP analysis & synthetic ground‑truth validation (Priority P3)  

- [ ] T036a **[US3]** Implement `code/shap_analysis.py::generate_synthetic_ground_truth` – create a synthetic dataset (`data/synthetic/ground_truth.parquet`) with the same 14 descriptor columns, known non‑linear feature weights (physics‑inspired function), and target generated as `w·x + α·∑x² + β·∑x_i·x_{i+1}` plus Gaussian noise. Also write the true weight vector to `data/synthetic/ground_truth_weights.json`.  
  **Verification**: Parquet contains expected columns; weight file lists 14 numeric entries.  

- [ ] T036b **[US3]** Implement `code/shap_analysis.py::validate_synthetic_weights` – read the generated weights and confirm they follow the prescribed formula (e.g., monotonic relationship with atomic number). Write validation summary to `data/synthetic/ground_truth_validation.json`.  
  **Verification**: JSON contains a boolean `valid` flag set to true.  

- [ ] T037 **[US3]** Implement `code/shap_analysis.py::compute_shap_values` – compute SHAP values for **both** skewed and balanced models using `shap.TreeExplainer`. Save arrays to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`.  
  **Verification**: both `.npy` files exist and have shape `(n_samples, 14)`.  

- [ ] T038 **[US3]** Implement `code/shap_analysis.py::rank_features` – rank features by mean absolute SHAP value for each model, produce `results/shap_analysis/rank_shift.csv` with columns `feature,rank_skewed,rank_balanced,rank_shift`.  
  **Verification**: top‑10 features for each model are present; rank shifts are integers.  

- [ ] T038a **[US3]** Implement `code/shap_analysis.py::calculate_mean_rank_shift` – compute the **mean rank shift** of the top‑10 features and write a summary CSV `results/shap_analysis/mean_rank_shift.csv` with columns `property,mean_rank_shift`.  
  **Verification**: CSV contains a single row per property with a numeric mean rank shift.  

- [ ] T039 **[US3]** Implement `code/shap_analysis.py::validate_shap_rankings` – compare the SHAP rank‑shift CSV against the known synthetic weights; produce a summary `results/shap_analysis/shap_validation.json` indicating whether observed distortions are consistent with the ground truth.  
  **Verification**: JSON includes fields `consistent` (bool) and `distortion_count` (int).  

- [ ] T040 **[US3]** Implement `code/shap_analysis.py::visualize_rank_shift` – generate `results/shap_analysis/rank_shift_plot.png` (bar plot of absolute rank shifts) and `results/shap_analysis/feature_importance_bar.png` (side‑by‑side importance bars for skewed vs. balanced).  
  **Verification**: both PNG files are non‑empty and readable.  

- [ ] T041 **[US3]** Assemble a markdown report `results/shap_analysis/shap_report.md` that links to the CSVs, PNGs, and validation JSON, summarizing the extent of feature‑importance distortion.  
  **Verification**: markdown file contains hyperlinks to all artifacts, the mean‑rank‑shift CSV, and a brief narrative; the report generation script checks that contract test T034 and integration test T035 have passed.  

## Phase 6 – Cross‑cutting polish, documentation, and final validation  

- [ ] T043a **[P]** Update `README.md` with installation steps, directory layout, and quick‑start command (`python -m code.main --full-pipeline`).  
  **Verification**: file exists and contains the exact string `python -m code.main --full-pipeline`.  

- [ ] T043b **[P]** Create `docs/quickstart.md` detailing step‑by‑step execution (ingestion → descriptors → baseline → resampling → SHAP) and expected output file names.  
  **Verification**: file exists and includes a level‑2 heading `## Quick‑Start`.  

- [ ] T044a **[P]** Run `ruff check` on all `code/` files; write `results/lint_report.txt`.  
  **Verification**: report contains “No issues found”.  

- [ ] T044b **[P]** Run `black --check` on all `code/` files; write `results/format_report.txt`.  
  **Verification**: report contains “All done!”.  

- [ ] T045 **[P]** Add memory‑profiling hooks (using `memory_profiler`) to `code/training.py::train_rf` and `code/shap_analysis.py::compute_shap_values`; log peak memory to `results/memory_profile.csv` (`timestamp,peak_memory_mb,function_name`).  
  **Verification**: CSV contains at least two rows with values < 7000 MB.  

- [ ] T046 **[P]** Add edge‑case unit tests (`tests/unit/test_edge_cases.py`) for: (a) a target property with < 100 samples (should be skipped), (b) API rate‑limit handling (exponential backoff).  
  **Verification**: all new tests pass.  

- [ ] T047a **[P]** Execute full pipeline in **MP‑available mode**: `python -m code.main --full-pipeline --include-mp --streaming`. Capture runtime, exit code, and pass/fail flag in `results/validation_log_mp.txt`. Ensure wall‑clock ≤ 6 h and RAM ≤ 7 GB (monitor via `psutil`).  
  **Verification**: log reports `runtime_seconds < 21600` and `max_ram_mb < 7000`.  

- [ ] T047b **[P]** Execute full pipeline in **fallback mode** (MP unavailable): `python -m code.main --full-pipeline --fallback-mode --streaming`. Save log to `results/validation_log_fallback.txt` with the same constraints as above.  
  **Verification**: same as T047a.  

- [ ] T048 **[P]** Review `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` for completeness; generate `results/versioning_review.json` summarizing whether all artifact hashes are present and match current files.  
  **Verification**: JSON field `all_hashes_match` is true.  

---  

### Dependency & Execution Order Summary  

1. **Phase 1** → establishes the runnable environment.  
2. **Phase 2** (T006a → T004a → T004c → T006b/e/d → checksums → T006f → T007a → **T007**, T007b → T008a → T008b → T010b → T012 → T006c‑agg) produces raw data, processed descriptors, imbalance scores, and the required contract files.  
3. **User Story 1** (T014‑T016, T019) depends on descriptors (T007) and the imbalance scores (optional).  
4. **User Story 2** (T023‑T033, T032) depends on baseline models (T014‑T016) and on the imbalance scores (T008a/b).  
5. **User Story 3** (T036a‑T041, T034‑T035) depends on both skewed and balanced models (T014‑T025).  
6. **Phase 6** runs after all scientific results are available; the full‑pipeline validation tasks (T047a/b) verify end‑to‑end reproducibility under both MP‑available and fallback scenarios.  

---  

*All tasks conform to the canonical checklist format, reference exact artifact paths, and include explicit verification steps to satisfy the independent verifier.*  