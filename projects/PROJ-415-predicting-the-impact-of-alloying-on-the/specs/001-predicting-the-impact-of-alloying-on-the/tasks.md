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
- [X] T003.1 [P] Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Config**: `line-length = 88`, `target-version = 'py311'`, `select = ['E', 'F', 'W', 'I']`. **Note**: This task creates the configuration files required by T003.
- [X] T003.2 [P] Run initial lint/format check on the empty project structure to verify configuration. **Dependency**: Must run after T003.1. **Note**: Removed [P] tag as this depends on T003.1.
- [X] T004 Implement `code/config.py` with global constants, random seeds, and path definitions
- [X] T005 Implement `code/utils/constants.py` with versioned periodic table data (Metallic Radii, Electronegativity)
- [X] T006 Implement `code/utils/logging.py` for standardized logging and error tracking
- [X] T007 Implement `code/data/checksum.py` to checksum files under `data/` using `hashlib.sha256` and store hashes in `data/checksums.json`. **Note**: Upgraded from MD5 to SHA-256 to satisfy Constitution Principle V (Versioning Discipline) and Principle III (Data Hygiene).
- [X] T008 [US1] Implement `code/data/acquisition.py` to fetch REAL diffusion data from NIST/Materials Project/Literature sources.
 **CRITICAL INSTRUCTIONS**:
 1. Use `requests` to fetch from a verified NIST CSV URL. **Primary URL**: `. **Fallback**: Iterate through a list of verified URLs: `['', 'https://materialsproject.org/static/diffusion_data_v1.csv']` if the primary fails.
 2. **Pre-flight Check**: Before fetching, perform a HEAD request to verify the URL is reachable. If unreachable after retries (3 retries, 5s backoff, timeout=30s), raise `SystemExit` with "Data Fetch Failed: URL unreachable".
 3. **Size Check**: If the fetched dataset size (Content-Length or file size) exceeds a predefined threshold, raise `SystemExit` with "Data Size Error: Dataset exceeds size limit. Halting per Constitution Principle VI." **DO NOT** attempt streaming or chunked processing.
 4. **Data Validation**: If the fetched RAW dataset contains a small number of entries, **DO NOT** exit. Save a flag `data/raw/data_insufficient_flag.json` with reason "N < 50 (Raw)", log a warning, and proceed to curation. The pipeline will handle the low count in downstream steps (T013/T014) which may exit if the *curated* count is < 50.
 5. Save output to `data/raw/fetched_diffusion.csv`.
 6. Write a `data/raw/source_metadata.json` file containing the exact URL used and a timestamp.
 7. No PDF parsing, external citation validation, or "Reference-Validator Agent" logic is required or permitted.
 8. **Note**: This task MUST run AFTER T008.5 to ensure the schema exists for validation.
 9. **Note**: This task is NOT parallel-safe; ensure it runs sequentially after T008.5.
- [X] T008.5 [US1] Generate `contracts/diffusion_record.schema.yaml` defining the `DiffusionRecord` entity schema.
 **Logic**:
 1. Define schema with fields:
 - `host_id`: string, required
 - `solute_id`: string, required
 - `concentration`: number (float), required, min: 0
 - `activation_energy`: number (float), required, min: 0
 - `crystal_structure`: string, required, enum: ["FCC"]
 - `diffusion_mode`: string, required, enum: ["self"]
 2. Save to `contracts/diffusion_record.schema.yaml`.
 **Note**: This artifact is required by T008 and T009. This task MUST run before T008 and T009. Updated to restrict enums to match FR-001 filtering criteria.
- [X] T009 [US1] Implement `tests/contract/test_schema.py` to validate data structure against `contracts/diffusion_record.schema.yaml` for the `DiffusionRecord` entity. **Status**: [X]. **Dependency**: This task MUST wait for T008.5 (schema generation) and T008 (data fetch). **Note**: Removed [P] tag as this depends on T008's output.
- [X] T010 Implement `tests/unit/test_constants.py` to verify periodic table data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Curation (Priority: P1) 🎯 MVP

**Goal**: Load raw diffusion datasets, filter for FCC self-diffusion, and handle missing values.

**Independent Test**: Run ingestion script against a mock CSV with mixed structures (FCC, BCC, HCP) and verify output contains ONLY FCC self-diffusion entries with standardized units.

### Tests for User Story 1

- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_data.py`
- [X] T012 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py`. **Note**: This test uses MOCK data ONLY for verifying logic flow and error handling, explicitly separated from the real data hypothesis validation in T008/T013.
- [X] T012.1 [P] [US1] Implement `code/data/mock_generator.py` to generate a synthetic mock dataset containing mixed crystal structures (FCC, BCC, HCP) and diffusion modes for the Independent Test.
 **Outputs**:
 1. Generate `data/mock/mock_diffusion.csv` with at least 100 rows.
 2. Ensure the file includes valid and invalid entries (e.g., BCC, missing concentration) to test filtering logic.
 3. This task provides the specific mock data required by the spec's "Independent Test" for US1, distinct from the real data fetched in T008.
- [X] T017 [P] [US1] Add validation script `tests/unit/test_ingestion.py` to verify filtering logic on mixed-structure mock data.
- [X] T017.1 [US1] Add validation script `tests/unit/test_ingestion_real.py` to run the ingestion pipeline against the MOCK data from T012.1 to verify filtering on mock data. **Dependency**: Must run after T012.1. **Note**: This task uses MOCK data to satisfy the spec's "Independent Test" requirement, avoiding non-deterministic dependency on real data fetch success.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data/ingestion.py` to load CSVs, filter `crystal_structure == config.FILTER_CRITERIA['crystal_structure']` and `diffusion_mode == config.FILTER_CRITERIA['diffusion_mode']`, and convert units to eV/atom. **Note**: Uses `config.FILTER_CRITERIA` to ensure Single Source of Truth compliance. **CRITICAL**: After filtering, if the resulting dataset has fewer than 50 entries, **exit with code 1** and log "Data Insufficient: Filtered count < 50".
- [X] T014 [US1] Implement `code/data/curation.py` to exclude rows with missing solute concentration or missing atomic radii.
 **Outputs**:
 1. Log exclusions to `data/logs/exclusions.log` (CSV format with `row_id`, `reason_code`). Explicitly record the **count of excluded rows as the first line** (e.g., `# EXCLUSION_COUNT: 5`).
 2. Append records for missing atomic radii to `errors/missing_atomic_data.csv` (CSV with `solute_symbol`, `missing_attribute`).
 3. Output the final curated dataset to `data/curated/filtered.csv`.
 **CRITICAL**: This task MUST create `errors/missing_atomic_data.csv` if any atomic data is missing. Log concentration exclusions with reason code 'MISSING_CONCENTRATION'.
 **Dependency**: This task produces the `data/curated/filtered.csv` artifact required by Phase 4 tasks.
