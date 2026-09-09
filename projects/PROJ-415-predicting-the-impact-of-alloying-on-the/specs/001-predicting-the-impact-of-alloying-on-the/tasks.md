---
description: "Task list template for feature implementation"
---

# Tasks: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Input**: Design documents from `/specs/001-predict-alloy-diffusion/`
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

- [X] T001 Create project structure per implementation plan. Create directories: `code/`, `tests/`, `data/raw/`, `data/curated/`, `data/artifacts/`, `models/`, `reports/`, `errors/`, `logs/`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Configure linting (ruff/flake8) and formatting (black) tools. **Note**: This task runs sequentially after T001 to ensure directories exist. It is NOT parallel-safe.
- [X] T003.1 [P] Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Config**: `line-length = 88`, `target-version = 'py311'`, `select = ['E', 'F', 'W', 'I']`. **Note**: This task creates the configuration files required by T003. Explicitly references `Python 3.11` from `plan.md`.
- [X] T003.2 Implement `code/utils/constants.py` with versioned periodic table data (Metallic Radii, Electronegativity). **Dependency**: Must run after T003.1. **Note**: Removed [P] tag as this depends on T003.1.
- [X] T004 Implement `code/config.py` with global constants, random seeds, and path definitions
- [X] T005 [US1] Generate `contracts/diffusion_record.schema.yaml` defining the `DiffusionRecord` entity schema.
 **Logic**:
 1. Define schema with fields:
 - `host_id`: string, required
 - `solute_id`: string, required
 - `concentration`: number (float), required, min: 0
 - `activation_energy`: number (float), required, min: 0
 - `crystal_structure`: string, required (allows mixed structures for testing, filtered later)
 - `diffusion_mode`: string, required, enum: ["self"]
 2. Save to `contracts/diffusion_record.schema.yaml`.
 **Note**: This artifact is required by T006 and T007. This task MUST run before T006 and T007. Updated to allow mixed structures to support mock data testing in T012.1.
- [ ] T006 [US1] Implement `code/data/acquisition.py` to fetch REAL diffusion data from NIST/Materials Project/Literature sources.
 **CRITICAL INSTRUCTIONS**:
 1. Use `pymatgen` to fetch data from the Materials Project API (requires API key) or fetch from a verified NIST CSV URL: `https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/heat_2.csv` (WRONG DATASET - REPLACE WITH REAL DIFFUSION DATA). **CORRECTED**: Use `pymatgen` to query the Materials Project API for diffusion data. If API fails, fetch from `https://raw.githubusercontent.com/materialsproject/pymatgen/master/pymatgen/analysis/diffusion/diffusion_data.csv` (if available) or a verified NIST CSV mirror.
 2. **Pre-flight Check**: Before fetching, perform a HEAD request to verify the URL is reachable. If unreachable after retries (3 retries, 5s backoff, timeout=30s), raise `DataFetchError` with "Data Fetch Failed: URL unreachable".
 3. **Data Validation**: If the fetched RAW dataset contains a small number of entries, **DO NOT** exit. Save a flag `data/raw/data_insufficient_flag.json` with reason "N < 50 (Raw)", log a warning, and proceed to curation. The pipeline will handle the low count in downstream steps (T013/T014) which may exit if the *curated* count is < 50.
 4. Save output to `data/raw/fetched_diffusion.csv`.
 5. Write a `data/raw/source_metadata.json` file containing the exact URL used and a timestamp.
 6. No PDF parsing, external citation validation, or "Reference-Validator Agent" logic is required or permitted.
 7. **Note**: This task MUST run AFTER T005 to ensure the schema exists for validation.
 8. **Note**: This task is NOT parallel-safe; ensure it runs sequentially after T005.
- [X] T007 [US1] Implement `tests/contract/test_schema.py` to validate data structure against `contracts/diffusion_record.schema.yaml` for the `DiffusionRecord` entity. **Status**: [X]. **Dependency**: This task MUST wait for T005 (schema generation) and T006 (data fetch). **Note**: Removed [P] tag as this depends on T006's output.
- [X] T008 Implement `tests/unit/test_constants.py` to verify periodic table data integrity
- [ ] T002.1 [P] Create `code/utils/errors.py` and define the `DataFetchError` exception class.
 **Logic**:
 1. Define `class DataFetchError(Exception): pass`.
 2. Save to `code/utils/errors.py`.
 **Note**: This task is required by T006 and T057 to ensure the 'Fail Loudly' policy is executable.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Curation (Priority: P1) 🎯 MVP

