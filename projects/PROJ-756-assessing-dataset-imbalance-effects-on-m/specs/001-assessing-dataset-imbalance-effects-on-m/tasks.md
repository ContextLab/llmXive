# Tasks: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Input**: Design documents from `/specs/001-assess-dataset-imbalance-effects/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project directory structure: `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` including `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`, `logs/`, `logs/archive/`. **MUST create placeholder files**: `code/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `artifacts/.gitkeep`, `results/.gitkeep`, `state/.gitkeep`, `logs/.gitkeep`, `tests/__init__.py`, `code/requirements.txt`, and a `run.sh` entry point script in the root to ensure the project is immediately runnable per Constitution Principle I.
- [X] T001b [P] Implement `code/main.py` entry point with CLI arguments `--full-pipeline`, `--include-mp`, `--fallback-mode`, `--streaming`. **Must parse arguments and orchestrate the full pipeline flow.** **Verification**: Run `python code/main.py --help` and verify usage string; create `tests/unit/test_main_cli.py::test_cli_parsing` to assert argument parsing. (FR-001, FR-008).
- [X] T002 [P] Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, scikit-learn, shap, magpie, datasets, numpy, scipy, pyyaml, cvxpy). **Verification**: Run `pip install -r code/requirements.txt` in a fresh venv and verify success.
- [X] T003 [P] Configure linting (ruff/black) and formatting tools in root `pyproject.toml`. **MUST add** `[tool.ruff]` and `[tool.black]` sections. **Verification**: Run `ruff check.` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Foundation is READY ONLY AFTER T006a, T004a-Backoff, T006b-DataFetch, T006d-DataFetch-MP, T006e-AFLOW-DataFetch, T006c-OQMD, T006c-AFLOW, T006c-MP, T007, T007a, T007b, T008a, T008b are complete.**

