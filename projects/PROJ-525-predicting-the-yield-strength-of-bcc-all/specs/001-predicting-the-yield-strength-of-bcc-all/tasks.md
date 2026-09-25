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

- [ ] T001 Create project structure: `mkdir -p data/raw data/processed data/logs code tests reports state`
- [ ] T002 Initialize Python 3.11 project with scikit-learn, pandas, numpy, periodictable, skbio, scipy, requests, pymatgen dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on plan.md structure):

- [ ] T004 Setup `data/raw`, `data/processed`, `data/logs` directories with `.gitkeep` and checksum scripts
- [X] T007 [P] Define `AlloyRecord` and `CompositionalDescriptor` data classes in `code/models.py`; define `ilr_transformed_features` as a list of floats (schema definition only)
- [X] T008 Configure `requirements.txt` with pinned versions for reproducibility
- [X] T009 [P] Setup environment configuration management for local vs. CI paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and BCC Filtering (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean, filtered dataset containing only BCC alloys with valid yield strength and complete compositions.

**Independent Test**: The system can be tested by executing the data ingestion pipeline and verifying that the output CSV contains zero entries with missing yield strength, zero entries with non-BCC crystal structures, and that all composition rows sum to 1.0 (atomic fraction).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010_test [P] [US1] Unit test for BCC filtering logic in `tests/unit/test_data_ingestion.py`
- [X] T011_test [P] [US1] Unit test for composition normalization (sum=1.0) in `tests/unit/test_data_ingestion.py`
- [X] T012_test [P] [US1] Unit test for handling non-numeric yield strength values in `tests/unit/test_data_ingestion.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` to download MPEA database using canonical DOI resolver (e.g., `doi.org/10.1038/s41597-020-00768-9`) and save to `data/raw/mpea_raw.xlsx`; verify SHA-256 checksum
- [X] T014 [US1] Implement filtering logic in `code/data_ingestion.py` to exclude non-BCC phases and null yield strength
- [X] T015 [US1] Implement composition normalization in `code/data_ingestion.py` to ensure rows sum to 1.0 with logging
- [X] T016 [US1] [MANDATORY] Implement logic to average duplicate compositions or select median, logging the method used (US-4 requirement); MUST be executed
- [X] T017 [US1] [MANDATORY] Implement data scarcity check: Halt with exit code 1 and "DATA_SCARCITY: Insufficient BCC alloys (N < 80)" if N < 80 (FR-004 requirement); MUST be executed
- [X] T018 [US1] Save filtered dataset to `data/processed/bcc_filtered.csv` and rejected entries to `data/logs/rejected_entries.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compositional Feature Engineering (Priority: P2)

**Goal**: Generate derived compositional descriptors and ILR-transformed features for regression modeling.

**Independent Test**: The system can be tested by running the feature engineering module on a fixed reference alloy (Mo-25Nb-25Ta-25W in atomic percent) and verifying that the calculated descriptors (δ, VEC, mixing entropy, mixing enthalpy, electronegativity difference) match the manually calculated reference values within a relative tolerance of ≤ 1e-6.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019_test [P] [US2] Unit test for atomic radius mismatch (δ) calculation in `tests/unit/test_feature_engineering.py`
- [X] T020_test [P] [US2] Unit test for VEC and mixing entropy/enthalpy calculations in `tests/unit/test_feature_engineering.py`
- [X] T021_test [P] [US2] Unit test for ILR transformation logic in `tests/unit/test_feature_engineering.py`
- [X] T022_test [P] [US2] Unit test for handling missing element references (error logging) in `tests/unit/test_feature_engineering.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/feature_engineering.py` to load periodic table data (atomic radius, electronegativity, valence)
- [X] T025a [US2] Install `pymatgen` and execute `pymatgen.analysis.phase_diagram.BinaryInteractionParameters` (or equivalent accessor) to export binary interaction parameters (Ω_ij) to `data/raw/thermo_params.json`; verify SHA-256 checksum; ensure source is distinct from MPEA yield strength data (FR-003)
- [X] T023b [US2] Embed and execute automated assertion for fixed reference alloy (Mo-25Nb-25Ta-25W) verifying all calculated descriptors match manual values within tolerance ≤ 1e-6; **fail pipeline with exit code 1 if tolerance exceeded**
- [X] T024 [US2] Implement calculation of scalar descriptors: δ, VEC, mixing entropy, mixing enthalpy (using sourced Ω_ij from T025a), electronegativity difference
- [X] T026 [US2] Implement Isometric Log-Ratio (ILR) transformation on compositional features using `skbio`
- [X] T027a [US2] Implement concatenation of ILR-transformed features and scalar descriptors into a single combined feature matrix (runs AFTER T026, T024)
- [X] T027c [US2] Populate `ilr_transformed_features` in the `CompositionalDescriptor` data class with the output from T026
- [X] T028 [US2] Implement pre-analysis independence check to detect circular validation between thermodynamic parameters and yield strength (runs BEFORE T029)
- [X] T029 [US2] Apply L1 regularization or Recursive Feature Elimination (RFE) on the **COMBINED set of ILR and scalar descriptors (after T027a)** to select the most predictive subset (FR-003.2); **DO NOT implement PCA or Residualization as they are not authorized in spec.md**
- [X] T032 [US2] Save engineered dataset to `data/processed/features_engineered.csv` with full traceability log

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling and Validation (Priority: P3)

**Goal**: Train models, evaluate performance, and generate confidence intervals using 80/20 split and 5-fold CV.

**Independent Test**: The system can be tested by running the training script with a fixed random seed and verifying that the reported R², MAE, and RMSE values match expected values within a predefined tolerance threshold, and that the bootstrapped confidence intervals are generated using the specified method.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033_test [P] [US3] Unit test for stratified split logic in `tests/unit/test_modeling.py`
- [X] T034_test [P] [US3] Unit test for 5-fold cross-validation implementation in `tests/unit/test_modeling.py`
- [X] T035_test [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T033_impl [US3] Implement `code/modeling.py` to perform a **stratified train-test split based on 4 quantile bins of the target variable (yield strength)**; save `train_split` and `test_split` artifacts
- [X] T034_impl [US3] Implement Random Forest, Gradient Boosting, and Ridge Regression training using **Repeated Stratified K-Fold (5 repeats)** with a fixed random seed on the `train_split` from T033_impl
- [X] T035 [US3] Generate a distribution of RAW 5-fold R² scores (list of floats, not aggregated) from the Repeated 5-fold CV repeats
- [X] T036a [US3] Run k-fold CV to generate the distribution of R² scores (ensure repeated structure is preserved)
- [X] T036b [US3] Perform multiple bootstrap resamples on the RAW k-fold CV scores (from T035) using the percentile method to generate a distribution of confidence intervals
- [X] T038a [US3] Implement permutation importance testing: Run on EACH of the bootstrap resampled datasets to generate multiple sets of feature importance ranks
- [X] T038b [US3] Generate final report comparing R², MAE, RMSE for all models and identifying the best performer; save to `reports/model_comparison_report.json`
- [X] T041_calc [US3] [CALCULATION ONLY] Calculate the standard deviation of feature importance ranks across multiple bootstrap resamples.; write the raw float value to `data/logs/sc003_stability_metric.log`; **DO NOT evaluate threshold or halt pipeline**
- [X] T041_report [US3] [REPORTING ONLY] Read `data/logs/sc003_stability_metric.log`; if value >= 2.0, write "UNSTABLE" to `reports/model_comparison_report.json` under `sc003_status`; otherwise write "STABLE"; **DO NOT halt pipeline**
- [X] T039 [US3] Implement `code/traceability.py` to extract metrics from logs and update `state/projects/PROJ-525-predicting-the-yield-strength-of-bcc-all.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `README.md` and `quickstart.md`
- [X] T041 [P] Code cleanup and refactoring for readability
- [X] T042 [P] Performance optimization to ensure full pipeline runs < 6 hours on CI
- [X] T043 [P] Additional unit tests for edge cases (log domain errors, missing elements)
- [X] T044 [P] Run quickstart.md validation to ensure end-to-end reproducibility

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
- **Note on T029c/T029d**: These tasks (PCA, Residualization) have been REMOVED from the mandatory list as they are not authorized in `spec.md` FR-003.2. Only L1/RFE is implemented.
- **Note on T017**: This task enforces the hard gate required by FR-004. If the plan's "conditional" analysis for N < 80 is required, it must be implemented as a separate branch or the spec amended.
- **Note on T041**: Split into T041_calc (pure calculation) and T041_report (evaluation) to separate metric generation from success criterion reporting.