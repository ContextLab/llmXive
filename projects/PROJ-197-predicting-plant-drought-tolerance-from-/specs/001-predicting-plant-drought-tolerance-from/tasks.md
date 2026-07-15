# Tasks: Predicting Plant Drought Tolerance from Publicly Available Physiological and Genomic Data

**Input**: Design documents from `/specs/001-drought-tolerance-prediction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project directory structure with explicit directories: `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `docs/reports/` <!-- ATOMIZE: requested -->
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing `scikit-learn>=1.3.0`, `xgboost>=2.0.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `scipy>=1.11.0`, `requests>=2.31.0`, `imblearn>=0.11.0`, `pyyaml>=6.0.0`, `joblib>=1.3.0`, `pytest>=7.4.0`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/logging.py` to create `DataPipelineLog` with methods for recording source URLs, download status, imputation details, merge statistics, and **excluded species** (FR-007)
- [ ] T005 [P] Create `code/utils/stats.py` implementing DeLong's test for paired AUCs and standard statistical utilities
- [X] T006 [P] Setup `code/config.py` to manage species lists, random seeds (), and synthetic data parameters
- [X] T007 Create base data entities: `SpeciesRecord` (fields: `species_id`, `traits_dict`, `genomic_markers`, `label`) and `ModelResult` (fields: `model_name`, `metrics`, `hyperparameters`, `feature_importance`) in `code/models/entities.py`
- [~] T016 [P] [Foundational] Implement `code/data/generate.py` to generate a **synthetic phylogenetic distance matrix** for the species list. **Logic**: Create N x N symmetric matrix (N=species count), zero diagonal, off-diagonal values uniformly distributed between a lower bound and an upper bound. Save to `data/processed/synthetic_phylo_matrix.npy`. (FR-009)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Download real TRY data, generate synthetic genomic data (per plan), merge into a clean dataset with imputation.

**Independent Test**: Can be fully tested by executing `code/data/ingest.py` and verifying the output CSV contains the expected number of rows (species) and columns, with no missing values for the target label.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data/download.py` to fetch TRY database CSVs with exponential backoff and checksum verification. (FR-001)
- [~] T012 [US1] Implement `code/data/generate.py` to generate **synthetic genomic features** and **synthetic drought labels**. **Logic**: Use `random_state=42`. **Gene List (20)**: `NCED3`, `ABF3`, `P5CS`, `DREB2A`, `ERF1`, `ABI5`, `RD29A`, `COR15A`, `LEA3`, `HSP70`, `SOD`, `APX1`, `CAT1`, `GPX1`, `MDHAR`, `DHAR`, `GSTU`, `ZAT12`, `WRKY33`, `MYB96`. **Label Logic**: `label = 1` if `sum(genomic_markers) >= 12`, else `0`. Output to `data/processed/synthetic_genomics.csv`. (FR-001, Plan Validation Mode)
- [X] T013 [US1] Implement `code/data/ingest.py` to merge TRY traits (from T011) and synthetic genomic data (from T012) by species ID. **Explicitly detect species present in TRY but missing in genomic data, flag them with "no_genomic_data" or exclude them, and log the count.** (FR-002)
- [X] T014a [US1] Implement `code/data/ingest.py` to apply **standard MICE** imputation for missing continuous traits using `sklearn.impute.IterativeImputer` (`max_iter=10`, `random_state=42`). (FR-002)
- [X] T014b [US1] Implement logic in `code/data/ingest.py` to drop columns if imputation fails after max iterations. (FR-002)
- [X] T014c [US1] Implement logging in `code/data/ingest.py` to record imputation counts, dropped columns, and exclusion events. (FR-007)
- [X] T015 [US1] Implement `code/data/split.py` to perform stratified train-test split by drought label, with fallback to leave-one-out if N is small. (FR-003)

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for TRY download retry logic with 404 simulation in `tests/unit/test_download.py`
- [X] T009 [P] [US1] Unit test for synthetic genomic data generation consistency (seed 42) in `tests/unit/test_synthetic.py`
- [ ] T010 [P] [US1] Integration test for full merge pipeline (TRY + Synthetic) producing valid DataFrame in `tests/integration/test_ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. A clean `data/processed/merged_dataset.csv` should exist.

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train RF, XGBoost, and KNN Baseline on CPU; validate performance against baseline using DeLong's test.

