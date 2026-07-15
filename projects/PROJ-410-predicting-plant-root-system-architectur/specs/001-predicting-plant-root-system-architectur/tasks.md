# Tasks: Predicting Plant Root System Architecture from Genomic Data

**Input**: Design documents from `/specs/001-predict-root-architecture/`
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

- [X] T001 Create project directories: `data/raw`, `data/processed`, `code/`, `tests/`, `contracts/`
- [X] T002 Create `projects/PROJ-410-predicting-plant-root-system-architectur/` root structure files (`.gitignore`, `README.md`)
- [X] T003 [P] Create `requirements.txt` file with pinned versions for `scikit-learn`, `pandas`, `numpy`, `scipy`, `shap`, `matplotlib`, `seaborn`, `pyyaml`
- [X] T004 [P] Create `.flake8` configuration file with linting rules
- [X] T005 [P] Add `black` pre-commit hook configuration
- [X] T006 [P] Create `code/config.py` with paths and random seeds
- [X] T007 [P] Define default hyperparameters in `code/config.py` (regularization strengths, tree depths)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 [P] Create `contracts/unified_dataset.schema.yaml` defining schema for unified data
- [ ] T009 [P] Create `contracts/model_output.schema.yaml` defining schema for model results
- [ ] T010 [P] Implement `code/download.py` with full fetch logic for 1001 Genomes/ATRDB
- [ ] T011 [P] Implement `code/mock_data.py` to generate synthetic data with correct schema
- [ ] T012 [P] Implement fallback logic in `code/download.py` to trigger mock data if fetch fails
- [X] T013 [P] Implement `code/verify_fit.py` to check variable existence, log errors, and return status code
- [X] T014 [P] Implement explicit verification task in `code/download.py` to confirm real source reachability before fallback
- [~] T015 Setup `pytest` configuration in `projects/PROJ-410-predicting-plant-root-system-architectur/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Harmonization and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download/harmonize genomic and phenotypic data, encode genotypes (0,1,2), and create stratified splits.

**Independent Test**: Run preprocessing on a small subset; verify output contains matched pairs, correct encoding, and stratified splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US1] Contract test for `UnifiedDataset` schema in `tests/contract/test_unified_dataset.py`
- [X] T017 [P] [US1] Unit test for genotype encoding logic (0,1,2) in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [X] T018 [US1] Implement accession matching logic in `code/preprocess.py` (FR-002)
- [X] T019 [US1] Implement genotype encoding (0,1,2) in `code/preprocess.py` (FR-002)
- [X] T020 [US1] Implement missingness filter (>5%) in `code/preprocess.py` (FR-002) <!-- FAILED: unspecified -->
- [ ] T021 [US1] Save `data/processed/unified_dataset.parquet` with metadata flag (real vs. mock)
- [X] T022 [US1] Implement stratified split logic (80/10/10 train/val/test) per nutrient condition in `code/preprocess.py` (FR-003)
- [ ] T023 [US1] Save `data/processed/train.parquet`, `val.parquet`, `test.parquet` per nutrient condition
- [~] T024 [US1] Add logging for excluded accessions and missing data counts (Edge Case: naming inconsistencies)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Model Training and Evaluation (Priority: P2)

**Goal**: Train baseline models (Linear, RF, GB) per nutrient condition and evaluate against null model.

**Independent Test**: Train models on stratified dataset; verify R², MAE, and CV scores are calculated and stored.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US2] Unit test for L1/L2 regularization application in `tests/unit/test_train.py`
- [ ] T026 [P] [US2] Integration test for model training loop per nutrient condition in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T027 [US2] Implement and train null model (intercept-only) per nutrient condition; save `data/processed/null_model_metrics.csv` (FR-005)
- [ ] T028 [US2] Implement Lasso/ElasticNet training loop in `code/train.py` (FR-004, FR-010)
- [ ] T029 [US2] Implement hyperparameter search for regularization in `code/train.py`
- [ ] T030 [US2] Implement Random Forest training in `code/train.py` (FR-004)
- [ ] T031 [US2] Implement Gradient Boosting training in `code/train.py` (FR-004)
- [ ] T032 [US2] Implement PCA/L1 regularization strictly for Linear Models if features > 5000; save transformed features to `data/processed/pca_features.parquet` (FR-010)
- [ ] T033 [US2] Load null model metrics from `data/processed/null_model_metrics.csv` and compare against trained models (FR-005, SC-001)
- [X] T034 [US2] Implement 95% CI calculation method in `code/evaluate.py`
- [~] T035 [US2] Implement cross-validation scoring for each model/condition (SC-003)
- [ ] T036 [US2] Save `data/processed/model_metrics.csv` with performance rankings per condition

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Significance Testing (Priority: P3)

**Goal**: Identify predictive markers via SHAP/Permutation importance and perform statistical significance testing.

**Independent Test**: Run feature importance and 1000-iteration permutation tests; verify p-values and significant markers.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T037 [P] [US3] Unit test for nested permutation loop (no data leakage) in `tests/unit/test_evaluate.py`
- [X] T038 [P] [US3] Integration test for SHAP value calculation in `tests/integration/test_feature_importance.py`

### Implementation for User Story 3

- [X] T039 [US3] Implement variance filtering in `code/evaluate.py`
- [X] T040 [US3] Implement nested loop logic (feature selection inside permutation) in `code/evaluate.py` (Plan Phase 5)
- [~] T041 [US3] Execute a permutation test for each model/condition; calculate p-values (FR-007, SC-002)
- [~] T042 [US3] Apply Benjamini-Hochberg correction to model-level tests (one per condition) (Plan Phase 5)
- [X] T043 [US3] Implement SHAP value calculation for tree models in `code/visualize.py` (FR-006)
- [X] T044 [US3] Implement Lasso coefficient extraction for linear models in `code/visualize.py` (FR-006)
- [~] T045 [US3] Perform Stability Selection with multiple bootstrap samples to rank marker stability. (SC-004)
- [ ] T046 [US3] Generate feature importance plot in `code/visualize.py`
- [ ] T047 [US3] Generate prediction vs. actual scatter plot in `code/visualize.py`
- [ ] T048 [US3] Append standardized disclaimer: "Findings are associational and do not imply causation" to all reports (FR-009)
- [ ] T049 [US3] Save `data/processed/results.json` and `data/processed/figures/`
- [ ] T050 [US3] Implement null-result detection logic: if p >= 0.05 for all models, flag environmental dominance in report (Edge Cases)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure CI compliance

- [ ] T051 [P] Run contract tests against `contracts/unified_dataset.schema.yaml` and `contracts/model_output.schema.yaml` (Plan Phase 7)
- [ ] T052 [P] Validate schema compliance of output files
- [ ] T053 [P] Implement resource monitoring in `code/monitor.py`
- [ ] T054 [P] Execute CI simulation for runtime (≤6h) and memory (<7GB) constraints via CI simulation (FR-004, SC-005)
- [ ] T055 Code cleanup: Ensure all random seeds are fixed in `config.py` for reproducibility (Constitution I)
- [ ] T056 Add execution instructions to `README.md`
- [ ] T057 Add data availability disclaimer to `README.md` (Plan Phase 7)
- [ ] T058 Run `quickstart.md` validation to ensure pipeline runs end-to-end on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

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
Task: "Contract test for UnifiedDataset schema in tests/contract/test_unified_dataset.py"
Task: "Unit test for genotype encoding logic in tests/unit/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py"
Task: "Implement code/preprocess.py"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Analysis & Viz)
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