- [X] T015 [US1] Implement edge case handling in `code/data/ingestion.py` for single-host-metal datasets: fallback to random split and log the specific warning: 'Stratification by host metal was not possible due to single-class data.'
- [X] T051 [US1] [Moved to Phase 3] Refactor `code/data/curation.py` to explicitly write a `data/curated/data_provenance.json` file.
 **Logic**:
 1. Read `data/raw/source_metadata.json` (from T008) to extract the exact URL or source identifier.
 2. Record the `constants.py` version hash used for descriptor calculation.
 3. Record the total number of rows in `data/raw/fetched_diffusion.csv` before filtering.
 4. Record the exact number of rows in `data/curated/filtered.csv` after filtering.
 5. Include a `filter_criteria` object detailing `crystal_structure` and `diffusion_mode` values used.
 6. **CRITICAL**: Include a `source_type` field set to "real" if the URL is from the verified list, or "mock" if from mock generator.
 7. **Note**: This task is now in Phase 3.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Compute atomic descriptors, train RF/GB models with GridSearch, and train Linear Regression for statistical inference.

**Independent Test**: Verify `size_mismatch` calculation matches manual math; confirm RF/GB/Linear train on CPU without CUDA errors and output metrics.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for `size_mismatch` calculation in `tests/unit/test_descriptors.py`
- [X] T019 [P] [US2] Unit test for model training (CPU-only check) in `tests/unit/test_models.py`
- [X] T039 [P] [US2] Additional unit tests for edge cases in `tests/unit/`. Specifically test:
 1. 'Single-host-metal' handling in ingestion (T015).
 2. 'Missing atomic data' handling in curation (T014).

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/data/descriptors.py` to compute `size_mismatch = (solute_r - host_r) / host_r` using Metallic Radii from `constants.py`
- [X] T021 [US2] Implement `code/models/training.py` to train Random Forest with `GridSearchCV` (5-fold cross-validation, `cv=5` explicitly overriding default, `max_depth` range [3, 10], `n_estimators` range [50, 200] as per FR-003) maximizing R².
 **Dependency**: This task MUST wait for T014 and **T051** to complete and consume `data/curated/filtered.csv` as the output of T013/T014 (satisfying FR-003).
 **Pre-training Check**: Before training, check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit` with "Training Error: Cannot train on synthetic data. Real data source required."
 **Note**: This task implements the GridSearch logic AND saves the best model. Uses `train_model` helper for shared logic.
 **CRITICAL**: Perform GridSearch ONLY on the training set (after `train_test_split` with `test_size=0.2, random_state=42`) to prevent data leakage. If a `MemoryError` occurs, raise `SystemExit` with "Memory Error: GridSearch exceeds resource limits" instead of reducing search space. **Implementation Detail**: The MemoryError handling must be a distinct `try/except` block wrapping the `GridSearchCV.fit()` call.
 **Artifact**: Save the best trained model to `models/final_rf.pkl` and save **intermediate** metrics to `models/rf_metrics.json` within this task.

 **MemoryError Handling**:
 1. Wrap the `GridSearchCV.fit()` call in a distinct `try/except MemoryError` block.
 2. If caught, raise `SystemExit("Memory Error: GridSearch exceeds resource limits")`.
 3. Do NOT reduce grid size or catch the error silently.

