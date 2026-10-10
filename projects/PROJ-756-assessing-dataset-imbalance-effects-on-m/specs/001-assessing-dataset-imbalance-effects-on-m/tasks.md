# Tasks: Assessing Dataset Imbalance Effects on Materials Property Predictions  

**Input**: `spec.md`, `plan.md`, existing research artifacts, contracts, and reviewer feedback.  

The checklist below follows the platform’s task‑template.  Tasks are grouped by **research phase** and **user story**.  Checked boxes (`[x]`) indicate work that has already passed verification; unchecked boxes (`[ ]`) are pending or have been reopened for correction.  Every task lists the exact artifact paths it creates or modifies and the verification steps required to prove completion.

---

## Phase 1 – Project bootstrap & end‑to‑end entry point  

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T001 **[P]** Create project directory skeleton under `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` with sub‑folders `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`, `logs/`. Add placeholder files (`__init__.py`, `.gitkeep`, `run.sh`). **Verification**: `tree` output contains all directories and placeholder files.  
- [ ] T001b **[P]** Implement `code/main.py` CLI (`--full-pipeline`, `--include-mp`, `--fallback-mode`, `--streaming`). **Verification**: `python -m code.main --help` prints usage; unit test `tests/unit/test_main_cli.py::test_cli_parsing` passes.  
- [ ] T002 **[P]** Add `code/requirements.txt` with pinned versions (`pandas==2.2.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `magpie==0.2.*`, `datasets==2.19.*`, `numpy==1.26.*`, `scipy==1.13.*`, `pyyaml==6.0.*`, `cvxpy==1.5.*`). **Verification**: fresh venv `pip install -r code/requirements.txt` succeeds without warnings.  
- [ ] T003 **[P]** Add `pyproject.toml` sections for `ruff` and `black`. **Verification**: `ruff check .` and `black --check .` both exit with code 0.  

---

## Phase 2 – Foundational data ingestion, integrity, and schema generation  

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T006a **[ ]** Implement `code/ingestion.py::check_mp_availability` – probes Materials Project API with a lightweight request; sets global `MP_AVAILABLE` flag and logs a warning if missing/unauthorized. **Verification**: unit test `tests/unit/test_mp_check.py::test_flag` asserts correct flag value for both success and failure scenarios.  
- [ ] T004a **[ ]** Implement exponential‑backoff retry logic in `code/ingestion.py::log_api_error` (base 1 s, max 60 s, multiplier 2.0, max 5 retries). Log each attempt as JSON line to `logs/api_errors.log`. **Verification**: mock a failing endpoint, run ingestion, and assert 5 retries recorded in the log.  
- [ ] T004c **[P]** Add `code/ingestion.py::fail_loudly` that raises `DataFetchError` after retries for OQMD/AFLOW and switches to fallback mode for MP as required by FR‑008. **Verification**: integration test confirms exception is raised and fallback flag is set.  
- [ ] T006b **[ ]** Implement `code/downloaders.py::fetch_oqmd` – streams OQMD dataset via `datasets.load_dataset(..., streaming=True)` into `data/raw/oqmd.parquet`. **Verification**: file exists, size ≤ 5 GB, and a checksum file `data/raw/oqmd.parquet.sha256` is generated.  
- [ ] T006e **[ ]** Implement `code/downloaders.py::fetch_aflow` – streams AFLOW dataset to `data/raw/aflow.parquet`. **Verification**: same as above.  
- [ ] T006d **[ ]** Implement `code/downloaders.py::fetch_mp` – streams MP dataset to `data/raw/mp.parquet` **only if** `MP_AVAILABLE` is True; otherwise logs warning and skips. **Verification**: presence/absence of file matches flag.  
- [ ] T006c‑OQMD **[ ]** Implement `code/downloaders.py::generate_checksum` for `oqmd.parquet` and write SHA‑256 to `data/raw/oqmd.parquet.sha256`. Update `state/projects/PROJ‑756‑...yaml` with the checksum. **Verification**: checksum file matches actual file hash.  
- [ ] T006c‑AFLOW **[ ]** Same as above for `aflow.parquet`.  
- [ ] T006c‑MP **[ ]** Same as above for `mp.parquet` (if file exists).  
- [ ] T006f **[ ]** Implement `code/ingestion.py::merge_datasets` – merges the three raw Parquet files (or the subset available) into `data/merged/merged_raw.parquet`. **Verification**: merged file exists and row count equals sum of inputs.  
- [ ] T007a **[ ]** Implement `code/descriptors.py::preprocess_data` – handles missing values, L2‑normalizes numeric columns, writes `data/processed/preprocessed_data.parquet`. **Verification**: no NaNs remain; file size reasonable.  
- [ ] T007 **[ ]** **(Reopened & corrected)** Implement `code/descriptors.py::compute_magpie` – computes **all 14 L2‑normalized Magpie compositional descriptors** for each material and writes `data/processed/descriptors.parquet`. **Verification**: parquet contains columns `material_id` plus exactly 14 descriptor columns; a unit test `tests/unit/test_descriptors.py::test_magpie_l2_normalization` checks that each descriptor vector has unit L2 norm.  
- [ ] T007b **[ ]** Implement `code/descriptors.py::extract_schema` – extracts column names/types from `data/processed/descriptors.parquet` and writes JSON schema to `data/processed/descriptor_schema.json`. **Verification**: JSON file lists 15 columns (id + 14 descriptors) and matches parquet schema.  
- [ ] T010b **[ ]** **(Reopened & corrected)** Generate **YAML** dataset contract: implement `code/generate_schemas.py::save_dataset_schema` that writes a proper YAML file `contracts/dataset.schema.yaml` matching the supplied `specs/001-assessing-dataset-imbalance-effects-on-m/contracts/dataset.schema.yaml`. **Verification**: file exists, `yamllint` passes, and the contract test `tests/contract/test_dataset_schema.py` runs without error.  
- [ ] T010c **[ ]** **(Reopened & corrected)** Generate **YAML** resampling contract: implement `code/generate_schemas.py::save_resampling_schema` that writes `contracts/resampling.schema.yaml` defining the required fields (`bin_id`, `sample_count`, `cv`, `real_data_flag`, `synthetic_flag`). **Verification**: file exists, validates against a minimal instance in `tests/contract/test_resampling_schema.py`.  
- [ ] T012 **[ ]** **(Reopened & corrected)** Write contract test `tests/contract/test_dataset_schema.py::test_dataset_schema_validation` that loads `contracts/dataset.schema.yaml` and validates `data/processed/descriptors.parquet` against it using `jsonschema`. **Verification**: test passes on the current descriptor file.  

---

## Phase 3 – User Story 1: Baseline model training on skew‑ed data (Priority P1)  

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T014 **[ ]** Implement `code/training.py::train_rf` and `train_gb` – train Random Forest and Gradient Boosting regressors on the **skewed** training set (the full merged dataset) with identical hyper‑parameters. Save models to `artifacts/baseline_rf.pkl` and `artifacts/baseline_gb.pkl`. **Verification**: both pickle files exist; a unit test checks that `model.feature_importances_` is non‑empty.  
- [ ] T015 **[ ]** Implement `code/evaluation.py::evaluate_model` – evaluate each baseline model on a **stratified test set** that preserves the original imbalance. Write global metrics (MAE, RMSE, R²) to `results/baseline_metrics.json`. **Verification**: JSON contains keys `mae`, `rmse`, `r2` for both models and values are numeric.  
- [ ] T016 **[ ]** Implement `code/evaluation.py::generate_baseline_report` – collate baseline metrics into a CSV `results/baseline_report.csv` with columns `property, model_type, mae, rmse, r2`. **Verification**: CSV header matches specification; row count equals 2 × (number of target properties).  
- [ ] T019 **[ ]** Add verification step `code/verify_baseline.py` that runs contract test `tests/contract/test_dataset_schema.py` and integration test `tests/integration/test_baseline_pipeline.py` before allowing report generation. **Verification**: script exits with code 0 only when both tests pass.  

---

## Phase 4 – User Story 2: Resampling, balanced training, and statistical analysis (Priority P2)  

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T023 **[ ]** Implement `code/resampling.py::resample_dataset` – perform **equal‑frequency binning into 20 bins**, enforce **real‑data CV ≤ 0.10**; if > 20 % data loss or empty bins, automatically switch to **cost‑sensitive learning** (`class_weight='balanced'`) or **SMOTE for regression** (synthetic portion ≤ 30 %). Raise `ValidationException` if synthetic > 30 % or combined CV > 0.30. Output balanced dataset to `data/processed/balanced_dataset.parquet`. **Verification**: file exists; a test `tests/unit/test_resampling.py::test_cv_constraints` checks CV values and fallback behavior.  
- [ ] T024 **[ ]** (internal) Add explicit CV assertions inside `resample_dataset` that raise `ValidationException` when constraints are violated. **Verification**: unit test confirms exception is raised on a deliberately imbalanced mock input.  
- [ ] T025 **[ ]** Implement `code/training.py::train_balanced_models` – train RF and GB on `balanced_dataset.parquet` using the same hyper‑parameters as baseline. Save to `artifacts/balanced_rf.pkl` and `artifacts/balanced_gb.pkl`. **Verification**: model files exist and `model.n_estimators` matches baseline.  
- [ ] T026 **[ ]** Implement `code/evaluation.py::isolate_minority_subset` – identify the **bottom 10 th percentile** of each target property using a **configurable quantile** read from `config/research_params.yaml`. Save subset to `data/processed/minority_subset.parquet` and document the threshold choice in `results/minority_threshold_justification.md`. **Verification**: subset file contains ≤ 10 % of rows per property; justification file is non‑empty.  
- [ ] T027 **[ ]** Implement `code/evaluation.py::calculate_degradation` – compute `MAE_skewed_minority - MAE_balanced_minority` per property and write `results/performance_degradation.csv`. **Verification**: CSV contains columns `property, mae_skewed, mae_balanced, degradation`.  
- [ ] T028 **[ ]** Implement `code/evaluation.py::run_power_analysis` – perform a power analysis (Cohen’s d = 0.5, α = 0.05, power ≥ 0.8) to determine the minimum number of random seeds. Write seed count to `results/power_analysis.json`. **Verification**: JSON field `seed_count` is an integer ≥ 5.  
- [ ] T029 **[ ]** Implement `code/evaluation.py::run_statistical_tests` – for the seed count obtained above, run a **paired t‑test** (fallback to Wilcoxon if normality fails) comparing skewed vs. balanced MAE on the minority subset. Write results to `results/statistical_test_results.csv` (`test_type, p_value, effect_size, seed_count`). **Verification**: p‑value column is numeric and ≤ 1.  
- [ ] T030 **[ ]** Implement `code/evaluation.py::compute_correlation` – Pearson correlation between **Compositional Imbalance Score** (from T008b) and **performance degradation** (from T027). Append to `results/correlation_analysis.csv` (`property, score_type, r, p_value`). **Verification**: correlation values are within [‑1, 1].  
- [ ] T031 **[ ]** Implement `code/evaluation.py::compute_target_correlation` – same as T030 but using **Target Imbalance Score** (from T008a). **Verification**: same as above.  
- [ ] T032 **[ ]** Implement `code/evaluation.py::generate_comparison_report` – combine baseline and balanced metrics, degradation, statistical significance, and effect sizes into `results/comparison_report.csv`. **Verification**: each property appears with both strategies and all required columns.  
- [ ] T033 **[ ]** Add contract test `tests/contract/test_resampling_logic.py::test_cv_constraint` (depends on schema from T010c) and integration test `tests/integration/test_statistical_significance_logic.py::test_power_analysis_seed_count`. Both must pass before T032 runs. **Verification**: test suite exits with code 0.  

---

## Phase 5 – User Story 3: SHAP analysis & synthetic ground‑truth validation (Priority P3)  

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T036a **[ ]** Implement `code/shap_analysis.py::generate_synthetic_ground_truth` – create a synthetic dataset (`data/synthetic/ground_truth.parquet`) with the same 14 descriptor columns, known non‑linear feature weights (physics‑inspired function), and target generated as `w·x + α·∑x² + β·∑x_i·x_{i+1}` plus Gaussian noise. Also write the true weight vector to `data/synthetic/ground_truth_weights.json`. **Verification**: parquet contains expected columns; weight file matches descriptor count.  
- [ ] T036b **[ ]** Implement `code/shap_analysis.py::validate_synthetic_weights` – read the generated weights and confirm they follow the prescribed formula (e.g., check monotonic relationship with atomic number). Write validation summary to `data/synthetic/ground_truth_validation.json`. **Verification**: JSON contains a boolean `valid` flag set to true.  
- [ ] T037 **[ ]** Implement `code/shap_analysis.py::compute_shap_values` – compute SHAP values for **both** skewed and balanced models (using `shap.TreeExplainer`). Save arrays to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`. **Verification**: both `.npy` files exist and have shape `(n_samples, 14)`.  
- [ ] T038 **[ ]** Implement `code/shap_analysis.py::rank_features` – rank features by mean absolute SHAP value for each model, produce `results/shap_analysis/rank_shift.csv` with columns `feature, rank_skewed, rank_balanced, rank_shift`. **Verification**: top‑10 features for each model are present; rank shifts are integers.  
- [ ] T039 **[ ]** Implement `code/shap_analysis.py::validate_shap_rankings` – compare the SHAP rank‑shift CSV against the known synthetic weights; produce a summary `results/shap_analysis/shap_validation.json` indicating whether observed distortions are consistent with the ground truth. **Verification**: JSON includes fields `consistent`, `distortion_count`.  
- [ ] T040 **[ ]** Implement `code/shap_analysis.py::visualize_rank_shift` – generate `results/shap_analysis/rank_shift_plot.png` (bar plot of absolute rank shifts) and `results/shap_analysis/feature_importance_bar.png` (side‑by‑side importance bars for skewed vs. balanced). **Verification**: both PNG files are non‑empty and readable.  
- [ ] T041 **[ ]** Assemble a markdown report `results/shap_analysis/shap_report.md` that links to the CSVs, PNGs, and validation JSON, summarizing the extent of feature‑importance distortion. **Verification**: markdown file contains hyperlinks to all artifacts and a brief narrative.  
- [ ] T034 **[ ]** **(Reopened & corrected)** Write contract test `tests/contract/test_shap_schema.py::test_rank_shift_schema` that validates `rank_shift.csv` against `specs/001-assessing-dataset-imbalance-effects-on-m/contracts/shap_comparison.schema.yaml`. **Verification**: test passes on the generated CSV.  
- [ ] T035 **[ ]** **(Reopened & corrected)** Write integration test `tests/integration/test_shap_validation.py::test_ground_truth_accuracy` that runs the synthetic‑ground‑truth pipeline (T036a → T037 → T038 → T039) and asserts that `shap_validation.json` reports `consistent == true` when the synthetic weights are used. **Verification**: test exits with code 0.  

---

## Phase 6 – Cross‑cutting polish, documentation, and final validation  

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T043a **[P]** Update `README.md` with installation steps, directory layout, and quick‑start commands (`python -m code.main --full-pipeline`).  
- [ ] T043b **[P]** Create `docs/quickstart.md` detailing step‑by‑step execution (ingestion → descriptors → baseline → resampling → SHAP) and expected output file names.  
- [ ] T044a **[P]** Run `ruff check` on all `code/` files; write `results/lint_report.txt`. **Verification**: report contains “No issues found”.  
- [ ] T044b **[P]** Run `black --check` on all `code/` files; write `results/format_report.txt`. **Verification**: report contains “All done!”.  
- [ ] T045 **[ ]** Add memory‑profiling hooks (using `memory_profiler`) to `code/training.py::train_rf` and `code/shap_analysis.py::compute_shap_values`; log peak memory to `results/memory_profile.csv` (`timestamp, peak_memory_mb, function_name`). **Verification**: CSV contains at least two rows with realistic memory values (< 7 GB).  
- [ ] T046 **[ ]** Add edge‑case unit tests (`tests/unit/test_edge_cases.py`) for: (a) property with < 100 samples (should be skipped), (b) API rate‑limit handling (exponential backoff). **Verification**: all new tests pass.  
- [ ] T047a **[ ]** Execute full pipeline in **MP‑available mode**: `python -m code.main --full-pipeline --include-mp --streaming`. Capture runtime, exit code, and pass/fail flag in `results/validation_log_mp.txt`. Ensure total wall‑clock ≤ 6 h and RAM ≤ 7 GB (monitor via `psutil`). **Verification**: log reports `runtime_seconds < 21600` and `max_ram_mb < 7000`.  
- [ ] T047b **[ ]** Execute full pipeline in **fallback mode** (MP unavailable): `python -m code.main --full-pipeline --fallback-mode --streaming`. Save log to `results/validation_log_fallback.txt` with same constraints as above. **Verification**: same as T047a.  
- [ ] T048 **[ ]** Review `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` for completeness; generate `results/versioning_review.json` summarizing whether all artifact hashes are present and match current files. **Verification**: JSON field `all_hashes_match` is true.  

---

### Dependency & Execution Order Summary  

1. **Phase 1** must complete before any code is runnable.  
2. **Phase 2** (T006a → T004a → T006b/e/d → checksums → merge → preprocess → descriptor generation) unlocks all user‑story work.  
3. **User Story 1** (T014‑T016, T019) can start once descriptors exist.  
4. **User Story 2** (T023‑T033) depends on baseline models (T014‑T016) and on the imbalance scores (T008a, T008b).  
5. **User Story 3** (T036a‑T041, T034‑T035) depends on both baseline and balanced models (T014‑T025).  
6. **Phase 6** runs after all scientific results are available; the full‑pipeline validation tasks (T047a/b) verify end‑to‑end reproducibility under both MP and fallback scenarios.  

---  

*All tasks above conform to the canonical checklist format, reference exact artifact paths, and include explicit verification steps to satisfy the independent verifier.*
