# Tasks: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

**Input**: Design documents from `/specs/001-predict-weibull-modulus/`
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

- [X] T001 Create project structure per implementation plan (projects/PROJ-314-predicting-the-impact-of-composition-on-/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T012a [P] Generate contract schema `ceramic_entry.schema.yaml` in `code/contracts/` (Moved to start of Phase 2)
- [ ] T012b [P] Generate contract schema `model_result.schema.yaml` in `code/contracts/` (Moved to start of Phase 2)
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [X] T004 Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T006 [P] Create base `CeramicEntry` dataclass in `code/__init__.py`
- [X] T007 [P] Create base `DescriptorSet` dataclass in `code/__init__.py`
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py`
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T017b [US1] Implement `generate_data_availability_report()` in `code/ingestion.py`: Generate `data/reports/data_availability_report.json` with fields `total_sources`, `valid_entries`, `reason_code`, `timestamp` when N < 30 (Required for Data Gap Protocol). **Output**: File must be written before halting.
- [X] T017 [US1] Implement `validate_data_gap()` in `code/ingestion.py`:
 1. Check total valid entries (N) after fetching and applying per-entry filters (T018a).
 2. **HALT**: If N < 30, call `generate_data_availability_report()` (T017b) to create `data/reports/data_availability_report.json`, log `INFO: PROJECT_HALTED: Insufficient data (N={N})`, and exit with code 1.
 3. If N >= 30, proceed to cleaning.
- [X] T018a [US1] Implement `clean_data()` in `code/ingestion.py`:
 1. Filter for `N >= 30` by explicitly extracting sample count from fields named 'N', 'sample_size', or 'n' (FR-003).
 2. Handle range values: Extract midpoint, set `is_range_flag`, store `range_original` (to be processed by T018b).
 3. Impute missing processing params (group median -> global median).
 4. Handle non-stoichiometric phases: **Exclude** if the specific class has < 5 samples; otherwise, impute using global median.
 5. **Output Schema**: Ensure output CSV contains columns: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group` (derived grouping feature, not elemental descriptor), `sintering_temp`, `is_imputed`. (Descriptors like `mean_atomic_radius` are populated by T019).
- [X] T018b [US1] Implement `compute_range_uncertainty()` in `code/descriptors.py`:
 1. Extract midpoint from `range_original` if `is_range_flag` is true.
 2. Calculate `range_uncertainty` as (max - min) / 2.
 3. Add `range_uncertainty` column to the dataset. (Addresses Plan Phase 1, Task 1.4)
- [X] T019 [US1] Implement `compute_descriptors()` in `code/descriptors.py`:
 1. Calculate mean atomic radius and electronegativity std.
 2. Calculate Cation Size Variance.
 3. **Explicitly Calculate Valence Electron Concentration (VEC)** as: `sum(valence electrons of all atoms) / total number of atoms in formula unit` (FR-002).
- [X] T020 [US1] Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py` that raises `ValueError` with message "Missing values in primary predictors: {col_names}" if any primary predictor column (mean_atomic_radius, electronegativity_std, valence_electron_concentration) contains NaN, and add unit test `tests/test_ingestion.py::test_validate_no_missing`.
- [X] T021 [US1] Implement logging for data exclusion reasons in `code/ingestion.py`: Log format `INFO: Excluded row {row_index} due to {reason}` where `{row_index}` is the pandas index and `{reason}` is one of: 'N<30', 'missing_stoichiometry', 'non_stoichiometric_phase'. Log to `logs/ingestion.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py`
- [X] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py`
- [ ] T025 [P] [US2] Implement integration test `tests/integration/test_modeling.py::test_5fold_cv_stratified_split` to verify the 5-fold CV workflow and generate `data/results/cv_split_report.json`

### Implementation for User Story 2

- [X] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group` (derived from US1 output); switch to hold-out if 30 <= N < 50 (FR-005, SC-004). **Dependency**: Requires T018a completion.
- [X] T027 [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM with limited hyperparameter search (a constrained number of combinations) to fit h runtime (FR-004)
- [ ] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples. Calculate and save its MAE to `data/results/baseline_metrics.json` (key: `baseline_mae`). (Addresses Plan Phase 2, Task 2.3)
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline (SC-001). **Output**: Save metrics to `data/results/model_metrics.json`.
- [X] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: **REMOVED** (See constraint preservation note: Permutation test removed to align with FR-004 and SC-001; only baseline comparison required).
- [X] T030 [US2] Implement `check_leakage()` in `code/diagnostics.py`:
 1. Select the **best model** from T027/T028 (lowest validation MAE). Load from `data/models/best_model.pkl`.
 2. Re-run the model without the `primary_anion_cation_group` feature.
 3. **Logic**: Calculate performance drop = (Original MAE - New MAE) / Original MAE. Retrieve `Original MAE` from `data/results/model_metrics.json` (key: `best_model_mae`).
 4. **Mandatory Output**: If performance drop < 10% (i.e., MAE increases by less than 10%), write a "Potential Leakage" warning to `data/results/leakage_report.json` (FR-005.5).
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [X] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on trained model; verify output lists top 5 descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [X] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py`
- [X] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [X] T036 [US3] Implement `calculate_shap()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model (FR-006)
- [X] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`:
 1. Compute VIF for all predictors.
 2. **Output**: Report individual VIF scores for every feature in `data/results/vif_diagnostics.json`.
 3. Flag any pair with VIF > 5.0 (FR-007, SC-003).
- [X] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`:
 1. Cluster features with VIF > 5 for *interpretive grouping*.
 2. **Constraint**: Suppress individual causal claims for clustered features in the final report (T040). Report aggregate importance for clusters instead to prevent invalid claims (SC-003).
 3. Do NOT suppress individual VIF scores in the diagnostic report (T037), only in the interpretive summary.
- [X] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters identified in T038, ensuring these are used in the final ranking instead of individual features for correlated groups. (Addresses Plan Phase 3, Task 3.3)
- [X] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation for top features across folds (FR-009, SC-002)
- [X] T040 [US3] Implement `generate_interpretation()` in `code/report.py`:
 1. Rank features.
 2. Map top descriptors to physical mechanisms using `code/physics_mappings.py` (created in T022).
 3. Include correlation matrix between top descriptors and Weibull modulus.
 4. **Consume clustered data from T038** to suppress individual causal claims for correlated features.
- [ ] T041 [US3] Generate SHAP summary plots and feature ranking tables: Create `data/results/shap_summary.png` and `data/results/feature_ranking_table.csv` using `shap.summary_plot` and `pandas.DataFrame.to_csv`. **Also**: Export Coefficient of Variation (CV) stability scores to `data/results/stability_metrics.json` to satisfy SC-002 evidence requirements.
- [X] T042 [US3] Implement disclaimer logic: Create `sanitize_conclusion(text)` function in `code/report.py` to remove 'cause' (case-insensitive, whole word) and append "These results represent statistical associations only and do not imply causal relationships." to **all text outputs** (logs, CLI, reports) as required by FR-008, and add unit test `tests/test_report.py::test_disclaimer_removal`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [X] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers. **Include**: Calculate Confidence Intervals (CIs) for all metrics via bootstrapping (sufficient iterations) and export CI bounds in the final report JSON. (Addresses Plan Phase 4, Task 4.2)
- [ ] T044 [P] Execute `code/hash_artifacts.py` to update `state/project_state.yaml` with new content hashes for all files in `data/` and `code/`
- [ ] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline; success condition: Exit code 0 and no errors in `logs/validation.log`
- [ ] T047 [P] Update `docs/data_gap_protocol.md` with the exact report generation steps defined in T017b (N < 30 halting logic and `data_availability_report.json` schema)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the dataset for US2/US3.**
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` dataset). **Specific Dependency**: T026 requires T018a to be complete.
- **User Story 3 (P3)**: Depends on US2 (needs trained models from US2) and T022 (physics_mappings.py).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (logic)
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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for chemparse composition parsing in tests/test_descriptors.py"
Task: "Unit test for imputation logic in tests/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_data() in code/ingestion.py"
Task: "Implement compute_descriptors() in code/descriptors.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion & Descriptors)
4. **STOP and VALIDATE**: Test ingestion on sample data; verify dataset quality.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Modeling)
4. Add User Story 3 → Test independently → Deploy/Demo (Interpretability)
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling) - *Can start once US1 produces data*
 - Developer C: User Story 3 (Interpretability) - *Can start once US2 produces models*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data ingestion must use real URLs or package-based fetches. No synthetic data generation for training.
- **Note on Phase 2 Tasks**: T012a/T012b are split to ensure atomic implementation and testing. T022 is moved to Phase 2 to ensure availability.
- **Note on T018**: Unauthorized fallback options removed to align with spec. T018a now strictly handles cleaning; descriptors are calculated in T019.
- **Note on T017b**: Explicitly generates the Data Availability Report artifact. Moved to Phase 3 to ensure dependency on T017.
- **Note on T029**: Permutation test removed to align with FR-004 and SC-001.
- **Note on T030**: Leakage logic corrected to flag if drop < 10%.
- **Note on T043**: Now includes CI calculation.
- **Note on T041**: Now includes export of stability metrics (CV).
- **Note on T022**: Duplicate entry removed from Phase 3 to resolve executability concern.