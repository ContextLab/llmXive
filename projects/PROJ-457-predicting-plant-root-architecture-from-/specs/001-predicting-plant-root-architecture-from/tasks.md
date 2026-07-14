# Tasks: Predicting Plant Root Architecture from Soil Nutrient Availability

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

- [ ] T001 Create project structure per implementation plan: `code/`, `tests/`, `data/raw/`, `data/processed/`, `artifacts/`, `artifacts/models/`, `artifacts/plots/`, `artifacts/reports/`
- [ ] T002 Initialize Python 3.11+ project: Create `code/requirements.txt` with dependencies `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `geopandas` and run `pip install -r code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` to load paths, seeds, and constants from `config.yaml`
- [ ] T007 [P] Create base data models/classes for `RootPhenotypeRecord` and `SoilNutrientRecord` in `code/models.py`
- [ ] T005 [P] Implement schema validation contracts in `tests/contract/test_schemas.py` (raw_root, raw_soil, merged, output) - *Prerequisite: T007*
- [ ] T006 [P] Setup logging infrastructure in `code/config.py` (file + console handlers)
- [ ] T008 Setup environment configuration management (`.env` or `config.yaml` template)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest root phenotype data from RootReader/PlantPheno and soil nutrient data from ISRIC, filter for valid observations (n≥20 per species), merge with spatial interpolation, and produce a cleaned, merged dataset.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a sample subset and verifying the output CSV contains the required columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen) with no null values in the predictor columns and at least 20 rows per species.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_schemas.py`
- [ ] T010 [P] [US1] Unit test for KNN imputation logic (k=5, Euclidean) in `tests/unit/test_preprocessing.py`
- [ ] T011 [P] [US1] Unit test for log-transformation handling of zeros/negatives in `tests/unit/test_preprocessing.py`
- [ ] T012 [US1] Integration test for full ingestion pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `data_ingestion.py` to download/parse RootReader and PlantPheno data (FR-001)
- [ ] T014 [P] [US1] Implement `data_ingestion.py` logic to fetch ISRIC soil data via verified loader OR load user-provided file (fallback for reproducibility) and handle missing coordinates via nearest neighbor interpolation within a defined spatial threshold (FR-002, FR-012)
- [ ] T015 [US1] Implement filtering logic in `data_ingestion.py` to exclude species with n<20 (FR-001) - *Note: Combine with T015.1 for full filtering*
- [ ] T015.1 [US1] Implement filtering logic in `data_ingestion.py` to explicitly exclude rows where `data_source_type` is 'experimental' or 'controlled' (FR-012) - *Prerequisite: T013*
- [ ] T018 [US1] Merge root and soil datasets in `data_ingestion.py` ensuring no data leakage (species-level integrity) - *Prerequisite: T015, T015.1*
- [ ] T016 [US1] Implement `preprocessing.py` for log-transformation of root metrics and z-score normalization of nutrients (FR-003, Const VII) - *Prerequisite: T018*
- [ ] T017 [US1] Implement `preprocessing.py` KNN imputation (k=5, Euclidean, numeric only) with mean fallback (FR-003) - *Prerequisite: T018*
- [ ] T019 [US1] Add logging for exclusion counts (species < 20, missing nutrients, experimental data) and transformation steps

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Fit Linear Mixed-Effects Models (LMM) and baseline Random Forest models to quantify nutrient-architecture relationships, perform species-level cross-validation, and report statistical significance.

**Independent Test**: The modeling step can be tested by running the training script on the preprocessed dataset and verifying the output JSON contains R², RMSE, and p-values for the LMM coefficients, ensuring the random forest baseline is also evaluated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model output schema (R², p-values) in `tests/contract/test_schemas.py`
- [ ] T021 [P] [US2] Unit test for species-level stratified split logic in `tests/unit/test_preprocessing.py`
- [ ] T022 [US2] Integration test for model training and evaluation pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `modeling.py` to perform k-fold cross-validation split strictly by species (FR-006) - *Prerequisite: T018 (US1 output)*
- [ ] T024 [US2] Implement LMM fitting in `modeling.py` using `statsmodels` (REML, Satterthwaite p-values, species as random intercept) (FR-004)
- [ ] T025 [US2] Implement Random Forest baseline in `modeling.py` (max_depth=5) for comparison (FR-005)
- [ ] T026 [US2] Implement F-test for overall model significance and coefficient p-values in `modeling.py` (FR-008)
- [ ] T027 [US2] Implement multiple-comparison correction (Bonferroni or FDR) for hypothesis testing in `modeling.py` (FR-010)
- [ ] T028 [US2] Implement sensitivity analysis of nutrient coefficients against literature ranges (FR-011)
- [ ] T029 [US2] Generate output JSON with adjusted R², RMSE, p-values, and cross-validation mean R² for both models (FR-004, FR-005, FR-006)
- [ ] T029.1 [US2] Implement logic in `modeling.py` to calculate the difference between LMM R² and RF R² and evaluate if it is within the 5% threshold defined in SC-002 (FR-006, SC-002) - *Prerequisite: T029*

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate partial dependence plots, compile final report with statistical findings, and ensure output size constraints are met.

**Independent Test**: The reporting step can be tested by running the visualization script and verifying that PNG files are generated for partial dependence plots and that the total output size is ≤100MB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for report schema in `tests/contract/test_schemas.py`
- [ ] T031 [P] [US3] Unit test for file size constraint enforcement in `tests/unit/test_reporting.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `visualization.py` to generate partial dependence plots (wide percentile range) for nutrient-architecture relationships (FR-007)
- [ ] T033 [US3] Implement `visualization.py` to save figures as PNGs, enforcing total size ≤100MB (FR-007, SC-004)
- [ ] T034 [US3] Implement `reporting.py` to compile final report including R², p-values, plots, and associational framing (FR-009)
- [ ] T035 [US3] Implement `reporting.py` to document excluded species and data coverage metrics (SC-001, SC-005)
- [ ] T035.1 [US3] Implement logic in `reporting.py` to calculate the merge success rate (merged count / total available) required by SC-001 (SC-001) - *Prerequisite: T034*
- [ ] T036 [US3] Verify biological plausibility of coefficients against literature in final report (FR-011, SC-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring (ensure PEP8 compliance)
- [ ] T039 Performance optimization (ensure execution ≤ 6 hours, RAM ≤ 6GB)
- [ ] T040 [P] Additional unit tests for edge cases (zero values, missing coords) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure reproducibility

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
Task: "Contract test for merged dataset schema in tests/contract/test_schemas.py"
Task: "Unit test for KNN imputation logic in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement data_ingestion.py to download/parse RootReader and PlantPheno data"
Task: "Implement preprocessing.py for log-transformation and z-score normalization"
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
- **Constraint Check**: All tasks designed for CPU-only (2 cores, 7GB RAM), no GPU, ≤6h runtime. No 8-bit/4-bit quantization or large model training.