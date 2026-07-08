# Tasks: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Input**: Design documents from `/specs/001-quantify-spatial-correlations/`
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

## Phase 0: Test Definition (OPTIONAL - Only if explicitly requested in spec)

**Purpose**: Define and implement tests BEFORE code implementation.
**Instruction**: If tests are NOT requested in the spec, SKIP this phase entirely. If requested, complete ALL tasks in this phase BEFORE starting Phase 1.
**Note**: The following tasks assume tests were explicitly requested. If not, remove this phase.

- [X] T009 [US1] Contract test for data ingestion success rate in `tests/unit/test_data_ingestion.py` (Assert `success_rate` >= `config.ingestion_success_threshold`)
- [X] T010 [US1] Integration test for missing metric exclusion in `tests/integration/test_missing_metrics.py` (Assert samples with missing metrics are excluded and logged)
- [X] T017 [US2] Unit test for autocorrelation decay fit accuracy against synthetic Gaussian noise in `tests/unit/test_spatial_metrics.py` (Assert deviation <= 5%)
- [X] T018 [US2] Unit test for Fourier low-frequency integration in `tests/unit/test_fourier_metrics.py` (Assert spectral power matches synthetic ground truth)
- [X] T025 [US3] Unit test for Benjamini-Hochberg correction logic in `tests/unit/test_correlation.py` (Assert adjusted p-values match reference implementation)
- [X] T026 [US3] Integration test for leave-one-out cross-validation stability in `tests/integration/test_robustness.py` (Assert Δr calculation is correct)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: directories `code/`, `data/raw/`, `data/processed/`, `tests/`, `state/`, `docs/`
- [ ] T002 Create `requirements.txt` containing pinned versions: numpy, scipy, scikit-learn, pandas, hyperSpy, pyyaml, matplotlib, statsmodels, pygam, pytest
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/update_state.py` to read `data/` checksums and update `state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml` with `artifact_hashes` map
- [ ] T005 [P] Setup directory structure: `data/raw/`, `data/processed/`, `code/data/`, `code/preprocess/`, `code/analysis/`, `code/modeling/`, `code/validation/`, `code/report/`, `tests/`
- [X] T006 [P] Create base configuration loader for environment variables, random seeds, and thresholds (e.g., `min_sample_count`, `ingestion_success_threshold`) in `code/utils/config.py`
- [ ] T007 Implement `code/main_pipeline.py` entry point: accepts `--config` path, logs to `logs/pipeline.log`, orchestrates download -> preprocess -> analyze -> report steps
- [~] T008 Create data model definitions (ElementalMap, DevicePerformance, SpatialMetric, AnalysisResult) in `code/data/models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, parse, and align EDS elemental maps and performance metrics from verified sources into a unified dataset.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script against a known subset of the public database and verifying that the output CSV contains exactly N rows with non-null values for all required columns.

### Implementation for User Story 1

- [~] T010 [US1] **Data Feasibility Check**: Verify programmatic access to EDS maps. Search NREL Perovskite Database and Zenodo for a verified URL/DOI. If no verified source is found, halt execution and generate "Data Availability Report". Output: `state/data_feasibility_status.yaml` (success/fail + URL). <!-- FAILED: unspecified -->
- [~] T011 [US1] **Conditional Download**: If T010 succeeded, fetch EDS maps from the verified URL determined by T010 (not placeholder URLs) and Zenodo, saving raw files to `data/raw/`. If T010 failed, skip this task. (FR-001) <!-- FAILED: unspecified -->
- [~] T012 [US1] Implement `code/data/align.py` to resample maps to a common pixel grid and handle dimension mismatches (US-1 Edge Case)
- [~] T013 [US1] Implement `code/preprocess/calibrate.py` to mask defective regions (dead pixels, artifacts) and log masked area percentage (US-1 Scenario 2)
- [~] T014c [US1] Implement `code/data/ingest.py` to orchestrate download, alignment, and masking, outputting a unified CSV to `data/processed/unified_dataset.csv` with columns: sample_id, Pb_map_path, I_map_path, MA_map_path, PCE, J_sc, V_oc. **Note**: This task produces the "pre-filter" valid dataset used for sensitivity analysis.
- [~] T015 [US1] Add validation logic to exclude samples with missing performance metrics and log warnings with specific sample IDs (US-1 Scenario 3)
- [~] T016 [US1] Implement co-location validation check in `code/validation/co_location.py` to verify EDS map and PCE originate from the same device by matching `device_id` metadata fields, setting a `validation_flag` for each sample (FR-007)
- [~] T023 [US1] Implement depth resolution validation in `code/validation/depth_check.py` to flag samples where bulk EDS may not correlate with surface PCE, setting a `depth_flag` (FR-008)
- [~] T010b [US1] **Calculate Ingestion Rate**: Compute `ingestion_success_rate` (N_processed / N_requested) from T010/T011 results and write to `state/ingestion_stats.json` for reporting.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Spatial Correlation Metric Extraction (Priority: P2)

**Goal**: Compute 2-D autocorrelation functions and Fourier transforms to extract correlation lengths and spectral power metrics.

**Independent Test**: The extraction module can be tested independently by running it on synthetic test images with known correlation lengths and verifying that calculated metrics match ground truth within ±5%.

