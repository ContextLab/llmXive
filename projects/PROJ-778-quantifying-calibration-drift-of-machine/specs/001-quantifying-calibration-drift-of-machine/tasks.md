# Tasks: Quantifying Calibration Drift of Machine Learning Classifiers Over Time

**Input**: Design documents from `/specs/001-calibration-drift/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, numpy, scipy, statsmodels, ruptures, requests, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/dataset_schema.yaml` defining expected columns for Adult/CPS datasets (Columns: 'age', 'workclass', 'education', 'occupation', 'relationship', 'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week', 'native-country', 'income'; Types: int, str, float).
- [ ] T005 Create `contracts/metric_record_schema.yaml` defining JSON structure for calibration/covariate metrics (Fields: year, model_type, ece_5, ece_10, ece_20, brier, pca_shift, key_feature_shift, rho_5, rho_10, rho_20, **rho_diff_5_10, rho_diff_10_20, max_rho_diff**, p_value_wls, change_point_year). Note: Added rho_diff fields to satisfy SC-002 robustness verification.
- [X] T006 [P] Implement `code/utils/config.py` for path and parameter configuration
- [~] T007 Create `code/utils/metrics.py` with stub functions: `pca_shift(train_features, test_features, n_components=0.95)`, `key_feature_shift(train_features, test_features, feature_names=...)`. **Implement PCA Shift and Key Feature Shift on raw feature vectors**. Implements Plan's PCA shift override of FR-004. Include formula reference for PCA projection and Key Feature Mean Shift. **Do NOT implement wasserstein_dist**.
- [~] T008 Create `code/utils/shift_detection.py` with stub function: `detect_change_point_bic(metrics, alpha=0.05)`. **Implement BIC-based detection**, not fixed block-size. Implements Plan's BIC-based detection override of FR-006 (see Plan Complexity Tracking).
- [~] T009 Setup environment configuration management (`.env` or `config.yaml` for data paths)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Fixed Model Training (Priority: P1) 🎯 MVP

**Goal**: Download yearly snapshots of versioned benchmark datasets and train fixed probabilistic classifiers on the earliest snapshot.

**Independent Test**: A script runs successfully, downloading two datasets, training two models on the earliest split, and saving the model artifacts and test data splits for subsequent years.

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/00_data_availability_gate.py`: Check for IPUMS CPS or synthetic config; halt if missing.
- [~] T013 [US1] Implement `code/01_data_acquisition.py`: Download yearly snapshots for UCI Adult (1994-2022) and Credit Card Default (2005-2021) as primary targets per FR-001. **Strictly follow FR-001**. If unavailable, do NOT proceed to synthetic data in this task; halt and log critical error.
- [ ] T013-Fallback [US1] **Conditional**: If `00_data_availability_gate.py` determines IPUMS/Synthetic is the only option, implement fallback logic in `code/01_data_acquisition.py` to download/generate IPUMS/Synthetic data. Log a critical scope warning and document the scope reduction in `data/processed/scope_log.md` citing FR-001 deviation and Plan authorization.
- [ ] T013-Fallback-Log [US1] **Conditional**: If fallback data is used, implement explicit logging in `code/01_data_acquisition.py` to record the specific dataset source used (IPUMS or Synthetic) and the resulting scope implications in the research record. Verify fallback source is real (IPUMS) or properly seeded (Synthetic), not random placeholder.
- [~] T014 [US1] Implement schema alignment logic in `code/01_data_acquisition.py`: Intersect feature columns between training and test snapshots (FR-008). Save aligned feature list to `data/processed/aligned_features.json`. Abort with error if intersection < 90% of original features.
- [~] T015 [US1] Implement `code/02_model_training.py`: Train Logistic Regression and Random Forest on the earliest snapshot only.
- [~] T016 [US1] Implement serialization logic in `code/02_model_training.py`: Save models to `data/models/` without further updates.
- [~] T017 [US1] Implement logic to split and save test data for all subsequent years to `data/processed/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for schema validation logic in `tests/unit/test_schema_validation.py`: Implement `test_schema_validation_rejects_mismatched_columns` to assert that a schema mismatch >10% triggers an abort with a clear error message.
- [ ] T011 [P] [US1] Integration test for data download and model serialization in `tests/integration/test_data_pipeline.py`: Verify that `data/models/` contains `logistic_regression.pkl` and `random_forest.pkl` and that `data/processed/` contains yearly splits for the test datasets (mocked for this test). Assert files are loadable and non-empty.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Temporal Calibration Metric Computation (Priority: P2)

**Goal**: Compute calibration metrics (ECE, Brier Score) and covariate shift measures (PCA-based shift and Key Feature Shift) for each fixed model across every subsequent yearly test split.