**Goal**: Load raw diffusion datasets, filter for FCC self-diffusion, and handle missing values.

**Independent Test**: Run ingestion script against a mock CSV with mixed structures (FCC, BCC, HCP) and verify output contains ONLY FCC self-diffusion entries with standardized units.

### Tests for User Story 1

- [X] T009 [P] [US1] Contract test for data schema validation in `tests/contract/test_data.py`
- [X] T010 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py`. **Note**: This test uses MOCK data ONLY for verifying logic flow and error handling, explicitly separated from the real data hypothesis validation in T006/T013.
- [X] T010.1 [P] [US1] Implement `code/data/mock_generator.py` to generate a synthetic mock dataset containing mixed crystal structures (FCC, BCC, HCP) and diffusion modes for the Independent Test.
 **Outputs**:
 1. Generate `data/mock/mock_diffusion.csv` with at least 100 rows.
 2. Ensure the file includes valid and invalid entries (e.g., BCC, missing concentration) to test filtering logic.
 3. This task provides the specific mock data required by the spec's "Independent Test" for US1, distinct from the real data fetched in T006.
- [X] T011 [P] [US1] Add validation script `tests/unit/test_ingestion.py` to verify filtering logic on mixed-structure mock data.
- [X] T011.1 [US1] [REMOVED - Merged into T011]

### Implementation for User Story 1

- [ ] T051.1 [US1] Implement `code/data/provenance.py` to create an INITIAL `data/curated/data_provenance.json` stub.
 **Logic**:
 1. Read `data/raw/source_metadata.json` (from T006) to extract the exact URL or source identifier.
 2. Record the `constants.py` version hash used for descriptor calculation.
 3. Record the total number of rows in `data/raw/fetched_diffusion.csv` before filtering.
 4. Set `filtered_count` to 0 initially.
 5. Set `source_type` to "real" if the URL is from the verified list, or "mock" if from mock generator.
 6. Save to `data/curated/data_provenance.json`.
 **Note**: This task MUST run BEFORE T012 so T012 can read `source_type`.
- [ ] T012 [US1] Implement `code/data/ingestion.py` to load CSVs, filter `crystal_structure == config.FILTER_CRITERIA['crystal_structure']` and `diffusion_mode == config.FILTER_CRITERIA['diffusion_mode']`, and convert units to eV/atom. **Note**: Uses `config.FILTER_CRITERIA` to ensure Single Source of Truth compliance. **CRITICAL**: After filtering, if the resulting dataset has fewer than 50 entries AND `source_type == 'real'` (from `data/curated/data_provenance.json`), **exit with code 1** and log "Data Insufficient: Filtered count < 50". If `source_type == 'mock'`, proceed regardless of count. **Dependency**: Must run after T051.1.
- [ ] T013 [US1] Implement `code/data/curation.py` to exclude rows with missing solute concentration or missing atomic radii.
 **Outputs**:
 1. Log exclusions to `data/logs/exclusions.log` (CSV format with `row_id`, `reason_code`). Explicitly record the **count of excluded rows as the first line** (e.g., `# EXCLUSION_COUNT: 5`).
 2. Append records for missing atomic radii to `errors/missing_atomic_data.csv` (CSV with `solute_symbol`, `missing_attribute`).
 3. Output the final curated dataset to `data/curated/filtered.csv`.
 **CRITICAL**: This task MUST create `errors/missing_atomic_data.csv` if any atomic data is missing. Log concentration exclusions with reason code 'MISSING_CONCENTRATION'.
 **Dependency**: This task produces the `data/curated/filtered.csv` artifact required by Phase 4 tasks.
- [ ] T051.2 [US1] Implement `code/data/provenance.py` to UPDATE `data/curated/data_provenance.json` with final counts.
 **Logic**:
 1. Read `data/curated/filtered.csv` (from T013) to get the final count.
 2. Update `filtered_count` in `data/curated/data_provenance.json`.
 3. Log the update.
 **Dependency**: Must run after T013.
- [ ] T014 [US1] Implement edge case handling in `code/data/ingestion.py` for single-host-metal datasets: fallback to random split and log the specific warning: 'Stratification by host metal was not possible due to single-class data.'

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Compute atomic descriptors, train RF/GB models with GridSearch, and train Linear Regression for statistical inference.

**Independent Test**: Verify `size_mismatch` calculation matches manual math; confirm RF/GB/Linear train on CPU without CUDA errors and output metrics.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test for `size_mismatch` calculation in `tests/unit/test_descriptors.py`
- [X] T016 [P] [US2] Unit test for model training (CPU-only check) in `tests/unit/test_models.py`
- [X] T039 [P] [US2] Additional unit tests for edge cases in `tests/unit/`. Specifically test:
 1. 'Single-host-metal' handling in ingestion (T014).
 2. 'Missing atomic data' handling in curation (T013).

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `code/data/descriptors.py` to compute `size_mismatch = (solute_r - host_r) / host_r` using Metallic Radii from `constants.py`
- [ ] T018 [US2] Implement `code/models/training.py` to train Random Forest with `GridSearchCV` (5-fold cross-validation, `cv=5` explicitly overriding default, `max_depth` range [3, 10], `n_estimators` range [50, 200] as per FR-003) maximizing R².
 **Dependency**: This task MUST wait for T013 and **T051.2** to complete and consume `data/curated/filtered.csv` as the output of T012/T013 (satisfying FR-003).
 **Pre-training Check**: Before training, check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit` with "Training Error: Cannot train on synthetic data. Real data source required."
 **Note**: This task implements the GridSearch logic AND saves the best model. Uses `train_model` helper for shared logic.
 **CRITICAL**: Perform GridSearch ONLY on the training set (after `train_test_split` with `test_size=0.2, random_state=42`) to prevent data leakage. If a `MemoryError` occurs, catch it and fallback to a reduced grid search (e.g., `max_depth` range [3, 6], `n_estimators` range [50, 100]) and FLAG the result as "Memory-Constrained" (does NOT satisfy full FR-003 range).
 **Artifact**: Save the best trained model to `models/final_rf.pkl` and save **intermediate** metrics to `models/rf_metrics.json` within this task.

- [ ] T018.1 [US2] Implement `code/models/training.py` to train a **Mean-Predictor Baseline** model (predicting the mean of the training set) and calculate its R² score.
 **Dependency**: This task MUST wait for T013 and **T051.2**.
 **Pre-training Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit`.
 **Output**: Save `mean_r2` to `models/mean_metrics.json` to satisfy SC-001.
 **Note**: This task is a core requirement for SC-001, not a revision item.

- [ ] T019 [US2] Implement `code/models/training.py` to train Gradient Boosting with same GridSearch parameters (`cv=5` explicitly set, `max_depth` range [3, 10], `n_estimators` range [50, 200] as per FR-003).
 **Dependency**: This task MUST wait for T013 and **T051.2** to complete and consume `data/curated/filtered.csv` as the output of T012/T013 (satisfying FR-003).
 **Pre-training Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit`.
 **Note**: This task implements the GridSearch logic AND saves the best model. Uses `train_model` helper for shared logic.
 **CRITICAL**: Perform GridSearch ONLY on the training set (after `train_test_split` with `test_size=0.2, random_state=42`) to prevent data leakage. If a `MemoryError` occurs, catch it and fallback to a reduced grid search and FLAG the result as "Memory-Constrained" (does NOT satisfy full FR-003 range).
 **Artifact**: Save the best trained model to `models/final_gb.pkl` and save **intermediate** metrics to `models/gb_metrics.json` within this task.

- [ ] T020 [US2] Implement `code/models/training.py` to train Linear Regression and extract `size_mismatch` coefficient with p-value.
 **Dependency**: Must run after T013 and **T051.2**.
 **Pre-training Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit`.
 **Artifact**: Save the coefficient and p-value to `models/linear_coef.json`.
- [ ] T021 [US2] Implement logic to save Linear Regression coefficients to `models/linear_coef.json` (if not done in T020) and **aggregate all training metrics** into `models/metrics.json`.
 **Implementation Details**:
 1. Load `models/rf_metrics.json` (from T018), `models/gb_metrics.json` (from T019), and `models/mean_metrics.json` (from T018.1).
 2. Load `models/linear_coef.json` (from T020).
 3. **Explicitly compare** RF and GB R² scores against `mean_r2` to calculate the performance delta (R²_model - R²_mean) for both models.
 4. Aggregate into a single `models/metrics.json` with keys: `rf_r2`, `rf_rmse`, `rf_mae`, `gb_r2`, `gb_rmse`, `gb_mae`, `mean_r2`, `rf_delta`, `gb_delta`, `linear_coef`, `linear_p_value`.
 5. Use `joblib.dump` for model serialization (protocol 5).
 **Dependency**: Must run after T018, T019, T020.
 **Note**: T021 is the **single owner** of `models/metrics.json` (training metrics only). T022 writes to a separate file.