### Implementation for User Story 2

- [~] T019 [US2] Implement `code/analysis/spatial_metrics.py` to compute 2-D autocorrelation functions for Pb, I, and MA maps, writing results to `data/processed/spatial_metrics.csv` with columns: sample_id, element, correlation_length, model_type, AIC (FR-002)
- [~] T020 [US2] Implement decay model fitting (exponential, Gaussian, power-law) in `code/analysis/spatial_metrics.py` with AIC-based best-fit selection (FR-002)
- [~] T021 [US2] Implement logic to flag "undefined" correlation lengths when decay does not occur within image bounds and record lower bounds (US-2 Scenario 3)
- [~] T022 [US2] Implement `code/analysis/spatial_metrics.py` to compute 2-D Fourier transforms and integrated low-frequency spectral power (low-frequency range) (FR-003)
- [~] T024 [US2] Aggregate all spatial metrics into a structured DataFrame in `data/processed/spatial_metrics.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

**Goal**: Fit linear regression models, calculate correlations, apply corrections, and perform robustness checks to test the hypothesis.

**Independent Test**: The modeling module can be tested by running it on a synthetic dataset with a known negative correlation and verifying that the model detects a statistically significant relationship after correction.

### Implementation for User Story 3

- [~] T034 [US3] **Unified Sample Filtering**: Implement `code/modeling/filter.py` to consume `validation_flag` (T016) and `depth_flag` (T023), filtering out mismatched samples from the dataset produced by T014c. This task produces the **primary_analysis_dataset** used for all subsequent correlation calculations (T027, T028, T029, AND T031c). (FR-007, FR-008)
- [~] T031c [US3] **Sensitivity Analysis (Counter-Factual)**: Implement `code/modeling/sensitivity.py` to calculate the impact of excluding depth-confounded samples. **Input**: The "pre-filter" valid dataset from T014c and the **primary_analysis_dataset** from T034. **Execution Order**: This task runs AFTER T034 completes, but CAN run in parallel with T027, T028, and T029 as it consumes T034's output. **Action**: Compute correlation coefficients on both datasets, calculate the delta (Δr), and define the quantitative threshold for "high sensitivity" (default: [deferred] change in correlation coefficient, configurable via `config.yaml`). Report whether the exclusion of flagged samples significantly alters the conclusion. (FR-008)
- [~] T027 [US3] Implement `code/modeling/correlation.py` to calculate Pearson and Spearman correlation coefficients and p-values between spatial metrics and PCE using the **primary_analysis_dataset from T034** (FR-004)
- [~] T028 [US3] Implement Benjamini-Hochberg correction for multiple comparisons in `code/modeling/correlation.py` and report raw/adjusted p-values (FR-004)
- [~] T029 [US3] Implement `code/modeling/gam.py` to fit Generalized Additive Models (GAM) for detecting non-linear relationships (FR-004)
- [~] T030 [US3] Implement `code/analysis/robustness.py` to perform leave-one-out cross-validation and report Δr changes for each sample (FR-005, SC-003)
- [~] T032 [US3] Implement `code/report/generate.py` to generate summary report (CSV at `data/report/summary.csv` and PDF at `data/report/summary.pdf`) with fields: correlation coefficient, p-value, sample count, best-fit model, AIC, Δr max, **ingestion_success_rate** (read from `state/ingestion_stats.json`), and **sensitivity_delta_r** (from T031c) (FR-006)
- [~] T033 [US3] Add logic to calculate statistical power; if N < `config.min_sample_count` (default a moderate number), flag results as 'non-definitive' and halt interpretation (Assumptions)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034a [P] Update `README.md` with usage instructions and example commands
- [~] T035 Add docstrings to all public functions in `code/` (Complete coverage of public API)
- [ ] T036 Optimize memory usage: ensure peak RAM < 7GB during full pipeline run on CPU-only CI
- [ ] T037 [P] Add additional unit tests to achieve >80% code coverage in `tests/unit/`
- [ ] T038 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data ingestion (US1) for input data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on spatial metrics (US2) for input data

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
Task: "Contract test for data ingestion success rate in tests/unit/test_data_ingestion.py"
Task: "Integration test for missing metric exclusion in tests/integration/test_missing_metrics.py"

# Launch all models for User Story 1 together:
Task: "Create base configuration loader in code/utils/config.py"
Task: "Create data model definitions in code/data/models.py"
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
- **Critical**: All data processing must run on CPU-only CI (A minimal computing configuration with multiple cores and sufficient memory.); no GPU/CUDA dependencies allowed.
- **Critical**: All data must be real; no synthetic data generation for final analysis tasks.
- **Critical**: Task ordering MUST respect data flow (e.g., download/align MUST precede metric extraction).
- **Critical**: Dataset URLs must be explicit and reachable; "download from UCI" without a specific URL is invalid.
- **Critical**: T010 must succeed before T011 runs. T011 uses the URL from T010.
- **Critical**: T034 is the single source of truth for the primary analysis dataset. T031c performs a counter-factual comparison using T034's output and the pre-filter dataset to quantify sensitivity. T031c runs after T034 but can run in parallel with T027/T028/T029.