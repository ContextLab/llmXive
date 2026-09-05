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
- [X] T003.1 Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Note**: This task creates the configuration files required by T003.
- [X] T003.2 Run initial lint/format check on the empty project structure to verify configuration. **Dependency**: Must run after T003.1.
- [X] T004 Implement `code/config.py` with global constants, random seeds, and path definitions
- [X] T005 Implement `code/utils/constants.py` with versioned periodic table data (Metallic Radii, Electronegativity)
- [X] T006 Implement `code/utils/logging.py` for standardized logging and error tracking
- [X] T007 Implement `code/data/checksum.py` to checksum files under `data/` using `hashlib.sha256` and store hashes in `data/checksums.json`. **Note**: Upgraded from MD5 to SHA-256 to satisfy Constitution Principle V (Versioning Discipline) and Principle III (Data Hygiene).
- [X] T008 Implement `code/data/acquisition.py` to fetch REAL diffusion data from NIST/Materials Project/Literature sources.
 **CRITICAL INSTRUCTIONS**:
 1. Use `requests` to fetch from a verified NIST CSV URL.
 2. If the URL is unreachable, raise `SystemExit` with "Data Fetch Failed: URL unreachable".
 3. **Large Dataset Handling**: If the fetched dataset size exceeds 10MB, do NOT immediately halt. Instead, invoke the streaming logic from T058 to process the data in chunks. Only raise `SystemExit` if streaming fails or data is insufficient (N < 50).
 4. If the fetched dataset contains fewer than 50 valid entries (after streaming/filtering), save a flag `data/raw/data_insufficient_flag.json` with reason "N < 50", log the event, and exit with code 0 (success) to allow the pipeline to proceed to a "Low Predictive Power" state.
 5. Save output to `data/raw/fetched_diffusion.csv` (or chunked equivalent).
 6. Write a `data/raw/source_metadata.json` file containing the exact URL used and a timestamp.
 7. No PDF parsing, external citation validation, or "Reference-Validator Agent" logic is required or permitted.
 8. This task is NOT parallel-safe; ensure it runs sequentially before dependent tasks.
- [ ] T008.5 [P] Generate `contracts/diffusion_record.schema.yaml` defining the `DiffusionRecord` entity schema.
 **Logic**:
 1. Define schema with fields: `host_id`, `solute_id`, `concentration`, `activation_energy`, `crystal_structure`, `diffusion_mode`.
 2. Save to `contracts/diffusion_record.schema.yaml`.
 **Note**: This artifact is required by T009.
- [ ] T009 [US1] Implement `tests/contract/test_schema.py` to validate data structure against `contracts/diffusion_record.schema.yaml` for the `DiffusionRecord` entity
 **Dependency**: This task MUST wait for T008.5 (schema generation) and T008 (data fetch).
 **Note**: Removed [P] tag as this depends on T008's output.
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
 **Dependency**: This task MUST depend on T012.1 to use the generated mock dataset.
 **Note**: This test uses MOCK data ONLY for verifying logic flow, explicitly separated from the real data hypothesis validation.
- [X] T017.1 [US1] Add validation script `tests/unit/test_ingestion_real.py` to run the ingestion pipeline against the REAL fetched data from T008 (`data/raw/fetched_diffusion.csv`) to verify filtering on real-world noise.
 **Dependency**: Must run after T008.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data/ingestion.py` to load CSVs, filter `crystal_structure == config.FILTER_CRITERIA['crystal_structure']` and `diffusion_mode == config.FILTER_CRITERIA['diffusion_mode']`, and convert units to eV/atom. **Note**: Uses `config.FILTER_CRITERIA` to ensure Single Source of Truth compliance.
- [X] T014 [US1] Implement `code/data/curation.py` to exclude rows with missing solute concentration or missing atomic radii.
 **Outputs**:
 1. Log exclusions to `data/logs/exclusions.log` (CSV format with `row_id`, `reason_code`). Explicitly record the **count of excluded rows as the first line** (e.g., `# EXCLUSION_COUNT: 5`).
 2. Append records for missing atomic radii to `errors/missing_atomic_data.csv` (CSV with `solute_symbol`, `missing_attribute`).
 3. Output the final curated dataset to `data/curated/filtered.csv`.
 **CRITICAL**: This task MUST create `errors/missing_atomic_data.csv` if any atomic data is missing. Log concentration exclusions with reason code 'MISSING_CONCENTRATION'.
 **Dependency**: This task produces the `data/curated/filtered.csv` artifact required by Phase 4 tasks.