- [ ] T006a-MP-Availability-Check Implement `code/ingestion.py::check_mp_availability` to **detect Materials Project API availability** by attempting a lightweight probe request using the configured API key. **If the key is missing or the probe fails (403/timeout), set a global flag `MP_AVAILABLE = False` and log a warning.** **This task ensures FR-008 fallback logic is triggered before ingestion begins.** (FR-008). **Must be the first task in Phase 2; must complete before T004a-Backoff.**
- [ ] T004a-Backoff Implement `code/ingestion.py::log_api_error` and retry logic for OQMD, AFLOW, and Materials Project APIs. **Parameters**: base_delay=1s, max_delay=60s, multiplier=2.0, max_retries=5. **Log all API errors as JSON lines to `logs/api_errors.log`** with schema `{"timestamp":..., "endpoint":..., "error":..., "retry_count":...}`. (FR-007, FR-008). **Depends on T006a for MP availability flag. Must run after T006a. Cannot be marked [P] for parallel execution with T006a.**
- [X] T004c [P] Implement `code/ingestion.py::fail_loudly` logic for **Fail Loudly**: raise `DataFetchError` on persistent failure for OQMD/AFLOW; for Materials Project, if persistent failure occurs after retries, log a warning and switch to fallback mode (OQMD/AFLOW only) as per FR-008, ensuring no synthetic fallback. **Depends on T004a-Backoff.**
- [ ] T006b-DataFetch Implement `code/downloaders.py::fetch_oqmd` to download OQMD dataset **to `data/raw/oqmd.parquet`** using the **Hugging Face `datasets` library with `streaming=True`** to avoid loading full dataset into memory. **Ensure directory exists: `mkdir -p data/raw`.** (FR-001, FR-007, FR-008). **Depends on T004a-Backoff (interface) and T004c (error handling).**
- [ ] T006d-DataFetch-MP Implement `code/downloaders.py::fetch_mp` to download Materials Project dataset **to `data/raw/mp.parquet`** if `MP_AVAILABLE` is True. **Use the Hugging Face `datasets` library with `streaming=True`**. **If `MP_AVAILABLE` is False, skip this task and log a warning.** (FR-001, FR-008). **Depends on T004a-Backoff (interface), T004c (error handling), and T006a.**
- [ ] T006e-AFLOW-DataFetch Implement `code/downloaders.py::fetch_aflow` to download AFLOW dataset **to `data/raw/aflow.parquet`** using the **Hugging Face `datasets` library with `streaming=True`**. (FR-001, FR-007, FR-008). **Depends on T004a-Backoff (interface) and T004c (error handling).**
- [ ] T006c-OQMD Implement `code/downloaders.py::generate_checksum` to generate SHA-256 checksum for `data/raw/oqmd.parquet` and save to `data/raw/oqmd.parquet.sha256` in `sha256sum` format. **Update `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` with the generated checksum.** (Constitution Principle III). **Sequential to T006b-DataFetch.**
- [ ] T006c-AFLOW Implement `code/downloaders.py::generate_checksum` to generate SHA-256 checksum for `data/raw/aflow.parquet` and save to `data/raw/aflow.parquet.sha256`. **Update state file.** **Sequential to T006e-AFLOW-DataFetch.**
- [ ] T006c-MP Implement `code/downloaders.py::generate_checksum` to generate SHA-256 checksum for `data/raw/mp.parquet` (if exists) and save to `data/raw/mp.parquet.sha256`. **Update state file.** **Sequential to T006d-DataFetch-MP.**
- [ ] T006f-Merge-Datasets Implement `code/ingestion.py::merge_datasets` to combine OQMD, AFLOW, and MP (if available) into a single unified dataset. **Output**: `data/merged/merged_raw.parquet`. **This task is required by FR-001 and is a dependency for T007.** **Depends on T006b, T006d, T006e, and T006c-OQMD/AFLOW/MP.**
- [ ] T007a-Preprocessing Implement `code/descriptors.py::preprocess_data` to handle missing values, normalize features (L2-normalization), and prepare the merged dataset for descriptor computation. **Output**: `data/processed/preprocessed_data.parquet`. **Depends on T006f.**
- [ ] T007 [P] Implement `code/descriptors.py::compute_magpie` to compute all Magpie compositional descriptors (L2-normalized) and save to `data/processed/descriptors.parquet` (FR-002). **Depends on T007a.**
- [ ] T007b-Schema-Extraction Implement `code/descriptors.py::extract_schema` to **extract the schema (column names, count)** from `data/processed/descriptors.parquet` and save it as `data/processed/descriptor_schema.json`. **This artifact is required for T036 to generate the synthetic ground truth.** (FR-014). **Depends on T007.**
- [ ] T008a [P] Implement `code/imbalance.py::calculate_target_imbalance` to calculate **Target Imbalance Score** (Gini coefficient of target property values for properties with >= 100 samples, handling negative values via absolute transformation or offset). Skip properties with < 100 samples. Output to `results/target_imbalance_scores.csv` (FR-011). **Depends on T006b, T006d, T006e, T007.**
- [ ] T008b [P] Implement `code/imbalance.py::calculate_compositional_imbalance` to calculate **Compositional Imbalance Score** (Gini coefficient of the **cluster assignment counts** derived from K-Means clustering with k=50 and Euclidean distance on compositional features). **Step 1: Perform K-Means clustering (k=50) on compositional features. Step 2: Calculate Gini coefficient of the frequency of samples assigned to each cluster.** **Load feature matrix from `data/processed/descriptors.parquet`.** Output to `results/compositional_imbalance_score.csv` (FR-002). **Note: This task implements Spec FR-002, which supersedes the Plan.md 'Complexity Tracking' table's mention of 'Convex Hull'. The Spec (FR-002) is the Single Source of Truth and takes precedence.** **Depends on T006b, T006d, T006e, T007.**
- [X] T010 [P] Create unit tests for ingestion retry logic and API failure handling in `tests/unit/test_ingestion.py::test_exponential_backoff_retries`.
- [ ] T011 [P] Create unit tests for Magpie descriptor computation in `tests/unit/test_descriptors.py::test_magpie_l2_normalization`.
- [ ] T010b [P] Generate `contracts/dataset.schema.yaml` defining the schema for `data/processed/` (columns: composition, target properties, descriptors, imbalance scores) (FR-001). **Implement `code/generate_schemas.py::generate_dataset_schema`**.
- [ ] T010c [P] Generate `contracts/resampling.schema.yaml` defining the schema for resampled datasets (columns: bin_id, sample_count, CV, real_data_flag, synthetic_flag) (FR-003). **Implement `code/generate_schemas.py::generate_resampling_schema`**. **Must be completed before T020.**
- [ ] T012 [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py::test_dataset_schema_validation` (validates `data/processed/` against `contracts/dataset.schema.yaml`). *Depends on T010b.*
- [ ] T013 [P] Integration test for baseline pipeline in `tests/integration/test_baseline_pipeline.py::test_full_pipeline_mae_output` (runs ingestion → descriptors → baseline training → report).
- [ ] T015 [P] Integration test for statistical significance in `tests/integration/test_statistical_significance.py::test_statistical_significance_validation` (validates power analysis and p-value calculation).
- [ ] T049 [P] Implement strict error handling in `code/downloaders.py` and `code/ingestion.py`: **raise a specific `DataFetchError` exception on any persistent fetch failure for OQMD/AFLOW after retries**, ensuring no synthetic fallback code paths exist (Constitution Principle II, "Fail Loudly" rule). **Preserve exponential backoff and retry logic. For MP, implement fallback logic as per FR-008.** **Depends on T004a-Backoff, T004c, T006b-DataFetch, T006d-DataFetch-MP, T006e-AFLOW-DataFetch.**
- [ ] T050 [P] [US1/US2] Add a verification script `code/verify_no_synthetic_fallback.py` that scans `code/downloaders.py`, `code/resampling.py`, and `code/ingestion.py` for patterns indicating synthetic fallback (e.g., `if not data: return mock_data`, `except: return synthetic`) and fails the build if found. **Depends on T004a-Backoff, T004c, T006b-DataFetch, T006d-DataFetch-MP, T006e-AFLOW-DataFetch.**
- [ ] T051 [P] [US2] Implement explicit logging in `code/resampling.py::log_smote_usage` when SMOTE is triggered as a fallback, logging the **exact percentage of synthetic data added** and the **resulting CV** to `results/resampling_log.json` to ensure compliance with FR-013 (Synthetic data ≤ 30%) and FR-003 (Combined CV ≤ 0.30). **Verify that the hard validation gate in T023 raises a ValidationException if the synthetic portion exceeds 30%.** **Depends on T023.**

### Checkpoint
**Foundation ready ONLY AFTER T006a (MP Check), T004a-Backoff, T006b (OQMD), T006d (MP), T006e (AFLOW), T006c-OQMD/AFLOW/MP, T006f (Merge), T007a (Preprocessing), T007 (Descriptors), T007b, T008a, T008b are complete** – user story implementation can now begin in parallel. Note: T006a must run first, followed by T004a-Backoff, then T006b/T006d/T006e.

---

## Phase 3: User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1) 🎯 MVP

**Goal**: Download datasets, compute descriptors, train baseline RF/GB models on skewed data, and generate baseline performance report.

**Independent Test**: Can be fully tested by running `code/ingestion.py`, `code/descriptors.py`, and `code/training.py` (baseline mode) to produce a CSV report with MAE, RMSE, R² for skewed data.

### Tests for User Story 1 (Contract & Integration) ⚠️

- [ ] T012 [US1] Contract test for data schema validation (already defined above).
- [ ] T013 [US1] Integration test for baseline pipeline (already defined above).

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/training.py::train_rf` to train Random Forest and Gradient Boosting regressors on skewed data (FR-004). **Output**: `artifacts/baseline_rf.pkl`.
- [ ] T015 [US1] Implement `code/training.py::evaluate_model` to evaluate models on a stratified test set preserving original imbalance (FR-004). **Output**: `results/baseline_metrics.json`.
- [ ] T016 [US1] Implement `code/evaluation.py::generate_baseline_report` to generate **baseline performance report** saved as `results/baseline_report.csv` with columns: `property, model_type, MAE, RMAE, R2` (FR-004).
- [ ] T019 [US1] Verify that contract tests T012 and integration test T013 **pass before** baseline report generation. **Output**: `results/test_run_log.json` with pass/fail status. **Scheduling constraint: MUST be executed only after T012 and T013 are marked complete.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

**Goal**: Apply stratified resampling (or fallback), retrain models, and statistically compare performance on the minority subset.

**Independent Test**: Can be fully tested by running the resampling pipeline, producing a comparison table and statistical test results (paired t-test/Wilcoxon) showing performance difference on the bottom [MINORITY_QUANTILE] subset.

### Tests for User Story 2 (Contract & Integration) ⚠️

- [ ] T020 [US2] Define Contract test for resampling logic in `tests/contract/test_resampling_logic.py::test_cv_constraint` (validates CV constraints against `contracts/resampling.schema.yaml`). **Validates output of T023.** **Depends on T010c (schema generation).** **This test MUST be written BEFORE T023 implementation (TDD).**
- [ ] T021 [US2] Define Integration test for statistical significance in `tests/integration/test_statistical_significance_logic.py::test_power_analysis_seed_count` (validates power analysis and p-value calculation). **Depends on T029.**

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/resampling.py::resample_dataset` with stratified undersampling/oversampling using **equal-frequency binning into 20 bins** (default) and ensure **real-data CV ≤ 0.10**. **Fallback Logic**: If >20% data loss or empty bins occur, **switch to cost-sensitive learning (class_weight='balanced') OR SMOTE for regression** (flexible order as per FR-003). Enforce **combined CV ≤ 0.30** while still keeping real-data CV ≤ 0.10. **Implement hard validation gate raising `ValidationException` if synthetic data > 30% (FR-013).** **Output**: `data/processed/balanced_dataset.parquet`. (FR-003, US-2 Edge Cases). **Depends on T008a, T008b.**
- [ ] T024 [US2] Enforce the CV constraints described above (real ≤ 0.10, combined ≤ 0.30) within the resampling implementation. **Add assertion in `code/resampling.py::resample_dataset` that raises `ValidationException` if CV > 0.10.**
- [ ] T025 [US2] Implement `code/training.py::train_balanced_models` to retrain RF and GB models on the balanced dataset with identical hyperparameters (FR-004). **Output**: `artifacts/balanced_rf.pkl`.
- [ ] T026-MinoritySubset [US2] Implement `code/evaluation.py::isolate_minority_subset` to **isolate the bottom [deferred] (MINORITY_QUANTILE)** of each target property using **Jenks Natural Breaks (k=5) OR stratified quantile** derived from the **FULL dataset** distribution (FR-010). **The quantile threshold MUST be read from `config/research_params.yaml` or a CLI argument; do NOT hardcode a default.** Calculate per-bin MAE for this subset. **Document the justification for the chosen threshold in `results/minority_threshold_justification.md`.** **Output**: `data/processed/minority_subset.parquet`. (FR-010). **Depends on T008a.**
- [ ] T027 [US2] Implement `code/evaluation.py::calculate_degradation` to calculate **performance degradation**: `MAE_skewed_minority - MAE_balanced_minority` and write to `results/performance_degradation.csv`.
- [ ] T028 [US2] Implement `code/evaluation.py::run_power_analysis` to determine the minimum number of random seeds required for **paired t-test**, Cohen's d = 0.5, power ≥ 0.8, α = 0.05; output seed count to `results/power_analysis.json`.
- [ ] T029 [US2] Implement `code/evaluation.py::run_statistical_tests` to perform paired statistical tests (paired t-test or Wilcoxon) across the seed count from T028 (**Read seed_count from results/power_analysis.json**), saving results to `results/statistical_test_results.csv` with columns `test_type, p_value, effect_size, seed_count` (FR-005). **Sequential dependency: T029 MUST run after T028 completes.**
- [ ] T030 [US2] Implement `code/evaluation.py::compute_correlation` to compute Pearson correlation between **Compositional Imbalance Score** (from T008b) and **performance degradation** (from T027); append results to `results/correlation_analysis.csv` with columns `property, score_type, r, p_value` (FR-012).
- [ ] T031 [US2] Implement `code/evaluation.py::compute_target_correlation` to compute Pearson correlation between **Target Imbalance Score** (from T008a) and **performance degradation**; append results to the same `results/correlation_analysis.csv` (FR-012).
- [ ] T032 [US2] Implement `code/evaluation.py::generate_comparison_report` to generate comparison report `results/comparison_report.csv` with columns `property, metric, skewed_value, balanced_value, delta_pct, p_value, effect_size` (US-2).
- [ ] T033 [US2] Verify that contract test T020 and integration test T021 pass after resampling implementation. **Output**: `results/test_run_log.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

**Goal**: Generate SHAP values, compare top-ranked feature rankings, and validate against a synthetic ground-truth baseline.

**Independent Test**: Can be fully tested by running the SHAP analysis script on trained models and synthetic data, producing a ranked list and visualization of rank shifts.

### Tests for User Story 3 (Contract & Integration) ⚠️

- [ ] T034 [US3] Define Contract test for SHAP output schema in `tests/contract/test_shap_schema.py::test_rank_shift_schema` (validates rank-shift CSV schema). **Validates output of T036.** **Depends on T036a (Synthetic Ground Truth generation completed).**
- [ ] T035 [US3] Define Integration test for synthetic ground truth validation in `tests/integration/test_shap_validation.py::test_ground_truth_accuracy`. **Validates output of T036.** **Depends on T036a (Synthetic Ground Truth generation completed).**

### Implementation for User Story 3

- [ ] T036a [US3] Implement `code/shap_analysis.py::generate_synthetic_ground_truth` to generate a **synthetic dataset** with known non-linear feature weights (algorithm: Gaussian noise with fixed seed). **Load the descriptor schema from T007b (`data/processed/descriptor_schema.json`) to determine feature count and names.** Dynamically generate the `known_weights` vector based on a physics-inspired function: `w_i = mean_atomic_number / scaling_factor` for the **`mean_atomic_number`** feature column, and a negligible or null value otherwise. Target calculated as `target = sum(w_i * x_i) + alpha * sum(x_i^2) + beta * sum(x_i * x_{i+1})` where alpha and beta represent tunable weighting coefficients., saved as `data/synthetic/ground_truth.parquet` (columns: Magpie descriptors, `target`, `known_weights`) (FR-014). *Ensure `known_weights` are validated against descriptor count before use.* **Depends on T007b.**
- [ ] T036b [US3] Validate the generated synthetic ground truth weights in `code/shap_analysis.py::validate_synthetic_weights` to ensure they match the intended physics-inspired function. **Output**: `data/synthetic/ground_truth_validation.json`. **Depends on T036a.**
- [ ] T037 [US3] Implement `code/shap_analysis.py::compute_shap_values` to compute SHAP values for both skewed and balanced models, saving to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`.
- [ ] T038 [US3] Implement `code/shap_analysis.py::rank_features` to rank top features for each model, calculate **mean rank shift** (ties broken by average rank), and write `results/shap_analysis/rank_shift.csv` containing `feature, rank_skewed, rank_balanced, rank_shift`.
- [ ] T039 [US3] Implement `code/shap_analysis.py::validate_shap_rankings` to validate SHAP rankings against the synthetic ground truth (load `data/synthetic/ground_truth.parquet` column `known_weights`), compare `rank_shift.csv` with `known_weights`, output validation summary to `results/shap_analysis/shap_validation.json`.
- [ ] T040 [US3] Implement `code/shap_analysis.py::visualize_rank_shift` to visualize significant rank changes: create `results/shap_analysis/rank_shift_plot.png` (bar plot of rank shift) and `results/shap_analysis/feature_importance_bar.png` (side-by-side importance bars) using matplotlib.
- [ ] T041 [US3] Implement `code/shap_analysis.py::assemble_shap_report` to assemble SHAP comparison report in `results/shap_analysis/shap_report.md` linking to CSVs and PNGs.
- [ ] T042 [US3] Verify contract test T034 and integration test T035 pass after SHAP implementation. **Output**: `results/test_run_log.json`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [P] Update `README.md` with setup instructions, directory layout, and quick-start command examples. **MUST add** `## Installation`, `## Usage`, `## Output` sections.
- [ ] T043b [P] Update `docs/quickstart.md` with step-by-step execution guide and expected output files. **MUST add** `## Step 1: Ingestion`, `## Step 2: Training` sections.
- [ ] T044a [P] Run `ruff check` on all Python files in `code/` and fix errors. **Verification**: Generate `results/lint_report.txt` with exit code 0.
- [ ] T044b [P] Run `black` on all Python files in `code/` and format code. **Verification**: Generate `results/format_report.txt` with exit code 0.
- [ ] T045 [P] Add memory profiling to `code/training.py::train_rf` and `code/shap_analysis.py::compute_shap_values`; log peak usage to `results/memory_profile.csv` with columns `timestamp, peak_memory_mb, function_name` (verify Constraint-002).
- [ ] T046 [P] Add additional unit tests for edge cases (e.g., < 100 samples property, API rate limits) in `tests/unit/test_edge_cases.py::test_insufficient_samples`.
- [ ] T047a [P] [US1/US2/US3] Execute the full pipeline using command `python code/main.py --full-pipeline --include-mp --streaming`, ensuring total runtime ≤ 6 hours by **streaming the full merged dataset (OQMD/AFLOW/MP shards via `datasets.load_dataset(..., streaming=True)` and processing in chunks to fit RAM)**, and save execution log to `results/validation_log_mp.txt` containing runtime, exit code, and pass/fail flag (verify Constraint-001). **Task must check `MP_AVAILABLE` flag; if MP is unavailable, skip MP shards and log a warning, but still verify runtime on OQMD/AFLOW.** *Prerequisite: T016, T027, T030, T036a, T037, T038, T039, T040, T041, T001b must be complete and artifacts generated.*
- [ ] T047b [P] [US1/US2/US3] Execute the full pipeline using command `python code/main.py --full-pipeline --fallback-mode --streaming`, ensuring total runtime ≤ 6 hours by **streaming the OQMD/AFLOW dataset only (MP unavailable scenario)**, and save execution log to `results/validation_log_fallback.txt` containing runtime, exit code, and pass/fail flag (verify Constraint-001 for fallback). *Prerequisite: T016, T027, T030, T036a, T037, T038, T039, T040, T041, T001b must be complete and artifacts generated.* **T047a and T047b must be run sequentially.**
- [ ] T048 [P] Final review of `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` for versioning completeness and artifact hashes. **Verification**: Generate `results/versioning_review.json` with hash verification status.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.
- **Data Integrity (Phase 2)**: Implemented in Phase 2 to ensure foundational logic is in place before user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) – no dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – **requires baseline models** from US1 for comparison.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – **requires trained models** from US1 and US2 for SHAP analysis.

