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

- [ ] T001 Create project structure per implementation plan (projects/PROJ-314-predicting-the-impact-of-composition-on-/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [ ] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [ ] T006 [P] Create base `CeramicEntry` dataclass in `code/__init__.py` (Replaces coarse T006)
- [ ] T007 [P] Create base `DescriptorSet` dataclass in `code/__init__.py` (Replaces coarse T006)
- [ ] T008 [P] Setup `code/ingestion.py` skeleton file structure (Replaces coarse T007)
- [ ] T009 [P] Implement URL validation logic in `code/ingestion.py` (Replaces coarse T007)
- [ ] T010 [P] Configure logging infrastructure in `code/__init__.py`
- [ ] T011 [P] Setup environment configuration management (`.env` handling for API keys if needed)
- [ ] T012 [P] [US1] Generate contract schemas `ceramic_entry.schema.yaml` and `model_result.schema.yaml` in `code/contracts/` (Moved from Phase 3 to ensure schemas exist before ingestion logic is written)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [ ] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [ ] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement `fetch_data()` in `code/ingestion.py`: Fetch from Materials Project/NIST or load "Curated Literature Dataset" fallback (FR-001)
- [ ] T017 [US1] Implement `validate_data_gap()` in `code/ingestion.py`: 
  1. Check total valid entries (N) after fetch.
  2. **HALT**: If N < 30, halt execution immediately and generate "Data Availability Report" (Plan Phase 0 Task 0.4).
  3. If N >= 30, proceed to cleaning.
- [ ] T018 [US1] Implement `clean_data()` in `code/ingestion.py`: 
  1. Filter for `N >= 30` by explicitly extracting sample count from fields named 'N', 'sample_size', or 'n' (FR-003).
  2. Handle range values (extract midpoint, set `is_range_flag`, calculate `range_uncertainty`).
  3. Impute missing processing params (group median -> global median).
  4. Handle non-stoichiometric phases: log warning, exclude, OR impute using nearest neighbor element fallback (Edge Case).
  5. **Output Schema**: Ensure output CSV contains columns: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `range_uncertainty`, `primary_anion_cation_group`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`, `cation_size_variance`, `sintering_temp`, `is_imputed`.
- [ ] T019 [US1] Implement `compute_descriptors()` in `code/descriptors.py`: 
  1. Calculate mean atomic radius and electronegativity std.
  2. Calculate Cation Size Variance.
  3. **Explicitly Calculate Valence Electron Concentration (VEC)** as: `sum(valence electrons of all atoms) / total number of atoms in formula unit` (FR-002).
- [ ] T020 [US1] Add validation to ensure no missing values in primary predictors after imputation
- [ ] T021 [US1] Add logging for data exclusion reasons (e.g., "N < 30", "Invalid Stoichiometry", "Non-stoichiometric fallback used")
- [ ] T022 [P] [US3] Create `code/physics_mappings.py` with a dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support T040 (FR-006/US-3) (Resolves missing producer)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py`
- [ ] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py`
- [ ] T025 [P] [US2] Integration test for 5-fold CV workflow in `tests/integration/test_modeling.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group` (derived from US1 output); switch to hold-out if 30 <= N < 50 (FR-005, SC-004)
- [ ] T027 [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM with limited hyperparameter search (a constrained number of combinations) to fit 6h runtime (FR-004)
- [ ] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline (SC-001). **Output**: Save metrics to `data/results/model_metrics.json`.
- [ ] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: 
  1. Perform permutation test with **1000 permutations** and **random_seed=42**.
  2. **Success Criteria**: The model is significant ONLY if p-value < 0.05 (SC-001).
  3. **Output**: Generate `data/results/permutation_p_value.json` containing the p-value.
  4. **Constraint**: If p >= 0.05, flag as "Not Statistically Significant".
- [ ] T030 [US2] Implement `check_leakage()` in `code/diagnostics.py`: 
  1. Select the best model from T027/T028 (lowest validation MAE).
  2. Re-run the model without the `primary_anion_cation_group` feature.
  3. **Logic**: Calculate performance drop = (Original MAE - New MAE) / Original MAE.
 4. **Mandatory Output**: If drop < 0.10, write a "Potential Leakage" warning to `data/results/leakage_report.json` (FR-005.5).
- [ ] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [ ] T032 [US2] Add logic to exclude classes with < 5 samples from stratification if necessary (Rare Class Handling)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on trained model; verify output lists top 5 descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [ ] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py`
- [ ] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `calculate_shap()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model (FR-006)
- [ ] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`: 
  1. Compute VIF for all predictors.
  2. **Output**: Report individual VIF scores for every feature in `data/results/vif_diagnostics.json`.
  3. Flag any pair with VIF > 5.0 (FR-007, SC-003).
- [ ] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`: 
  1. Cluster features with VIF > 5 for *interpretive grouping*.
  2. **Constraint**: Suppress individual causal claims for clustered features. Report aggregate importance for clusters instead to prevent invalid claims (SC-003).
  3. Do NOT suppress individual VIF scores in the diagnostic report (T037), only in the interpretive summary.
- [ ] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation for top features across folds (FR-009, SC-002)
- [ ] T040 [US3] Implement `generate_interpretation()` in `code/report.py`: 
  1. Rank features.
  2. Map top descriptors to physical mechanisms using `code/physics_mappings.py` (created in T022).
  3. Include correlation matrix between top descriptors and Weibull modulus.
- [ ] T041 [US3] Generate SHAP summary plots and feature ranking tables in `data/results/`
- [ ] T042 [US3] Add disclaimer logic: Append "statistical associations only" and remove "cause" from conclusion (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [ ] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers
- [ ] T044 [P] Run `hash_artifacts.py` to update `state/` with content hashes for all new data/code artifacts
- [ ] T045 [P] Run `quickstart.md` validation to ensure reproducibility
- [ ] T046 [P] Code cleanup and refactoring
- [ ] T047 [P] Documentation updates in `docs/` regarding the "Data Gap Protocol"

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
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` dataset).
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
- **Note on Phase 2 Tasks**: T006 and T007 are split to ensure atomic implementation and testing.
- **Note on T022**: Created in Phase 3 to support US3, but placed early to ensure it is available before T040.