**Independent Test**: For a single fixed model and a single later year, the system outputs a JSON record containing ECE, Brier score, and shift values, validated against manual calculations.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/03_evaluation.py`: Load fixed models and iterate through yearly test splits. **This task must precede metric calculation tasks.**
- [ ] T020 [US2] Implement `code/utils/metrics.py`: Calculate ECE with 5, 10, and 20 bins (FR-010).
- [ ] T021 [US2] Implement `code/utils/metrics.py`: Calculate Brier Score.
- [ ] T022 [US2] Implement `code/utils/metrics.py`: Calculate covariate shift using **PCA-based shift** and **Key Feature Shift** on the common feature subset. **Do NOT implement raw Wasserstein distance** as it is statistically invalid for high-dimensional data per Plan Complexity Tracking. Implements Plan's architectural override of FR-004.
- [ ] T024 [US2] Implement `code/03_evaluation.py`: Compute and store metrics (ECE_5, ECE_10, ECE_20, Brier, PCA_Shift, Key_Feature_Shift, **rho_5, rho_10, rho_20, rho_diff_5_10, rho_diff_10_20, max_rho_diff**) for each year to `data/processed/metrics_records.json` using the schema defined in T005. Explicitly compute Spearman correlation (rho) for each binning strategy to satisfy T027's robustness check.
- [ ] T025 [US2] Implement logic to handle missing years gracefully (log warning, skip year) as per Edge Cases.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Trend Analysis and Reporting (Priority: P3)

**Goal**: Fit Weighted Least Squares models for systematic trends, perform correlation analysis, detect change-points, and generate a Markdown report.

**Independent Test**: The analysis script runs on the time-series data, outputs p-values and correlation coefficients, and generates a Markdown report with plots.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/04_statistical_analysis.py`: Load metric records and fit **Weighted Least Squares (WLS)** (Year vs. ECE) with p-value reporting. **Do NOT implement Simple Linear Regression** as per Plan Complexity Tracking (WLS required for heteroscedasticity). Note: Implements Plan's architectural override of FR-005. Save results to `data/processed/regression_results.json` (fields: slope, intercept, p_value, r_squared).
- [ ] T027 [US3] Implement `code/04_statistical_analysis.py`: Compute Spearman rank correlation between covariate shift and calibration error. **Verify robustness** by ensuring the coefficient remains consistent (within ±0.1) across ECE binning strategies of 5, 10, and 20 bins (FR-010, FR-009). Use `rho_5`, `rho_10`, `rho_20` from T024 and the `max_rho_diff` field to validate SC-002.
- [ ] T028 [US3] Implement `code/04_statistical_analysis.py`: Perform **BIC-based change-point detection** (alpha = 0.05) to identify abrupt shifts. **Do NOT implement fixed block-permutation** as per Plan Complexity Tracking (BIC required to avoid arbitrary block sizes). Note: Implements Plan's architectural override of FR-006.
- [ ] T029 [US3] Implement `code/05_report_generation.py`: Generate time-series plots (ECE/Brier vs. Year) using matplotlib/seaborn.
- [ ] T030 [US3] Implement `code/05_report_generation.py`: Generate scatter plots (Shift vs. Calibration Error).
- [ ] T031 [US3] Implement `code/05_report_generation.py`: Assemble Markdown report with Title, Methodology, Time-Series Plot, Scatter Plot, Statistical Significance Table (p-values, rho, change-points), and Conclusion. Flag trends if shift metrics are missing (Constitution Principle VI).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `specs/001-calibration-drift/quickstart.md`
- [ ] T033 Code cleanup and refactoring
- [ ] T034 [P] Additional unit tests for edge cases: implement `test_missing_year_handling` (asserts graceful skip and warning log), `test_schema_mismatch_threshold` (asserts abort on <90% overlap), and `test_empty_dataset` in `tests/unit/`.
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [ ] T036 Verify `00_data_availability_gate.py` correctly halts on missing real data sources (Constitution Principle II)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metric records

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
Task: "Unit test for schema validation logic in tests/unit/test_schema_validation.py"
Task: "Integration test for data download and model serialization in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/00_data_availability_gate.py"
Task: "Implement code/01_data_acquisition.py"
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
- **Constraint**: All tasks must run on CPU-only CI with a minimal core configuration and limited memory. No GPU, no 8-bit/4-bit quantization.
- **Data Integrity**: No synthetic data generation unless IPUMS is unavailable; `00_data_availability_gate.py` must enforce this.
- **Methodology Compliance**: All statistical methods (WLS, BIC, PCA Shift) MUST match the Plan's architectural decisions which override the Spec's initial mandates (FR-004, FR-005, FR-006) for validity and feasibility. The tasks explicitly implement the Plan's methods.
- **Schema Compliance**: T005 and T024 must include `rho_diff` fields to support SC-002 robustness verification.