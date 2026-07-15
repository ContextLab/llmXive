# Tasks: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Input**: Design documents from `/specs/001-predicting-species-distribution-shifts/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-181-predicting-species-distribution-shifts-u/` and subdirectories `code/`, `data/`, `tests/`, `metrics/`, `reports/`, `logs/`, `state/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `tests/unit/`, `tests/integration/`, `contracts/`

- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`: `scikit-learn==1.5.0 `, `geopandas==0.14.2 `, `rasterio==1.3.9 `, `pandas==2.2.2 `, `numpy==1.26.4 `, `requests==2.32.3 `, `matplotlib==3.9.0 `, `seaborn==0.13.2 `)
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with paths, thresholds, random seeds, and `n_jobs=2` configuration
- [ ] T005 [P] Initialize logging infrastructure (configure logger to write to `logs/`); do NOT produce `logs/preprocess_counts.yaml` yet
- [X] T006 [P] Create utility module `code/utils/spatial_blocks.py` for spatial block cross-validation generation
- [X] T007 Create `code/utils/data_utils.py` for coordinate validation, missing value imputation (nearest neighbor), and error handling
- [ ] T009 Create `contracts/` directory with JSON Schema files (`model_metrics.schema.yaml`, `occurrence.schema.yaml`) for validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download historical occurrence records (1970-2000) and climate rasters, then preprocess (filter, thin, extract) to produce clean CSVs.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains unique coordinates where no two points are within the minimum distance defined in FR-002, and that climate variables are successfully extracted for every record.

### Implementation for User Story 1

- [~] T010 [P] [US1] Implement `code/download.py` to fetch North American bird occurrence data (1970-2000) via GBIF API (URL: `) using `maxResults` pagination and `year` filters to handle large ranges efficiently, saving to `data/raw/occurrence_1970_2000.csv`
- [ ] T010b [P] [US1] Extend T010 logic to write `source_identifier`, `download_timestamp`, and `original_dataset_name` metadata columns to `data/raw/occurrence_1970_2000.csv` (Constitution Principle VI)
- [~] T011 [P] [US1] Implement `code/download.py` to fetch recent occurrence data (2005-2020) for evaluation, saving to `data/raw/occurrence_2005_2020.csv` (distinct file from T010)
- [ ] T011b [P] [US1] Extend T011 logic to write `source_identifier`, `download_timestamp`, and `original_dataset_name` metadata columns to `data/raw/occurrence_2005_2020.csv` (Constitution Principle VI)
- [~] T010c [US1] Implement `code/download.py` to derive "target-group effort data" as all-observer density from the historical GBIF dataset (T010) to serve as a bias proxy, saving to `data/raw/effort_data.csv` (Note: This is an internal derivation, not an external download)
- [ ] T012 [US1] Implement `code/bias_correction.py` to generate `bias_layer.tif` from `data/raw/effort_data.csv` using Kernel Density Estimation (KDE) with 10km bandwidth, saving to `data/processed/bias_layer.tif`
- [~] T013 [US1] Implement `code/preprocess.py` to filter records by breeding season, remove duplicates, spatially thin points to a minimum distance threshold (FR-002), and write `logs/preprocess_counts.yaml` with species, before_count, after_count, timestamp (Constitution Principle VI)
- [ ] T016b [US1] Implement validation in `code/preprocess.py` to flag species with <10 records *after historical thinning* as 'INSUFFICIENT_TRAINING_DATA' to prevent model failure (distinct from FR-006's test-period threshold)
- [ ] T014 [US1] Implement `code/preprocess.py` to extract climate variables from rasters at occurrence coordinates, handling missing data via nearest neighbor imputation (processes only valid species flagged by T016b)
- [ ] T017 [US1] Create `data/processed/occurrence_clean.csv` and verify all records have non-null climate variables; log summary to `logs/validation_summary.txt` and exit with code 1 if any nulls remain

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train three SDM algorithms (Random Forest, Bioclim, Regularized Logistic Regression PB) using spatial block cross-validation on CPU.

**Independent Test**: Can be fully tested by training models on a single species subset and verifying that training completes successfully and outputs performance metrics (AUC, TSS) without CUDA errors.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/baseline.py` to create a null prevalence model for baseline expectation (SC-001), outputting `metrics/baseline_performance.csv`
- [ ] T019 [US2] Implement `code/bias_null.py` to create a bias-only null model using the bias layer from T012, outputting `metrics/bias_null_metrics.csv` <!-- FAILED: unspecified -->
- [X] T020 [US2] Implement `code/power_analysis.py` to calculate minimum sample size for statistical power (post-thinning) using default parameters (power=0.8, {{claim:c_3e18cc50}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value), effect_size=0.5), outputting `metrics/power_analysis_report.json`
- [X] T021 [US2] Implement `code/train.py` to train Random Forest (`sklearn.ensemble.RandomForestClassifier`) with `n_jobs=2` on CPU
- [ ] T022 [US2] Implement `code/train.py` to train Bioclim algorithm (custom percentile envelope)
- [ ] T023 [US2] Implement `code/train.py` to train Regularized Logistic Regression (Presence-Background) using `sklearn.linear_model.LogisticRegression` with L2 regularization (FR-003)
- [ ] T024 [US2] Implement spatial block cross-validation logic in `code/train.py` using `code/utils/spatial_blocks.py` (FR-007)
- [ ] T025 [US2] Save trained model artifacts to `data/artifacts/model_{species}_{algo}.pkl`
- [ ] T026 [US2] Calculate and save AUC/TSS metrics to `metrics/training_metrics.csv`
- [ ] T027 [US2] Verify no GPU/CUDA dependencies are invoked during training (FR-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Future Projection and Evaluation (Priority: P3)

**Goal**: Project models onto CMIP6 SSP2-4.5 (2050) climate scenarios and evaluate against recent records (2005-2020) using statistical tests.

**Independent Test**: Can be fully tested by loading pre-trained models and running projections against the recent test set, producing a summary table of AUC/TSS improvements and niche stability metrics.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/project.py` to load trained models and project onto future climate rasters (`data/raw/cmip6_future.tif`), saving `data/artifacts/projection_{species}_{algo}_2050.tif`
- [ ] T029b [US3] Implement `code/preprocess.py` (or extend existing) to filter, deduplicate, and thin the 2005-2020 raw data (from T011) into `data/processed/occurrence_recent_clean.csv` for evaluation
- [ ] T029 [US3] Implement `code/evaluate.py` to evaluate projections against recent occurrence records from `data/processed/occurrence_recent_clean.csv` (produced by T029b)
- [ ] T030 [US3] Implement `code/evaluate.py` to compute AUC and TSS for historical-to-future generalization (FR-009)
- [ ] T031 [US3] Implement `code/evaluate.py` to perform niche stability checks (temporal validation vs. future projection degradation)
- [ ] T032 [US3] Implement `code/evaluate.py` to run non-parametric permutation tests or bootstrapped CI for model comparison (FR-010)
- [ ] T033b [US3] Implement validation in `code/evaluate.py` to flag species with <100 records in the 2005-2020 test period (from T029b) as 'INSUFFICIENT_DATA' and exclude from aggregation (FR-006)
- [ ] T034 [P] [US3] Implement `code/sensitivity.py` to sweep suitability thresholds (0.01, 0.05, 0.1) and apply Bonferroni correction for the family of tests (all pairwise model comparisons across all valid species), outputting `metrics/sensitivity_report.csv` with corrected p-values (FR-005, SC-003)
- [ ] T035 [US3] Save final results to `metrics/final_results.csv` and `metrics/sensitivity_report.csv`
- [ ] T036 [US3] Generate `reports/associational_disclaimer.txt` explicitly stating findings are associational (FR-008)
- [ ] T037 [US3] Verify total compute time stays within 6-hour limit (SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T038a [P] Write unit tests in `tests/unit/test_download.py` for download module
- [ ] T038b [P] Write unit tests in `tests/unit/test_preprocess.py` for preprocess module
- [ ] T038c [P] Write unit tests in `tests/unit/test_train.py` for train module
- [ ] T038d [P] Write unit tests in `tests/unit/test_project.py` for project module
- [ ] T038e [P] Write unit tests in `tests/unit/test_evaluate.py` for evaluate module
- [ ] T039 [P] Write integration tests in `tests/integration/` for end-to-end pipeline on a single species subset
- [ ] T040 Run Reference-Validator Agent as pre-commit hook to verify dataset URLs match citation titles
- [ ] T041 Update `README.md` with execution instructions and data provenance
- [ ] T042 Run `quickstart.md` validation to ensure all artifacts are generated correctly
- [ ] T043 Final review of `logs/preprocess_counts.yaml` and `metrics/` files for consistency

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output and US1 recent data processing

### Within Each User Story

- Models before services
- Services before endpoints (where applicable)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for User Story 1:
Task: "Implement code/download.py to fetch North American bird occurrence data (1970-2000) and metadata"
Task: "Implement code/download.py to fetch recent occurrence data (2005-2020) and metadata"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Training)
 - Developer C: User Story 3 (Projection/Eval)
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
- **Critical**: All models must run on CPU-only libraries (scikit-learn) without CUDA/GPU dependencies.
- **Critical**: All data must be real (GBIF, WorldClim, CMIP6); no synthetic data fabrication.
- **Critical**: Constitution Principle VI requires `source_identifier`, `download_timestamp`, `original_dataset_name` in all raw CSVs.
- **Critical**: Bias correction uses internal GBIF density proxy (T010c) and KDE (T012) as defined in plan.md.
- **Critical**: T016b enforces a minimal training threshold (10) for stability, distinct from FR-006's test-period threshold (100).