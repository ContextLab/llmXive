# Tasks: Predicting Yield Strength of BCC Alloys

**Input**: Design documents from `/specs/001-bcc-yield-strength/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with scikit-learn, pandas, numpy, periodictable, skbio, scipy, requests dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup `data/raw`, `data/processed`, `data/logs` directories with `.gitkeep` and checksum scripts
- [ ] T005 [P] Implement `code/config.py` with fixed random seeds, path constants, and CI resource limits
- [ ] T006 [P] Setup `code/utils.py` for logging, checksumming (SHA-256), and error handling infrastructure
- [ ] T007a [P] Define `AlloyRecord` and `CompositionalDescriptor` data classes in `code/models.py`; define `ilr_transformed_features` as a list of floats without placeholder logic
- [ ] T007b [P] Implement `code/models.py` initialization logic to ensure `ilr_transformed_features` is an empty list by default, to be populated by T027c
- [ ] T008 Configure `requirements.txt` with pinned versions for reproducibility
- [ ] T009 Setup environment configuration management for local vs. CI paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and BCC Filtering (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean, filtered dataset containing only BCC alloys with valid yield strength and complete compositions.

**Independent Test**: The system can be tested by executing the data ingestion pipeline and verifying that the output CSV contains zero entries with missing yield strength, zero entries with non-BCC crystal structures, and that all composition rows sum to 1.0 (atomic fraction).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for BCC filtering logic in `tests/unit/test_data_ingestion.py`
- [ ] T011 [P] [US1] Unit test for composition normalization (sum=1.0) in `tests/unit/test_data_ingestion.py`
- [ ] T012 [P] [US1] Unit test for handling non-numeric yield strength values in `tests/unit/test_data_ingestion.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data_ingestion.py` to download MPEA database from DOI: 10.1038/s41597-020-00768-9 and save to `data/raw/mpea_raw.csv`
- [ ] T014 [US1] Implement filtering logic in `code/data_ingestion.py` to exclude non-BCC phases and null yield strength
- [ ] T015 [US1] Implement composition normalization in `code/data_ingestion.py` to ensure rows sum to 1.0 with logging
- [ ] T016 [US1] Implement logic to average duplicate compositions or select median, logging the method used
- [ ] T017 [US1] Implement data scarcity check: Halt with exit code 1 and "DATA_SCARCITY: Insufficient BCC alloys (N < 80)" if N < 80
- [ ] T018 [US1] Save filtered dataset to `data/processed/bcc_filtered.csv` and rejected entries to `data/logs/rejected_entries.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compositional Feature Engineering (Priority: P2)

**Goal**: Generate derived compositional descriptors and ILR-transformed features for regression modeling.

**Independent Test**: The system can be tested by running the feature engineering module on a fixed reference alloy ({{claim:c_03b67f39}}) and verifying that the calculated descriptors match manually calculated reference values within a relative tolerance of ≤ 1e-6.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for atomic radius mismatch (δ) calculation in `tests/unit/test_feature_engineering.py`
- [ ] T020 [P] [US2] Unit test for VEC and mixing entropy/enthalpy calculations in `tests/unit/test_feature_engineering.py`
- [ ] T021 [P] [US2] Unit test for ILR transformation logic in `tests/unit/test_feature_engineering.py`
- [ ] T022 [P] [US2] Unit test for handling missing element references (error logging) in `tests/unit/test_feature_engineering.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/feature_engineering.py` to load periodic table data (atomic radius, electronegativity, valence)
- [ ] T025a [US2] Download and verify binary interaction parameters (Ω_ij) from the NIST-JANAF thermodynamic database (or specified CALPHAD source) and save to `data/raw/thermo_params_nist_janaf.json`; verify checksum
- [ ] T024 [US2] Implement calculation of scalar descriptors: δ, VEC, mixing entropy, mixing enthalpy (using sourced Ω_ij from T025a), electronegativity difference
- [ ] T026 [US2] Implement Isometric Log-Ratio (ILR) transformation on compositional features using `skbio`
- [ ] T027a [US2] Implement concatenation of ILR-transformed features and scalar descriptors into a single feature matrix
- [ ] T027c [US2] Populate `ilr_transformed_features` in the `CompositionalDescriptor` data class with the output from T026
- [ ] T029 [US2] Implement Pre-Filter Dimensionality Reduction (PCA) on the concatenated feature matrix to mitigate overfitting for N < 100; retain components explaining the majority of variance
- [ ] T030 [US2] Implement Residualization of scalar descriptors against ILR coordinates to ensure geometric independence and mitigate multicollinearity
- [ ] T031 [US2] Apply L1 regularization if N < 100, else Recursive Feature Elimination (RFE) on the PCA/Residualized feature matrix to select the most predictive subset
- [ ] T028 [US2] Implement pre-analysis independence check to detect circular validation between thermodynamic parameters and yield strength
- [ ] T032 [US2] Save engineered dataset to `data/processed/features_engineered.csv` with full traceability log

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling and Validation (Priority: P3)

**Goal**: Train models, evaluate performance, and generate confidence intervals using nested cross-validation.

**Independent Test**: The system can be tested by running the training script with a fixed random seed and verifying that the reported R², MAE, and RMSE values match expected values within a predefined tolerance threshold, and that the bootstrapped confidence intervals are generated using the specified method.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for stratified split logic in `tests/unit/test_modeling.py`
- [ ] T034 [P] [US3] Unit test for nested cross-validation implementation in `tests/unit/test_modeling.py`
- [ ] T035 [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/modeling.py` to perform a stratified train-test split based on 4 quantile bins of yield strength; save `train_split` and `test_split` artifacts
- [ ] T034 [US3] Implement Random Forest, Gradient Boosting, and Ridge Regression training with k-fold cross-validation within the training set
- [ ] T035 [US3] Implement nested cross-validation strategy (Repeated Stratified K-Fold) applied ONLY to the `train_split` from T033 to avoid data leakage
- [ ] T036a [US3] Run nested cross-validation to generate a distribution of R² scores
- [ ] T036b [US3] Perform bootstrap resamples on the DISTRIBUTION of scores generated by T036a (nested CV) to generate multiple bootstrap iterations
- [ ] T037 [US3] Calculate confidence intervals for R² using the percentile method on the bootstrapped distribution from T036b
- [ ] T038a [US3] Implement permutation importance testing to rank the most predictive features for each bootstrap iteration
- [ ] T041 [US3] Extract feature importance ranks from the bootstrap resamples generated in T038a, calculate the standard deviation of these ranks across resamples, and verify SC-003 (std dev < 2.0); run `code/validate_success.py` against `reports/model_comparison_report.json` to verify MAE ≤ 50 MPa AND R² > null baseline
- [ ] T038b [US3] Generate final report comparing R², MAE, RMSE for all models and identifying the best performer; save to `reports/model_comparison_report.json`
- [ ] T039 [US3] Implement `code/traceability.py` to extract metrics from logs and update `state/projects/PROJ-525-predicting-the-yield-strength-of-bcc-all.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T041 Code cleanup and refactoring for readability
- [ ] T042 Performance optimization to ensure full pipeline runs < 6 hours on CI
- [ ] T043 [P] Additional unit tests for edge cases (log domain errors, missing elements)
- [ ] T044 Run quickstart.md validation to ensure end-to-end reproducibility

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 feature output

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
Task: "Unit test for BCC filtering logic in tests/unit/test_data_ingestion.py"
Task: "Unit test for composition normalization (sum=1.0) in tests/unit/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download MPEA database"
Task: "Implement filtering logic in code/data_ingestion.py"
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