- [X] T021.1 [US2] Implement `code/models/training.py` to train a **Mean-Predictor Baseline** model (predicting the mean of the training set) and calculate its R² score.
 **Dependency**: This task MUST wait for T014 and **T051**.
 **Pre-training Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit`.
 **Output**: Save `mean_r2` to `models/mean_metrics.json` to satisfy SC-001.
 **Note**: This task is a core requirement for SC-001, not a revision item.
 **MemoryError Handling**: Wrap the training call in a `try/except MemoryError` block. If caught, raise `SystemExit("Memory Error: Mean-Predictor training failed")`.

- [X] T022 [US2] Implement `code/models/training.py` to train Gradient Boosting with same GridSearch parameters (`cv=5` explicitly set, `max_depth` range [3, 10], `n_estimators` range [50, 200] as per FR-003).
 **Dependency**: This task MUST wait for T014 and **T051** to complete and consume `data/curated/filtered.csv` as the output of T013/T014 (satisfying FR-003).
 **Pre-training Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit`.
 **Note**: This task implements the GridSearch logic AND saves the best model. Uses `train_model` helper for shared logic.
 **CRITICAL**: Perform GridSearch ONLY on the training set (after `train_test_split` with `test_size=0.2, random_state=42`) to prevent data leakage. If a `MemoryError` occurs, raise `SystemExit` with "Memory Error: GridSearch exceeds resource limits" instead of reducing search space. **Implementation Detail**: The MemoryError handling must be a distinct `try/except` block wrapping the `GridSearchCV.fit()` call.
 **Artifact**: Save the best trained model to `models/final_gb.pkl` and save **intermediate** metrics to `models/gb_metrics.json` within this task.

 **MemoryError Handling**:
 1. Wrap the `GridSearchCV.fit()` call in a distinct `try/except MemoryError` block.
 2. If caught, raise `SystemExit("Memory Error: GridSearch exceeds resource limits")`.
 3. Do NOT reduce grid size or catch the error silently.

- [X] T023 [US2] Implement `code/models/training.py` to train Linear Regression and extract `size_mismatch` coefficient with p-value.
 **Dependency**: Must run after T014 and **T051**.
 **Pre-training Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit`.
 **Artifact**: Save the coefficient and p-value to `models/linear_coef.json`.
- [X] T024 [US2] Implement logic to save Linear Regression coefficients to `models/linear_coef.json` (if not done in T023) and **aggregate all training metrics** into `models/metrics.json`.
 **Implementation Details**:
 1. Load `models/rf_metrics.json` (from T021), `models/gb_metrics.json` (from T022), and `models/mean_metrics.json` (from T021.1).
 2. Load `models/linear_coef.json` (from T023).
 3. **Explicitly compare** RF and GB R² scores against `mean_r2` to calculate the performance delta (R²_model - R²_mean) for both models.
 4. Aggregate into a single `models/metrics.json` with keys: `rf_r2`, `rf_rmse`, `rf_mae`, `gb_r2`, `gb_rmse`, `gb_mae`, `mean_r2`, `rf_delta`, `gb_delta`, `linear_coef`, `linear_p_value`.
 5. Use `joblib.dump` for model serialization (protocol 5).
 **Dependency**: Must run after T021, T022, T023.
 **Note**: T024 is the **single owner** of `models/metrics.json` (training metrics only). T025 writes to a separate file.
- [X] T025 [US2] Implement `code/models/inference.py` to compute R², RMSE, MAE on held-out test set for RF and GB; save results to `models/inference_metrics.json`.
 **Implementation Details**:
 1. Load `models/final_rf.pkl` (from T021) and `models/final_gb.pkl` (from T022).
 2. Evaluate on the held-out test set (from T014 split, `test_size=0.2, random_state=42`).
 3. Save results to `models/inference_metrics.json` (NOT updating `models/metrics.json`) with keys: `rf_r2`, `rf_rmse`, `rf_mae`, `gb_r2`, `gb_rmse`, `gb_mae`.
 **Dependency**: Must run after T021, T022. **Note**: Removed dependency on T024. T025 and T024 are parallel consumers of T021/T022.
- [X] T026 [US2] Handle edge case in `code/models/training.py` where R² < 0.1 (flag as "Low Predictive Power" in report, do not crash)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Threshold Sensitivity (Priority: P3)

**Goal**: Validate statistical significance of the `size_mismatch` coefficient and perform threshold sensitivity analysis.

**Independent Test**: Generate report confirming p < 0.05 for the coefficient and a sensitivity plot showing classification rate changes.

### Tests for User Story 3

- [X] T027 [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_stats.py`
- [X] T028 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/validation/stats.py` to compute 95% bootstrap confidence interval for `size_mismatch` coefficient, verify p-value < 0.05 AND that the 95% bootstrap confidence interval does not cross zero, and save the results to `reports/validation_report.json`.
 **Logic**:
 1. Load the coefficient and compute CI using bootstrap resampling.
 2. **Pre-validation Check**: Check `data/curated/data_provenance.json`. If `source_type != 'real'`, raise `SystemExit` with "Validation Error: Cannot validate statistical significance on synthetic data."
 3. **Do NOT raise an error** if p-value >= 0.05 or CI crosses zero.
 4. **Always save** `p_value`, `ci_95_lower`, `ci_95_upper`, and `significance_verified` (boolean: True if p < 0.05 AND CI does not cross zero, False otherwise) to `reports/validation_report.json`.
 5. If `p_value >= 0.05` OR CI crosses zero, log a warning: "Statistical Significance Not Met: p-value >= 0.05 or CI crosses zero. Result reported as non-significant."
 6. **Note**: This ensures the report is generated for both positive and negative results, satisfying FR-005.
 **Dependency**: Must run after T023.
- [X] T031 [US3] Implement `code/validation/sensitivity.py` to sweep classification threshold across a **targeted range of values** in **fine increments**.
 **Logic**:
 1. **Input**: Load `data/curated/baseline_shifts.csv` produced by T025. Verify the file exists and contains the `baseline_shift` column.
 2. Iterate thresholds across a narrow range around the standard decision boundary in fine-grained steps.
 3. For each threshold, calculate the classification rate of "significant diffusion slowing" (where `baseline_shift > threshold`).
 4. Write the results to `reports/sensitivity_sweep.csv` with columns `threshold_eV` and `classification_rate`.
 **Dependency**: Must run after T025.
- [X] T032 [US3] Implement `code/validation/sensitivity.py` to calculate classification stability and **verify against the ±5% threshold**.
 **Metric**: Calculate the **Standard Deviation (SD)** of the classification rates across the sweep (0.45 eV to 0.55 eV).
 **Logic**:
 1. **Load RMSE** from `models/inference_metrics.json` (produced by T025).
 2. **Load Sweep Data** from `reports/sensitivity_sweep.csv` (produced by T031).
 3. Compute `stability_metric = SD of classification rates`.
 4. **Threshold Check**: If `stability_metric > 0.05`, log a warning: "Stability Warning: Metric exceeds ±5% threshold. Results may be sensitive to cutoff choice." If `stability_metric <= 0.05`, log "Stability Pass: Metric within ±5% threshold."
 5. **Output**: Save the SD, mean classification rate, `stability_metric`, and `threshold_check` (pass/fail string) to `reports/stability_metrics.json` with keys: `stability_metric`, `sd_classification_rate`, `mean_classification_rate`, `threshold_check`.
 **Dependency**: Must run after T031 and T025.
- [X] T034 [US3] Generate `reports/validation_report.json` containing R², RMSE, p-values, CI, and stability metrics.
 **Implementation Details**:
 1. Include keys: `rf_r2`, `gb_r2`, `mean_r2` (from T025/inference_metrics).
 2. Include keys: `p_value`, `ci_95_lower`, `ci_95_upper` (from T029).
 3. Include keys: `stability_sd`, `mean_classification_rate` (from T032).
 4. Explicitly aggregate the CI values calculated in T029 into this JSON.
 **Dependency**: Requires T024, T025, T029, T031, T032 completion.

**Checkpoint**: All user stories should now be independently functional