- [X] T015 [US1] Implement edge case handling in `code/data/ingestion.py` for single-host-metal datasets: fallback to random split and log the specific warning: 'Stratification by host metal was not possible due to single-class data.'

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
 **Dependency**: This task MUST wait for T014 to complete and consume `data/curated/filtered.csv` as the output of T013/T014 (satisfying FR-003).
 **Note**: This task implements the GridSearch logic AND saves the best model.
 **CRITICAL**: Perform GridSearch ONLY on the training set (after `train_test_split` with `test_size=0.2, random_state=42`) to prevent data leakage. If a `MemoryError` occurs, raise `SystemExit` with "Memory Error: GridSearch exceeds resource limits" instead of reducing search space.
 **Artifact**: Save the best trained model to `models/final_rf.pkl` and save **intermediate** metrics to `models/rf_metrics.json` within this task.
- [X] T021.1 [US2] Implement `code/models/training.py` to train a **Mean-Predictor Baseline** model (predicting the mean of the training set) and calculate its R² score.
 **Dependency**: Must run after T014 (curated data).
 **Output**: Save `mean_r2` to `models/mean_metrics.json` to satisfy SC-001.
 **Note**: This task is a core requirement for SC-001, not a revision item.
- [X] T022 [US2] Implement `code/models/training.py` to train Gradient Boosting with same GridSearch parameters (`cv=5` explicitly set, `max_depth` range [3, 10], `n_estimators` range [50, 200] as per FR-003).
 **Dependency**: This task MUST wait for T014 to complete and consume `data/curated/filtered.csv` as the output of T013/T014 (satisfying FR-003).
 **Note**: This task implements the GridSearch logic AND saves the best model.
 **CRITICAL**: Perform GridSearch ONLY on the training set (after `train_test_split` with `test_size=0.2, random_state=42`) to prevent data leakage. If a `MemoryError` occurs, raise `SystemExit` with "Memory Error: GridSearch exceeds resource limits" instead of reducing search space.
 **Artifact**: Save the best trained model to `models/final_gb.pkl` and save **intermediate** metrics to `models/gb_metrics.json` within this task.
- [X] T023 [US2] Implement `code/models/training.py` to train Linear Regression and extract `size_mismatch` coefficient with p-value.
 **Artifact**: Save the coefficient and p-value to `models/linear_coef.json`.
- [X] T024 [US2] Implement logic to save Linear Regression coefficients to `models/linear_coef.json` (if not done in T023) and **aggregate all training metrics** into `models/metrics.json`.
 **Implementation Details**:
 1. Load `models/rf_metrics.json` (from T021), `models/gb_metrics.json` (from T022), and `models/mean_metrics.json` (from T021.1).
 2. Load `models/linear_coef.json` (from T023).
 3. Aggregate into a single `models/metrics.json` with keys: `rf_r2`, `rf_rmse`, `rf_mae`, `gb_r2`, `gb_rmse`, `gb_mae`, `mean_r2`, `linear_coef`, `linear_p_value`.
 4. Use `joblib.dump` for model serialization (protocol 5).
 **Dependency**: Must run after T021, T022, T021.1, T023.
 **Note**: T024 is the **single owner** of `models/metrics.json` (training metrics only). T025 writes to a separate file.
- [X] T025 [US2] Implement `code/models/inference.py` to compute R², RMSE, MAE on held-out test set for RF and GB; save results to `models/inference_metrics.json`.
 **Implementation Details**:
 1. Load `models/final_rf.pkl` (from T021) and `models/final_gb.pkl` (from T022).
 2. Evaluate on the held-out test set (from T014 split, `test_size=0.2, random_state=42`).
 3. Save results to `models/inference_metrics.json` (NOT updating `models/metrics.json`) with keys: `rf_r2`, `rf_rmse`, `rf_mae`, `gb_r2`, `gb_rmse`, `gb_mae`.
 **Dependency**: Must run after T021, T022, T024.
 **Note**: T025 is the **single owner** of `models/inference_metrics.json`. This resolves the race condition with T024.
- [X] T026 [US2] Handle edge case in `code/models/training.py` where R² < 0.1 (flag as "Low Predictive Power" in report, do not crash)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Threshold Sensitivity (Priority: P3)

**Goal**: Validate statistical significance of the `size_mismatch` coefficient and perform threshold sensitivity analysis.

**Independent Test**: Generate report confirming p < 0.05 for the coefficient and a stability plot for thresholds 0.45–0.55 eV.

### Tests for User Story 3