### Within Each User Story

- Tests (if included) **MUST** be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **except T010b/T010c which must complete before T012/T020/T034**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for baseline pipeline in tests/integration/test_baseline_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py with exponential backoff"
Task: "Implement code/descriptors.py to compute Magpie descriptors"
```

**Explicit Dependency Notes**:
- T010b/T010c MUST complete before T012/T014/T020/T034 can even begin (schema generation prerequisite).
- T012 and T014 depend on T010b/T010c.
- T029 depends on T028 (reads seed count from `results/power_analysis.json`).
- T030 and T031 depend on T027, T008a, T008b, and T007.
- T033 depends on T020 and T021.
- T042 depends on T034 and T035.
- T047a and T047b depend on completion of T016, T027, T030, T036a, T037, T038, T039, T040, T041, T001b (All marked [ ] in this revision).
- T019 depends on T012 and T013.
- T006b-DataFetch must complete before T006c-OQMD.
- T006d-DataFetch-MP must complete before T006c-MP.
- T006e-AFLOW-DataFetch must complete before T006c-AFLOW.
- T008a and T008b depend on T006b-DataFetch, T006d-DataFetch-MP, T006e-AFLOW-DataFetch, T007.
- **T049, T050, T051** must be implemented and verified before T047a/T047b (Full Pipeline Execution) to ensure data integrity and prevent fabrication.
- **T049 and T050 depend on T004a-Backoff, T004c, T006b-DataFetch, T006d-DataFetch-MP, T006e-AFLOW-DataFetch** (cannot run in parallel with them).
- **T028 and T029 are strictly sequential; T029 MUST wait for T028 to complete.**
- **T006a-MP-Availability-Check is the first task in Phase 2 and must complete before T004a-Backoff.**
- **T004a-Backoff, T006b, T006d, T006e are sequential to T006a and cannot be marked [P] for parallel execution with T006a.**
- **T006c-OQMD/AFLOW/MP is sequential to T006b/T006d/T006e but parallel to other Phase 2 tasks.**
- T036a depends on T007b-Schema-Extraction.
- **T023 depends on T008a and T008b.**
- **T020 depends on T010c (schema generation) and is written BEFORE T023 (TDD).**
- **T034 and T035 depend on T036a (validation of output).**
- **T047a and T047b must be run sequentially.**

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → test independently → Deploy/Demo
4. Add User Story 3 → test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion, Descriptors, Baseline)
 - Developer B: User Story 2 (Resampling, Statistics)
 - Developer C: User Story 3 (SHAP, Synthetic Ground Truth)
 - Developer D: Phase 2 (Data Integrity & Safety Checks)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where explicitly noted in Dependencies section).
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Data Constraint**: All data loaders **MUST** fail loudly on fetch errors; NO synthetic fallback allowed (T049).
- **Compute Constraint**: Pipeline must run on CPU-only runner; if GPU is required for a method, it must be explicitly scaled down or offloaded, not faked.
- **SMOTE Constraint Resolution**: FR-003 mandates SMOTE as a fallback; Plan.md 'Constraints' section updated to reflect this (SMOTE allowed as fallback).
- **Task Consolidation**: T009a and T009b were removed as they were duplicates of T008. T008 now covers both Target and Compositional Imbalance Score calculations (split into T008a/T008b).
- **Imbalance Score Metric**: T008a/T008b implement K-Means/Gini for compositional diversity (per FR-002) and Gini for target imbalance (per FR-011). **Removed density-weighting step.**
- **Bottom [deferred]**: T026 uses **Jenks Natural Breaks (k=5) OR stratified quantile** for minority subset determination, with a **configurable quantile threshold** (not hardcoded).
- **Log Rotation**: T004b uses size-based rotation (create new file if > 100MB) without deletion to preserve raw trace. T004b-Test was removed as it verified implementation details not in spec.
- **Subset Strategy**: T047a uses streaming of the **full merged dataset** (up to 5GB) for MP scenario; T047b uses streaming of **OQMD/AFLOW dataset only** for fallback scenario to ensure 6-hour constraint verification is valid for both MP and fallback scenarios.
- **Revision Concerns**: Phase 2 tasks (T049-T051) address the "Fail Loudly" data loading rule and prevent synthetic data fabrication in edge cases, ensuring compliance with the Constitution.
- **Data Source**: All data fetches now use Hugging Face `datasets` library with `streaming=True`, aligning with Plan.md's HF strategy and FR-001.
- **Entry Point**: T001b implements `code/main.py` with required CLI flags.
- **Internal Contradiction Resolution**: T008b prioritizes Spec FR-002 (Gini/K-Means) over Plan.md 'Complexity Tracking' text. T020 is moved before T023 to align with TDD. T047a/b and T006a/T004a [P] tags removed to reflect sequential dependencies.