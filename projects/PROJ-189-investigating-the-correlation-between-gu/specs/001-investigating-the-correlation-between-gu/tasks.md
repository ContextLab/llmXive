# Tasks: Gut Microbiome and Cognitive Decline Analysis

**Input**: Design documents from `/specs/001-investigating-the-correlation-between-gu/`
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

- [ ] T001a Create root project directory `projects/PROJ-189-investigating-the-correlation-between-gu/`
- [ ] T001b Create subdirectories: `data/raw`, `data/processed`, `data/models`, `code`, `code/utils`, `tests`, `tests/contract`, `tests/integration`, `tests/unit`, `docs`
- [ ] T001c Initialize `.gitignore` with patterns for large data files (`data/raw/*`), Python cache (`__pycache__`), and environment files (`venv/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement deterministic data fetching utilities with checksum validation in `code/utils/data_fetchers.py`
- [ ] T006 Setup logging infrastructure and memory usage monitoring in `code/utils/logging.py`
- [X] T007 Create base data models/entities (Sample, Taxon) in `code/utils/data_models.py`
- [ ] T008 Implement CPU-only execution guard and resource limit checks (≤7GB RAM, ≤6h) in `code/utils/resource_guard.py`
- [~] T009 Setup environment configuration management for dataset paths and random seeds <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw AGP 16S data and HRS cognitive metadata, merge by participant ID, filter for age ≥ 60, and produce a clean analysis-ready dataset using Rarefaction (per Spec FR-002) and document the process.

**Independent Test**: Can be fully tested by executing `code/01_data_ingestion.py` and `code/02_preprocessing.py` and verifying the output dataframe contains ≥ 500 rows where every row has non-null values for at least 5 microbial genera and 1 cognitive score column.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are "Write Test Code" tasks. They must be executed AFTER implementation tasks.

- [X] T010 Write contract test code for merged dataframe schema in `tests/contract/test_data_merge.py`
- [X] T011 Write integration test code for age filtering and missing value imputation in `tests/integration/test_preprocessing.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement AGP 16S taxonomic data fetcher from official Qiita/EBI source in `code/01_data_ingestion.py`
- [X] T013 [US1] Implement HRS cognitive metadata fetcher from official HRS portal in `code/01_data_ingestion.py` <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement participant ID merge logic with overlap logging (≥500 samples required) in `code/01_data_ingestion.py`
- [X] T015 [US1] Implement age ≥ 60 filter and covariate (BMI, education) imputation logic in `code/02_preprocessing.py`
- [ ] T016 [US1] Implement Rarefaction to uniform depth (minimum read depth of retained samples) and collapse to genus-level relative abundances in `code/02_preprocessing.py` (Per Spec FR-002)
- [ ] T017 [US1] Add validation to ensure no null values remain in the final analysis dataset
- [ ] T018 [US1] Log mismatch counts and proceed only if overlap ≥ 500 samples; fail gracefully otherwise

### Phase 3b: Test Execution (Run after Implementation)

- [ ] T045 Execute contract tests for merged dataframe schema
- [ ] T046 Execute integration tests for age filtering and missing value imputation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Associational Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman rank correlations between genus-level microbial abundances and cognitive test scores with FDR correction and CLR transformation on rarefied data.

**Independent Test**: Can be fully tested by running `code/03_correlation_analysis.py` and verifying the output table contains p-values adjusted via FDR, with no unadjusted p-values used for significance claims, and confirming the input data was CLR-transformed (on rarefied data).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 Write contract test code for correlation output schema (rho, p-value, adj-p-value) in `tests/contract/test_correlation.py`
- [ ] T020 Write integration test code for FDR correction logic in `tests/integration/test_correlation.py`

### Implementation for User Story 2

- [ ] T021 Implement Centered Log-Ratio (CLR) transformation for rarefied taxonomic data in `code/03_correlation_analysis.py`
- [ ] T022 [US2] Implement Spearman rank correlation calculation between genus abundances and cognitive scores (PRIMARY METHOD per Spec FR-003) in `code/03_correlation_analysis.py`
- [ ] T023 [US2] Implement Benjamini-Hochberg FDR correction (α = 0.05) on raw p-values in `code/03_correlation_analysis.py`
- [ ] T024 [US2] Filter and flag significant associations (adj-p < 0.05) and explicitly label as "associational" in results output
- [ ] T025 [US2] Generate summary report of significant genus-score pairs in `data/processed/correlation_results.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Robustness Validation (Priority: P3)

**Goal**: Train a Random Forest regressor with Nested Cross-Validation, validate against permutation null distribution, perform sensitivity analysis on rarefaction depth, and calculate VIF for collinearity on top predictive taxa.

**Independent Test**: Can be fully tested by executing `code/04_predictive_modeling.py` and `code/05_sensitivity_analysis.py` and verifying the hold-out R² score exceeds a high percentile threshold of the permutation null distribution (1000 shuffles) and memory usage remains within acceptable system limits.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 Write contract test code for model metrics schema (R², RMSE, VIF) in `tests/contract/test_model_metrics.py`
- [ ] T029 Write integration test code for permutation null distribution generation in `tests/integration/test_permutation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement Random Forest regressor training with Nested Cross-Validation (inner loop: hyperparameter tuning; outer loop: evaluation) in `code/04_predictive_modeling.py` (FR-004, Plan Summary)
- [ ] T031 [US3] Implement permutation test (sufficient shuffles) to generate null distribution for R² scores AND explicitly calculate and save the 95th percentile threshold to `data/processed/null_threshold.json` in `code/04_predictive_modeling.py`
- [ ] T032 [US3] Implement logic to identify and select 'top predictive taxa' based on Random Forest feature importance (mean decrease in impurity or permutation importance) and save list to `data/processed/top_taxa.json` in `code/04_predictive_modeling.py`
- [ ] T033 [US3] Calculate Variance Inflation Factors (VIF) for the 'top predictive taxa' (from T032) after CLR transformation; flag pairs with VIF > 5 and generate `data/processed/collinearity_review_log.json` (FR-006) in `code/04_predictive_modeling.py`
- [ ] T034 [US3] Implement sensitivity analysis sweep loop over rarefaction depths {a high predefined threshold, min_depth} in `code/05_sensitivity_analysis.py` (FR-005)
- [ ] T034b [US3] Execute model evaluation at each depth in the sweep and generate variance report in `data/processed/sensitivity_variance_report.json` (FR-005)
- [ ] T035 [US3] Add memory usage checks during permutation testing; sample taxa or reduce permutations if approaching GB limit (FR-007)
- [ ] T036 [US3] Save model artifacts (pickle/joblib) and SHAP values to `data/models/` with pinned hyperparameters and seeds
- [ ] T037 [US3] Verify hold-out R² score against the 95th percentile threshold (from T031) and record result in `data/processed/model_significance.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 Update `docs/paper_draft.md` Methods section with Rarefaction and Nested CV details
- [ ] T043 Update `docs/paper_draft.md` Results section with correlation and model findings
- [ ] T044 Update `docs/paper_draft.md` Discussion section with implications and limitations
- [ ] T038 Code cleanup and refactoring of `code/utils/` modules
- [ ] T039 Performance optimization for data loading and permutation loops
- [ ] T040 Additional unit tests for helper functions in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output; US2 results inform feature selection

### Within Each User Story

- Tests (if included) MUST be written (T010/T011) BEFORE implementation tasks, but EXECUTED AFTER implementation tasks (T045/T046).
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks can run in parallel
- All Foundational tasks can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all write-tests for User Story 1 together:
Task: "Write contract test code for merged dataframe schema in tests/contract/test_data_merge.py"
Task: "Write integration test code for age filtering and missing value imputation in tests/integration/test_preprocessing.py"
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