- [ ] T022 [US2] Implement `code/models/inference.py` to compute R², RMSE, MAE on held-out test set for RF and GB; save results to `models/inference_metrics.json`.
 **Implementation Details**:
 1. Load `models/final_rf.pkl` (from T018) and `models/final_gb.pkl` (from T019).
 2. Evaluate on the held-out test set (from T013 split, `test_size=0.2, random_state=42`).
 3. Save results to `models/inference_metrics.json` (NOT updating `models/metrics.json`) with keys: `rf_r2`, `rf_rmse`, `rf_mae`, `gb_r2`, `gb_rmse`, `gb_mae`.
 **Dependency**: Must run after T018, T019. **Note**: Removed dependency on T021. T022 and T021 are parallel consumers of T018/T019.
- [ ] T023 [US2] Handle edge case in `code/models/training.py` where R² < 0.1 (flag as "Low Predictive Power" in report, do not crash)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Threshold Sensitivity (Priority: P3)

**Goal**: Validate statistical significance of the `size_mismatch` coefficient and perform threshold sensitivity analysis.

**Independent Test**: Generate report confirming p < 0.05 for the coefficient and a sensitivity plot showing classification rate changes.

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_stats.py`
- [X] T025 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/validation/baseline.py` to calculate `baseline_shift` from `data/curated/filtered.csv`.
 **Logic**:
 1. **Input**: Load `data/curated/filtered.csv`.
 2. Implement a helper function `get_pure_host_baseline(host_id, curated_data)` that retrieves the activation energy for the pure host (concentration = 0) from the `data/curated/filtered.csv`.
 3. If multiple entries exist for a pure host, use the **median** value.
 4. Calculate `baseline_shift = activation_energy - pure_host_baseline` for every row.
 5. If no pure host entry exists for a given host_id, **exclude** that row from the sensitivity analysis and log a warning.
 6. Save the results to `data/curated/baseline_shifts.csv` with columns `host_id`, `solute_id`, `activation_energy`, `pure_host_baseline`, `baseline_shift`.
 **Dependency**: Must run after T013 (Curation). **Note**: This task produces the artifact required by T031. It does NOT depend on T022 (Inference).
- [ ] T030.1 [US3] Unit test for `code/validation/baseline.py` (T030) to verify baseline shift calculation.
 **Dependency**: Must run after T030.