**Independent Test**: Run `code/models/train.py` and `code/models/evaluate.py`; verify models train without OOM/GPU errors, cross-validation scores are logged, and DeLong's test confirms significance.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for stratified split logic ensuring label balance in `tests/unit/test_split.py`
- [ ] T018 [P] [US2] Integration test verifying RF and XGBoost train within 30 mins on 2-core CPU without GPU errors in `tests/integration/test_train.py`
- [ ] T019 [P] [US2] Unit test for DeLong's test implementation against known synthetic AUC pairs in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T020a [P] [US2] Implement `code/models/train.py` to train RandomForest using `joblib` for parallelism on 2 cores. (FR-004)
- [ ] T020b [P] [US2] Implement `code/models/train.py` to train XGBoost using `joblib` for parallelism on 2 cores. (FR-004)
- [ ] T020c [P] [US2] Implement `code/models/train.py` to perform `n_estimators` grid search across values {100, 200, 500} for both models. (FR-004)
- [ ] T021 [P] [US2] Implement `code/models/train.py` to train KNN Baseline (K=5) using the **synthetic phylogenetic distance matrix** (from T016). (FR-009)
- [ ] T022 [US2] Implement `code/models/evaluate.py` to calculate ROC-AUC on held-out test set and log best model. (FR-004)
- [ ] T023 [US2] Implement `code/models/evaluate.py` to perform DeLong's test comparing best model AUC vs. Baseline AUC. **Verify p < 0.05 AND AUC diff > 0.05** as per SC-001. (FR-010, SC-001)
- [ ] T024 [US2] Add error handling in `code/models/train.py` to catch OOM/GPU exceptions and fail gracefully with clear messages (Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Models are trained and statistically compared.

---

## Phase 5: User Story 3 - Statistical Comparison and Interpretation (Priority: P3)

**Goal**: Compare classifiers via paired t-test and generate feature importance rankings.

**Independent Test**: Run `code/models/compare.py`; verify p-value is generated and top features are ranked distinguishing genomic vs. physiological.

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test for paired t-test on synthetic CV score arrays in `tests/unit/test_compare.py`
- [ ] T026 [P] [US3] Integration test verifying feature importance output matches top 10 expected synthetic features in `tests/integration/test_compare.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/models/compare.py` to perform paired t-test on k-fold CV AUC scores for RF vs. XGBoost (FR-005, SC-003)
- [ ] T028 [P] [US3] Implement `code/models/compare.py` to calculate Permutation Feature Importance for the best model, distinguishing between genomic markers and physiological traits. (FR-006)
- [ ] T029 [US3] Implement `code/models/compare.py` to generate a final report at `docs/reports/final_analysis.md`. **Validation Logic**: Use **Validation Gene List (15)**: `DREB2A`, `ERF1`, `ABI5`, `RD29A`, `COR15A`, `LEA3`, `HSP70`, `SOD`, `APX1`, `CAT1`, `GPX1`, `MDHAR`, `DHAR`, `GSTU`, `ZAT12`. Check if count of these genes in Top 10 features >= 3. (SC-005)
- [ ] T030 [US3] Ensure all metrics and logs are written to `data/logs/metrics.json` for reproducibility (Plan: Single Source of Truth)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/reports/` including the limitation note regarding synthetic data
- [ ] T032 Code cleanup and refactoring to ensure type hinting and docstrings are complete
- [ ] T033 [P] Add unit tests for edge cases: empty species list, missing TRY data, single species in dataset
- [ ] T034 Run `quickstart.md` validation: Execute `pytest -q --timeout=1800` and **verify runtime < 30 minutes** (FR-008, SC-002)
- [ ] T035 Verify `code/requirements.txt` pins versions to ensure reproducibility (Constitution: Reproducibility)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) **AND** T015 (Split) output is available. US2 depends on US1 data.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) **AND** US2 output (trained models) is available.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **US1** can start immediately.
- **US2** implementation can start once T015 (Split) is complete.
- **US3** implementation can start once US2 is complete.
- All tests for a user story marked [P] can run in parallel (after code exists).
- Different user stories can be worked on in parallel by different team members **once their specific data dependencies are met**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after code exists):
Task: "Unit test for TRY download retry logic"
Task: "Unit test for synthetic genomic data generation"
Task: "Integration test for full merge pipeline"

# Launch all models for User Story 1 together:
Task: "Implement download.py"
Task: "Implement ingest.py"
Task: "Implement split.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify synthetic data generation and merge)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US2 models)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - **Must wait for T015 (Split) from US1**
 - Developer C: User Story 3 (Analysis) - **Must wait for US2**
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All genomic data and labels are SYNTHETIC (per Plan). No real NCBI RefSeq or TRY genomic data is used.
- **Critical Constraint**: Phylogenetic MICE is replaced by standard MICE due to lack of verified phylogenetic tree.
- **Critical Constraint**: Baseline model uses a synthetic distance matrix.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence