# Tasks: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Input**: Design documents from `/specs/001-predict-poissons-ratio/`
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
- [ ] T002 Initialize Python 3.11 project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, skbio) in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/__init__.py` and basic project scaffolding
- [ ] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/` paths, random seeds)
- [ ] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels)
- [ ] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics) including `measurement_method` and `source_method` fields to capture provenance metadata
- [ ] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Filtering (Priority: P1) 🎯 MVP

**Goal**: Download compositional and property data from public repositories, filter to valid monolithic aluminum alloys, and ensure unit consistency.

**Independent Test**: Can be fully tested by running the data extraction script against the source databases and verifying the script reports the count of filtered entries and that all entries have complete composition and property records.

### Implementation for User Story 1

- [ ] T009 [US1] Implement data extraction for Materials Project in `code/data_extraction.py` (fetch aluminum alloys via https://next-gen.materialsproject.org/api/v2/, validate against AlloyRecord schema from T007 ensuring `measurement_method` and `source_method` fields are populated, save to `data/raw/mp_aluminum.json`)
- [ ] T010 [US1] Implement data extraction for NIST Materials Data Repository in `code/data_extraction.py` (fetch aluminum alloys via https://www.nist.gov/mml/materials-data-repository, validate against AlloyRecord schema from T007 ensuring `measurement_method` and `source_method` fields are populated, save to `data/raw/nist_aluminum.json`)
- [ ] T011 [US1] Implement filtering logic in `code/data_cleaning.py` to select monolithic alloys with non-missing Poisson's ratio, Young's modulus, and Cu/Mg/Si/Zn/Mn composition
- [ ] T012 [US1] Implement unit normalization in `code/data_cleaning.py` (convert elastic constants to GPa, calculate atomic fractions summing to 1.0)
- [ ] T013 [US1] Implement exclusion logic in `code/data_cleaning.py` for entries where major element sum < 0.95 (log warning, drop row)
- [ ] T014 [US1] Implement positive verification logic in `code/data_cleaning.py` for FR-009: query the `measurement_method` field for each entry; explicitly retain ONLY entries where the method contains keywords 'ultrasonic', 'resonant', 'pulse-echo', or 'dynamic'; explicitly EXCLUDE entries where the method is 'calculated', 'derived', 'derived_from_Youngs_modulus', or missing/unknown; log the specific exclusion reason for each dropped entry; ensure the output dataset includes a `measurement_source` field confirming the verified method
- [ ] T015 [US1] Implement main orchestration for data pipeline in `code/main.py` (run extraction -> cleaning -> save `data/processed/filtered_alloys.csv`)
- [ ] T016 [US1] Implement error handling in `code/main.py` to raise SystemExit(1) with message "ERROR: Insufficient data (N < 50 entries)" if < 50 valid entries remain

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest regressor using ILR-transformed features, perform 5-fold cross-validation, and evaluate on a held-out test set.

**Independent Test**: Can be fully tested by training the model on the filtered dataset, running 5-fold cross-validation, and verifying the mean absolute error is computed and logged on the held-out test set.

### Implementation for User Story 2

- [ ] T017 [US2] Implement ILR transformation in `code/data_cleaning.py` using `skbio` for Cu, Mg, Si, Zn, Mn atomic fractions (DEPENDS ON T012/T013 completion)
- [ ] T018 [US2] Implement feature vector construction in `code/modeling.py` (combine ILR features with target Poisson's ratio)
- [ ] T019 [US2] Implement a standard train/test split logic

The research question, method, and references remain unchanged as per the planning document requirements. in `code/modeling.py` with fixed random seed
- [ ] T020 [US2] Implement Random Forest training with 5-fold cross-validation in `code/modeling.py` (log CV MAE)
- [ ] T021 [US2] Implement test set evaluation in `code/modeling.py` (compute and log test-set MAE)
- [ ] T022 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl`)
- [ ] T023 [US2] Implement results logging in `code/modeling.py` (save ModelMetrics to `docs/outputs/model_metrics.json`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

**Goal**: Extract feature importance scores, back-transform to compositional space, compute VIF diagnostics, and frame findings as associational.

**Independent Test**: Can be fully tested by running the feature importance extraction and verifying the output contains ranked elements with non-zero importance scores and an associational framing statement.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement feature importance extraction from Random Forest in `code/analysis.py`
- [ ] T025 [US3] Implement back-transformation logic in `code/analysis.py` to map ILR-importance back to original elemental importance scores
- [ ] T026 [US3] Implement VIF calculation in `code/analysis.py` for raw predictors (Cu, Mg, Si, Zn, Mn) and flag if VIF > 5
- [ ] T027 [US3] Implement result ranking and comparison logic in `code/analysis.py` (identify top 2 elements, compare magnitudes)
- [ ] T028 [US3] Implement associational framing in `docs/outputs/results_report.md` (explicitly state "associational, not causal" due to observational data)
- [ ] T029 [US3] Implement final report generation in `code/main.py` (aggregate metrics, VIF, importance, and framing into `docs/outputs/final_report.md`)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` (quickstart.md, data-model.md)
- [ ] T035 Code cleanup and refactoring
- [ ] T036 Performance optimization (ensure all steps run within 6h on CPU)
- [ ] T037 [P] Unit tests for data cleaning logic in `tests/unit/test_data_cleaning.py`
- [ ] T038 [P] Unit tests for modeling logic in `tests/unit/test_modeling.py`
- [ ] T039 [P] Contract tests for data schemas in `tests/contract/test_schemas.py`
- [ ] T040 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015 (clean data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T022 (trained model)

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
# Launch all tasks for User Story 1 data extraction in parallel:
Task: "Implement data extraction for Materials Project in code/data_extraction.py"
Task: "Implement data extraction for NIST Materials Data Repository in code/data_extraction.py"
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
   - Developer B: User Story 2 (Modeling)
   - Developer C: User Story 3 (Analysis)
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