- [X] T027 [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_stats.py`
- [X] T028 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/validation/stats.py` to compute 95% bootstrap confidence interval for `size_mismatch` coefficient, verify p-value < 0.05 AND that the 95% bootstrap confidence interval does not cross zero, and save the results to `reports/validation_report.json`.
 **Logic**:
 1. Load the coefficient and compute CI using bootstrap resampling.
 2. Verify `p_value < 0.05` AND `ci_lower > 0` OR `ci_upper < 0` (non-zero crossing).
 3. If verification fails, raise an `AssertionError` with message "Statistical significance not met".
 4. Save `p_value`, `ci_95_lower`, `ci_95_upper` to `reports/validation_report.json`.
 **Dependency**: Must run after T023 (Linear Regression training).
- [X] T031 [US3] Implement `code/validation/sensitivity.py` to define baseline shift: `predicted_E_solute - measured_E_pure_host` (Experimental Ground Truth).
 **Logic**:
 1. Load `data/curated/filtered.csv`.
 2. For each solute, use the **predicted** activation energy from the trained model (T021/T022).
 3. Find the **measured** activation energy of the pure host metal at 0 at.% from `data/curated/filtered.csv`.
 4. If multiple 0 at.% rows exist for the same host, calculate the mean of their activation energies.
 5. If the 0 at.% row for the pure host is missing, raise `SystemExit` with message "Baseline Error: Missing 0 at.% host data. Interpolation is not permitted per spec."
 6. **Output**: Write the calculated baseline shifts to `data/curated/baseline_shifts.csv` with columns: `solute_id`, `host_id`, `predicted_E_solute`, `measured_E_pure_host`, `baseline_shift`.
 **Dependency**: Consumes `data/curated/filtered.csv` (from T014).
 **Note**: This task MUST produce the `data/curated/baseline_shifts.csv` artifact required by T032.
- [X] T032 [US3] Implement `code/validation/sensitivity.py` to sweep classification threshold across the **exact range 0.45 eV to 0.55 eV in 0.01 eV increments**.
 **Logic**:
 1. **Input**: Load `data/curated/baseline_shifts.csv` produced by T031. Verify the file exists and contains the `baseline_shift` column.
 2. Iterate thresholds: 0.45, 0.46,..., 0.55.
 3. For each threshold, calculate the classification rate of "significant diffusion slowing" (where `baseline_shift > threshold`).
 4. Write the results to `reports/sensitivity_sweep.csv` with columns `threshold_eV` and `classification_rate`.
 **Dependency**: Must run after T031. **Critical**: This task depends on the artifact `data/curated/baseline_shifts.csv` from T031.
- [X] T033 [US3] Implement logic in `code/validation/sensitivity.py` to calculate classification stability.
 **Metric**: Calculate the **Standard Deviation (SD)** of the classification rates across the sweep (0.45 to 0.55 eV), then **divide by the Model RMSE** (retrieved from `models/inference_metrics.json` produced by T025).
 **Output**: Save the normalized SD, mean classification rate, and `stability_metric` (normalized SD) to `reports/stability_metrics.json`.
 **Dependency**: Explicitly consumes `models/inference_metrics.json` (produced by T025) and `reports/sensitivity_sweep.csv` (produced by T032).
 **CRITICAL**: If the number of unique `baseline_shift` values is < 5, raise `SystemExit` with "Stability Error: Insufficient variance in baseline shifts. Metric cannot be computed."
 **Note**: This task is NOT parallel-safe; it must run after T032 and T025.
- [X] T034 [US3] Generate `reports/validation_report.json` containing R², RMSE, p-values, CI, and stability metrics.
 **Implementation Details**:
 1. Include keys: `rf_r2`, `gb_r2`, `mean_r2` (from T025/inference_metrics).
 2. Include keys: `p_value`, `ci_95_lower`, `ci_95_upper` (from T029).
 3. Include keys: `stability_sd`, `mean_classification_rate` (from T033).
 4. Explicitly aggregate the CI values calculated in T029 into this JSON.
 **Dependency**: Requires T024, T025, T029, T031, T032, T033 completion. **Note**: Phase 5 tasks are strictly sequential after Phase 4 completion.
- [X] T035 [US3] Implement `code/main.py` orchestration to run full pipeline: Ingestion → Features → Training → Validation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 Code cleanup and refactoring of `code/models/training.py` for readability
- [ ] T038 Refactor `code/models/training.py` to use `n_jobs=-1` (parallel processing) in `GridSearchCV`.
 **Action**: Refactor `code/models/training.py` to use `n_jobs=-1`.
 **Dependency**: Must run after T035.
- [ ] T038.1 Implement `code/utils/performance_logger.py` to measure and log total pipeline runtime.
 **Metric**: Measure **total pipeline runtime** (Ingestion + Training + Validation) and log it to `reports/performance_log.json`. Assert `total_runtime < 6h`. If exceeded, log a warning but do not crash.
 **Dependency**: Must run after T035 to capture total runtime.
- [X] T040 Run `quickstart.md` validation and verify all artifacts are checksummed
- [X] T041 [US2] Implement `tests/integration/test_model_training.py` to verify end-to-end training flow from curated data to saved model artifacts (addresses review concern on missing integration coverage for T021-T025)
- [X] T042 [US3] Implement `tests/integration/test_sensitivity_analysis.py` to verify the full threshold sweep and stability calculation logic (addresses review concern on missing integration coverage for T031-T033)
- [X] T043 [US1] Add explicit contract test in `tests/contract/test_data.py` to validate that `errors/missing_atomic_data.csv` is generated with correct schema when atomic data is missing (addresses review concern on error handling verification)
- [X] T052 [US3] [Final] Generate `reports/sensitivity_sweep.csv` with columns `threshold_eV`, `classification_rate`, `stability_metric` (SD from T033) for every step from 0.45 to 0.55 eV.
 **Logic**:
 1. Read `reports/sensitivity_sweep.csv` (from T032) and `reports/stability_metrics.json` (from T033).
 2. Combine into a single CSV with the required columns.
 3. Verify the file exists and is non-empty.
 **Dependency**: Must run after T033.
 **Rationale**: Ensures the sensitivity analysis is fully transparent and externally verifiable, addressing the "robustness to arbitrary cutoff" requirement in US3.

---

## Phase 7: Revision & Gap Resolution (Review Concerns)

**Purpose**: Address specific gaps identified in prior research-stage reviews regarding data sourcing, reproducibility, and statistical rigor.

**Note**: These tasks are conditional on the successful completion of Phase 2 and Phase 3. They are NOT parallel-safe with respect to the main pipeline flow and must run after the core pipeline completes.

- [X] T044 [US1] [CANCELLED] Retry logic for acquisition. **Reason**: Integrated into T008.
- [X] T045 [US1] [REMOVED] Data summary generation. **Reason**: Superseded by T051 (Data Provenance).
- [X] T047 [US3] [Mandatory] Implement a "power analysis" helper in `code/validation/stats.py` that calculates the statistical power of the Linear Regression coefficient given the sample size and effect size.
 **Output**: Append a `power_analysis` object to `reports/validation_report.json` with keys: `{'power': <float>, 'effect_size': <float>}`.
 **Note**: This supports SC-002 statistical rigor and is now a mandatory part of the MVP validation flow.
- [X] T048 [US3] [REMOVED] Sensitivity CSV generation. **Reason**: Superseded by T032 and T052.
- [X] T049 [General] [Conditional] Update `code/config.py` to enforce a global random seed at the very start of execution (setting `numpy`, `random` seeds) and log this seed to `logs/execution_log.txt` in the format `SEED: <value>` to ensure full reproducibility (Constitution Principle I).
 **CRITICAL**: Do NOT import torch or set torch seeds as the project is CPU-only.
- [X] T050 [US1] [Conditional] Add a unit test in `tests/unit/test_acquisition.py` that mocks the HTTP request to verify the "Data Insufficiency" error path is triggered correctly when the mock returns < 50 rows.
- [X] T051 [US1] [Final] Refactor `code/data/curation.py` to explicitly write a `data/curated/data_provenance.json` file.
 **Logic**:
 1. Read `data/raw/source_metadata.json` (from T008) to extract the exact URL or source identifier.
 2. Record the `constants.py` version hash used for descriptor calculation.
 3. Record the total number of rows in `data/raw/fetched_diffusion.csv` before filtering.
 4. Record the exact number of rows in `data/curated/filtered.csv` after filtering.
 5. Include a `filter_criteria` object detailing `crystal_structure` and `diffusion_mode` values used.
 **Dependency**: Must run after T014 and T008.
 **Rationale**: Addresses the need for explicit data lineage and reproducibility beyond just a summary text file.

---

## Phase 8: Final Verification & Gap Closure (Post-Analysis Resolution)

**Purpose**: Address remaining gaps identified by the final analysis pass, specifically ensuring data provenance is explicit in the curation output and that sensitivity analysis results are externally verifiable.

- [X] T053 [General] [REMOVED] Implement `code/utils/data_streaming.py` to add a streaming fallback for datasets exceeding 10MB. **Reason**: Replaced by strict halt logic in T008. (Note: This task is now superseded by T058 in Phase 9).
- [X] T054 [US2] [REMOVED] Add explicit `try/except` block in `code/models/training.py` to catch `MemoryError` during `GridSearchCV`. **Reason**: Replaced by strict halt logic in T021/T022.
- [X] T055 [US3] [REMOVED] Implement `code/validation/sensitivity.py` to handle the case where `baseline_shift` distribution is too sparse for meaningful SD calculation. **Reason**: Replaced by strict halt logic in T033.
- [X] T056 [US1] [REMOVED] Implement `code/utils/data_streaming.py` to handle chunked processing of large CSV files. **Reason**: Replaced by strict halt logic in T008. Spec assumes <10MB. (Note: This task is now superseded by T058 in Phase 9).
- [X] T057 [US1] [REMOVED] Update `code/data/acquisition.py` to include a `streaming=True` flag. **Reason**: Replaced by strict halt logic in T008. Spec assumes <10MB. (Note: This task is now superseded by T059 in Phase 9).

---

## Phase 9: Data Streaming & Large Dataset Fallback (New)

**Purpose**: Implement robust streaming logic for real datasets that exceed the ~7GB RAM limit, ensuring no synthetic data is used while maintaining feasibility on free-tier runners.

- [X] T058 [US1] [Active] Implement `code/utils/data_streaming.py` to handle chunked processing of large CSV files.
 **Logic**:
 1. Use `pandas.read_csv` with `chunksize` parameter to process files in chunks.
 2. Accumulate statistics or filter data chunk-by-chunk to prevent memory overflow.
 3. Ensure the logic handles datasets that are valid (>50 rows) but approach or exceed the 10MB limit.
 **Dependency**: Must run before T008 if dataset size is unknown, or as a fallback mechanism.
- [X] T059 [US1] [Active] Update `code/data/acquisition.py` to include a `streaming=True` flag.
 **Logic**:
 1. If `streaming=True`, use the chunked processing logic from T058 to fetch and process data.
 2. This allows handling of datasets that are slightly larger than the 10MB limit without crashing.
 **Dependency**: Must run after T058.

---

## Phase 10: Execution Safety & Resource Guardrails (Revision Concerns)

**Purpose**: Address execution-stage feedback regarding resource limits, strict data validation, and prevention of silent failures that could lead to fabrication or runtime crashes.

- [ ] T060 [US1] [Revision] Add explicit pre-flight check in `code/data/acquisition.py` to verify the target URL is reachable and returns a valid CSV before attempting to parse.
 **Logic**:
 1. Use `requests.head()` or `requests.get()` with `stream=True` to check HTTP status code.
 2. If status != 200, raise `SystemExit` with "Data Fetch Failed: URL unreachable or invalid response".
 3. Do NOT proceed to parsing if the check fails.
 **Dependency**: Must run before T008.
 **Rationale**: Ensures the "Data Insufficiency" error is only raised for valid sources that return insufficient data, not for network failures or broken links.
- [ ] T061 [US2] [Revision] Add a `timeout` parameter to all `GridSearchCV` calls in `code/models/training.py` to prevent indefinite hangs on large grids.
 **Logic**:
 1. Wrap `GridSearchCV` in a `signal.timeout` (Unix) or `multiprocessing` wrapper with a 30-minute limit per model.
 2. If timeout occurs, raise `SystemExit` with "Training Timeout: GridSearch exceeded 30min limit".
 **Dependency**: Must run after T021 and T022.
 **Rationale**: Prevents the pipeline from hanging indefinitely on GitHub Actions, ensuring a clean failure mode rather than a timeout kill.
- [ ] T062 [US3] [Revision] Add a `min_samples` check in `code/validation/stats.py` before running bootstrap CI.
 **Logic**:
 1. If `len(X) < 10`, raise `SystemExit` with "Statistical Error: Insufficient samples for bootstrap CI (N < 10)".
 2. Do NOT proceed with CI calculation.
 **Dependency**: Must run after T023.
 **Rationale**: Ensures statistical validity of the bootstrap CI; prevents meaningless results from tiny datasets.
- [ ] T063 [General] [Revision] Implement `code/utils/resource_monitor.py` to log RAM usage at key pipeline stages (Ingestion, Training, Validation).
 **Logic**:
 1. Use `psutil` to log `process.memory_info().rss` at the start and end of each major task.
 2. If RAM usage > 6GB, log a warning: "RAM Warning: Usage exceeded 6GB threshold".
 3. Save logs to `reports/resource_usage.json`.
 **Dependency**: Must run throughout the pipeline (T008 to T035).
 **Rationale**: Provides visibility into resource consumption to ensure compliance with the 7GB RAM limit on free-tier runners.