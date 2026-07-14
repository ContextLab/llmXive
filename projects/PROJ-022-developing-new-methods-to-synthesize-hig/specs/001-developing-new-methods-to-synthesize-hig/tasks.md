# Tasks: Developing New Methods to Synthesize High-Performance Membranes using Sustainable Materials

**Input**: Design documents from `/specs/001-sustainable-membrane-synthesis/`
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

- [ ] T001a [P] Create directory structure: `code/`, `data/raw`, `data/processed`, `data/reports`, `tests/`, `artifacts/`
- [ ] T001b [P] Create `requirements.txt` pinning `rdkit==2023.9.5`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `pyyaml==6.0.1`, `datasets==2.14.6`
- [ ] T001c [P] Create `.gitignore` rules for `data/raw/*`, `data/processed/*`, `*.pkl`, `__pycache__`, `*.log`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Setup `data/raw` and `data/processed` directories with `.gitignore` rules for large files
- [ ] T005 [P] Implement `utils/logging_config.py` for structured logging across pipeline stages
- [ ] T006 [P] Setup `utils/constants.py` with unit conversion factors (Barrer, LMH/bar), random seed=42, and polymer-class lookup table for imputation
- [ ] T007 Create base `PolymerRecord` dataclass in `code/ingestion/models.py`
- [ ] T008 Configure error handling infrastructure with custom `DataInsufficientError` in `code/utils/errors.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Standardization (Priority: P1) 🎯 MVP

**Goal**: Aggregate sparse literature data, standardize units to Barrer, and handle missing data via imputation or halting.

**Independent Test**: The pipeline can be tested by running the ingestion script against a mock CSV of a representative set of literature entries and verifying the output dataframe contains standardized units, imputed missing values, and a valid count of non-null performance records.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for unit conversion in `tests/contract/test_standardize_units.py`
- [ ] T010 [P] [US1] Integration test for missing data halting logic in `tests/integration/test_missing_data_flow.py`

### Implementation for User Story 1

- [ ] T011a [US1] Implement `code/ingestion/manual_extraction.py` to parse structured CSV from manual literature review (FR-001 source 3)
- [ ] T011b [US1] Implement `code/ingestion/automated_fetch.py` to fetch real data from arXiv (query: "membrane OR polymer") and OpenPolymer (HuggingFace dataset ID: `openpolymer/v1`)
- [ ] T012 [US1] Implement `code/ingestion/handle_missing_data.py` with logic: >20% missing -> halt with `ERR_DATA_INSUFFICIENT`; A small percentage -> impute using polymer-class averages (defined by SMILES substructure lookup in `code/utils/constants.py`) AND generate `clarification_flag.json`
- [ ] T013 [US1] Create `code/ingestion/load_literature_data.py` to merge manual and automated sources into a unified dataframe
- [ ] T014 [US1] Implement validation step in `code/ingestion/validate_dataset.py` to count valid records (must be ≥30) and generate `missing_data_report.json` if needed
- [ ] T015 [US1] Add logic to flag "high variance" entries (conflicting metrics for same polymer) and exclude from primary training set
- [ ] T016 [US1] Generate `data/processed/standardized_polymers.csv` with standardized units and imputed values

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Generate molecular descriptors using RDKit and train a CPU-tractable Random Forest/Gradient Boosting regressor.

**Independent Test**: The training module can be tested by running on the standardized dataset from US-1 and verifying the model outputs a feature importance ranking and a cross-validated R² score ≥ 0.1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`
- [ ] T018 [P] [US2] Integration test for model training runtime fallback in `tests/integration/test_training_runtime.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/features/calculate_descriptors.py` to compute VdW volume, H-bond counts, and MW using RDKit (handle parse failures gracefully)
- [ ] T020 [US2] Implement `code/features/feature_selection.py` to perform Recursive Feature Elimination (RFE) or PCA to mitigate overfitting (FR-011)
- [ ] T021 [US2] Implement `code/modeling/train_model.py` with Random Forest (max depth of a moderate scale, n_estimators 100) and fallback logic: if runtime > 60m, reduce depth to 6, then 4 (per Plan Complexity Tracking)
- [ ] T022 [US2] Implement `code/modeling/cross_validate.py` to run stratified k-fold CV and report R² and MAE
- [ ] T023 [US2] Add categorical encoding for 'synthesis method' in the feature matrix (FR-008)
- [ ] T024 [US2] Add explicit disclaimer in model metadata that findings are associational, not causal (FR-007)
- [ ] T025 [US2] Save trained model artifact to `artifacts/model.pkl` and feature matrix to `data/processed/feature_matrix.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Candidate Screening and Statistical Validation (Priority: P3)

**Goal**: Screen a virtual library of sustainable candidates, rank them, and statistically compare against petrochemical benchmarks.

**Independent Test**: The screening module can be tested by providing a known set of "high-performance" and "low-performance" dummy candidates and verifying the ranking order matches the expected performance distribution.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for statistical test output format in `tests/contract/test_statistical_test.py`
- [ ] T027 [P] [US3] Integration test for power analysis report generation in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

- [ ] T028a [US3] Implement `code/screening/generate_bio_candidates.py` to create a diverse set of sustainable candidate SMILES

The research question is to identify sustainable molecular structures, and the method involves generating candidate SMILES strings based on sustainability criteria, as discussed in relevant literature (e.g., DOI:10.1021/acs.jcim.0c01234). from cellulose, chitosan, lignin templates using deterministic template expansion (seed=42, A set of derivatives/base will be generated.)
- [ ] T028b [US3] Implement `code/screening/generate_petro_benchmarks.py` to create a control set of petrochemical benchmark SMILES using deterministic template expansion (seed=42, 10 derivatives/base)
- [ ] T029 [US3] Implement `code/screening/rank_candidates.py` to predict performance for bio-candidates and petrochemical benchmarks using the trained model
- [ ] T030 [US3] Implement `code/screening/statistical_test.py` to run Mann-Whitney U test comparing predicted distributions (not experimental ground truth)
- [ ] T031 [US3] Implement `code/screening/generate_validation_protocol.py` to generate `validation_protocol.md` mandating experimental validation of top candidates (FR-009 requirement artifact)
- [ ] T032 [US3] Implement `code/screening/power_analysis.py` to calculate detectable effect size for N=30 and generate `data/reports/power_analysis_report.json`
- [ ] T033 [US3] Generate `data/reports/screening_results.json` with ranked candidates and p-values
- [ ] T034 [US3] Create `candidate_recommendation_report.md` listing top candidates for *future* experimental validation (FR-009)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Future Work (Priority: P4)

**Goal**: Compile final results and validate citations.

- [ ] T035 [US3] Implement `code/reporting/generate_final_report.py` to aggregate feature importance, statistical tests, and candidate lists
- [ ] T036 [US3] Implement `validate_citations.py` to re-check all references in the final report against primary sources by running `python code/reporting/validate_citations.py` and checking DOI resolution (Constitution Principle II)
- [ ] T037 [P] Run end-to-end pipeline validation script `code/main_pipeline.py` to verify a bounded runtime limit on a 2-core CPU

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for unit conversion in tests/contract/test_standardize_units.py"
Task: "Integration test for missing data halting logic in tests/integration/test_missing_data_flow.py"

# Launch all models for User Story 1 together:
Task: "Create base PolymerRecord dataclass in code/ingestion/models.py"
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