- [ ] T026 [US3] Implement `code/validation/stats.py` to compute 95% bootstrap confidence interval for `size_mismatch` coefficient, verify p-value < 0.05 AND that the 95% bootstrap confidence interval does not cross zero, and save the results to `reports/validation_report.json`.
 **Logic**:
 1. Load the coefficient and compute CI using bootstrap resampling.
 2. **Pre-validation Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit` with "Validation Error: Cannot validate statistical significance on synthetic data."
 3. **Do NOT raise an error** if p-value >= 0.05 or CI crosses zero.
 4. **Always save** `p_value`, `ci_95_lower`, `ci_95_upper`, and `significance_verified` (boolean: True if p < 0.05 AND CI does not cross zero, False otherwise) to `reports/validation_report.json`.
 5. If `p_value >= 0.05` OR CI crosses zero, log a warning: "Statistical Significance Not Met: p-value >= 0.05 or CI crosses zero. Result reported as non-significant."
 6. **Note**: This ensures the report is generated for both positive and negative results, satisfying FR-005.
 **Dependency**: Must run after T020.
- [ ] T031 [US3] Implement `code/validation/sensitivity.py` to sweep classification threshold across a **targeted range of values** in **fine increments**.
 **Logic**:
 1. **Input**: Load `data/curated/baseline_shifts.csv` produced by T030. Verify the file exists and contains the `baseline_shift` column.
 2. Iterate thresholds across the exact range **0.45** eV to 0.55 eV in steps of **0.01** eV (11 points total).
 3. For each threshold, calculate the classification rate of "significant diffusion slowing" (where `baseline_shift > threshold`).
 4. Write the results to `reports/sensitivity_sweep.csv` with columns `threshold_eV` and `classification_rate`.
 **Dependency**: Must run after T030.
- [ ] T032 [US3] Implement `code/validation/sensitivity.py` to calculate classification stability and **verify against the ±5% threshold**.
 **Metric**: Calculate the **Range (max - min)** of the classification rates across the sweep (0.45 eV to 0.55 eV).
 **Logic**:
 1. **Load Sweep Data** from `reports/sensitivity_sweep.csv` (produced by T031).
 2. Compute `stability_metric = max(classification_rates) - min(classification_rates)`.
 3. **Threshold Check**: If `stability_metric > 0.05`, log a warning: "Stability Warning: Metric exceeds ±5% threshold. Results may be sensitive to cutoff choice." If `stability_metric <= 0.05`, log "Stability Pass: Metric within ±5% threshold."
 4. **Output**: Save the `stability_metric`, `mean_classification_rate`, and `threshold_check` (pass/fail string) to `reports/stability_metrics.json` with keys: `stability_metric`, `mean_classification_rate`, `threshold_check`.
 **Dependency**: Must run after T031.
- [ ] T033 [US3] Generate `reports/validation_report.json` containing R², RMSE, p-values, CI, and stability metrics.
 **Implementation Details**:
 1. Include keys: `rf_r2`, `gb_r2`, `mean_r2` (from T022/inference_metrics and T018.1/mean_metrics).
 2. Include keys: `p_value`, `ci_95_lower`, `ci_95_upper` (from T026).
 3. Include keys: `stability_metric`, `mean_classification_rate` (from T032).
 4. Explicitly aggregate the CI values calculated in T026 into this JSON.
 5. **Explicitly load** `models/mean_metrics.json` to ensure `mean_r2` is included.
 **Dependency**: Requires T021, T022, T026, T031, T032 completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Robustness (Addressing Review Concerns)

**Goal**: Address specific reviewer concerns regarding data streaming, robust error handling, and baseline calculation logic.

- [X] T052 [US1] Refactor `code/data/acquisition.py` to implement **streaming** for large datasets and **remove** the hardcoded size-exit logic.
 **Rationale**: The current implementation exits if the file size is too large, violating the requirement to stream large real datasets.
 **Logic**:
 1. Replace the `requests.get(...).content` approach with `requests.get(..., stream=True)`.
 2. Use `pandas.read_csv` with `chunksize` parameter or `datasets.load_dataset(..., streaming=True)` if available for the target source.
 3. Process data in chunks to compute statistics or filter rows without loading the entire file into RAM.
 4. **Remove** the "Size Check" logic that raises `SystemExit` if the dataset is large.
 5. **Remove** the fallback logic that saves a `data_insufficient_flag.json` for small counts; instead, let the downstream curation step (T012) handle the count check.
 6. If streaming is not possible for a specific source, fall back to a well-defined **real sample** (e.g., first 1000 rows) and log the sampling rule explicitly in `data/curated/data_provenance.json`.
 7. Ensure the `try/except` block for network errors **does not** fallback to synthetic data; it must raise an exception to fail the build loudly.

- [X] T053 [US1] Refactor `code/data/curation.py` to ensure **strict separation** of real and mock data handling and improve logging of exclusion reasons.
 **Rationale**: Reviewers noted potential confusion between mock data used for testing and real data used for validation.
 **Logic**:
 1. Add a strict check at the start of `curation.py`: If `data_provenance.json` indicates `source_type == 'mock'`, the script should run in "validation mode" and skip statistical significance checks later.
 2. Enhance the exclusion logging in `data/logs/exclusions.log` to include the **exact row content** (truncated) for excluded rows to aid debugging.
 3. Ensure `errors/missing_atomic_data.csv` is created even if no rows are missing (empty file with headers) to satisfy contract tests.

- [ ] T054 [US3] [REMOVED - Logic moved to T030]

- [X] T055 [US2] Add a **robustness check** task to `code/models/training.py` to handle the case where the dataset is too small for a proper train/test split.
 **Rationale**: If the curated dataset has fewer than 20 rows, a standard 80/20 split is invalid.
 **Logic**:
 1. Add a check: If `len(curated_data) < 20`, raise a `SystemExit` with "Data Insufficient: Dataset too small for train/test split (N < 20)."
 2. If `20 <= len(curated_data) < 50`, log a warning "Small Dataset Warning: Using Leave-One-Out Cross-Validation (LOOCV) instead of standard split."
 3. Modify the `GridSearchCV` and model training logic to automatically switch to `cv=LeaveOneOut()` if the dataset size is between 20 and 50.
 4. Ensure the `data_provenance.json` is updated to record the `cv_strategy` used (e.g., "standard_split" or "LOOCV").

- [X] T056 [General] Update `code/config.py` to include a `DATA_STREAMING_CONFIG` section with explicit chunk sizes and sampling rules.
 **Rationale**: Centralize configuration for data handling strategies to ensure consistency across acquisition and curation tasks.
 **Logic**:
 1. Add `STREAMING_CHUNK_SIZE = 1000` (rows).
 2. Add `MAX_MEMORY_MB = 6000` (limit for RAM usage).
 3. Add `MIN_DATASET_SIZE_FOR_SPLIT = 20`.
 4. Add `MIN_DATASET_SIZE_FOR_VALIDATION = 50`.
 5. Ensure all data-loading tasks reference these constants instead of hardcoded values.

- [ ] T057 [US1] Implement **strict data source verification** in `code/data/acquisition.py` to enforce the "Fail Loudly" policy against synthetic fallbacks.
 **Rationale**: To prevent the pipeline from silently substituting synthetic data when real data fetches fail, which is the primary cause of fabrication rejection.
 **Logic**:
 1. Remove any `try/except` blocks in the data fetch logic that catch network errors and return synthetic/mock data.
 2. If a fetch to a verified real URL fails (timeout, client error, connection error), raise a `DataFetchError` exception with a clear message: "Real data fetch failed. Pipeline cannot proceed with synthetic data."
 3. Ensure the `acquisition.py` script exits immediately upon this error, preventing any downstream tasks from running with fake data.
 4. Add a unit test in `tests/unit/test_acquisition.py` that simulates a network failure and asserts the `DataFetchError` is raised and no mock data is generated.

- [ ] T058 [US1] Implement **explicit streaming logic** for large real datasets in `code/data/acquisition.py` using `datasets` library streaming.
 **Rationale**: To handle datasets larger than the 7GB RAM limit of the free runner without fabricating data or using toy subsets.
 **Logic**:
 1. Update `code/data/acquisition.py` to use `datasets.load_dataset(..., streaming=True)` for supported sources (e.g., HuggingFace datasets).
 2. For CSV sources, implement a chunked reading loop using `pandas.read_csv(..., chunksize=1000)` to process rows in batches.
 3. Accumulate filtered rows into a temporary file or a growing list (if memory permits for the filtered subset) without loading the entire raw file.
 4. If the source does not support streaming and the file size exceeds `MAX_MEMORY_MB` (from T056), automatically switch to a **real sample** strategy: read the first N rows (where N is defined by `MIN_DATASET_SIZE_FOR_VALIDATION` or a fixed safe limit) and log the sampling rule in `data/curated/data_provenance.json`.
 5. Ensure the "Real Sample" fallback is explicitly documented as a limitation, not a fabrication.

- [X] T059 [US3] [REMOVED - Spec defines single deterministic sweep]

- [X] T060 [US2] Implement **automated hyperparameter fallback** in `code/models/training.py` for memory-constrained environments.
 **Rationale**: To ensure the training pipeline completes successfully even if the full GridSearch exceeds the 7GB RAM limit, without sacrificing the scientific validity of the model.
 **Logic**:
 1. Wrap the `GridSearchCV` execution in a `try/except MemoryError` block.
 2. If a `MemoryError` is caught, log a warning: "Memory limit exceeded during GridSearch. Switching to reduced grid search."
 3. Automatically reduce the grid search space (e.g., `max_depth` [low, high], `n_estimators` [50, 100]) and re-run the search.
 4. If the reduced search also fails, fall back to a single model with default parameters and log: "GridSearch failed. Using default model parameters."
 5. Record the `grid_search_strategy` (full, reduced, default) in `models/metrics.json` and `data/curated/data_provenance.json` for transparency.

- [X] T061 [US1] Add **data provenance validation** to `tests/contract/test_data.py` to ensure all required provenance fields are present and valid.
 **Rationale**: To guarantee that the `data_provenance.json` file is correctly populated and contains all necessary information for reproducibility and verification.
 **Logic**:
 1. Extend the existing schema validation in `tests/contract/test_data.py` to include checks for `data_provenance.json`.
 2. Verify that `source_type`, `url`, `constants_version`, `row_counts`, `filter_criteria`, and `cv_strategy` (if applicable) are present and valid.
 3. Ensure that `source_type` is either "real" or "mock" and that the `url` field is present only if `source_type` is "real".
 4. Fail the test if any required field is missing or invalid, ensuring that downstream tasks cannot proceed with incomplete provenance data.

**Checkpoint**: All reviewer concerns addressed; pipeline is robust to data size variations and edge cases.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence