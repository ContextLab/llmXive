# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Input**: Design documents from `/specs/001-gut-microbiome-sleep-architecture/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `scikit-bio`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`
- [ ] T004b Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`
- [ ] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [ ] T006 [P] Implement deterministic synthetic data generator in `code/data_generator.py` (mock metagenomic counts + sleep metrics) to validate pipeline logic without real data
- [ ] T006a [P] Implement seed pinning in `code/data_generator.py` and `code/analysis.py` (e.g., `np.random.seed()`, `random.seed()`) to ensure reproducibility per Constitution Principle I
- [ ] T007 Create base data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [ ] T008 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [ ] T009 Setup environment configuration management (`.env` template, `requirements.txt`)
- [ ] T009a Implement Reference-Validator Agent logic in `code/reference_validator.py` per Constitution Principle II
- [ ] T009b [P] Integrate Reference-Validator Agent gate in CI (`.github/workflows/analysis.yml`) to fail build if citations are unverified per Constitution Principle II

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Depends on T004a, T004b, T005a)
- [ ] T011 [P] [US1] Integration test for missing variable error handling in `tests/integration/test_missing_variable.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) (Depends on T004a, T004b, T005a)
- [ ] T013 [US1] Implement `load_data()` in `code/ingest.py` to read CSV/TSV, handle missing columns, and **halt execution with `sys.exit(1)`** and specific error message (e.g., "Variable 'SWS duration' is missing") per FR-001
- [ ] T014 [US1] Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or <1.5x below 25th) and flag exclusion
- [ ] T014b [US1] Implement data filtering step in `code/ingest.py` to remove flagged outliers from the dataset and output the filtered dataset to `data/processed/filtered_data.parquet`
- [ ] T015 [US1] Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution
- [ ] T016 [US1] Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact (JSON log at `data/results/timing_evidence.json`)** to satisfy SC-004
- [ ] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2)

**Goal**: Compute correlations with automatic method selection (ZINB/Spearman/Pearson) and FDR correction, explicitly framing results as associational.

**Independent Test**: Run analysis on synthetic data with known zero-inflation; verify ZINB selection and correct coefficients. Verify BH-adjusted p-values and associational language in report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [ ] T019 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **Consuming filtered dataset from `data/processed/filtered_data.parquet` (output of T014b)**
- [ ] T021 [US2] Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic: 1) If zeros > 30% OR Shapiro-Wilk p < 0.05 -> **ZINB/Hurdle**, 2) Else if non-normal -> Spearman, 3) Else -> Pearson
- [ ] T022 [US2] Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling
- [ ] T023 [US2] Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [ ] T024 [US2] Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [ ] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05)
- [ ] T026 [US2] Implement report generation in `code/report.py` ensuring all findings are labeled "associational", causal language is prohibited, and **consumes the timing evidence artifact from `data/results/timing_evidence.json` (output of T016)** for the final report
- [ ] T027 [US2] Integrate method selection and correction into `code/main.py` pipeline (Depends on T015)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity, Collinearity Diagnostics, and Power Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds, calculate VIF/collinearity diagnostics, and validate sample size power.

**Independent Test**: Run diagnostics on data with known collinearity; verify VIF calculation and linear dependence flag. Verify power analysis flags "Underpowered" if N < required.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for diagnostics output in `tests/contract/test_diagnostics_schema.py`
- [ ] T029 [P] [US3] Integration test for collinearity detection (perfect multicollinearity) in `tests/integration/test_collinearity.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement sensitivity analysis in `code/diagnostics.py` to re-run significance at p < 0.01, p < 0.05, p < 0.10 and report % change
- [ ] T031 [US3] Implement linear dependence detection in `code/diagnostics.py` via matrix rank check for definitionally related taxa
- [ ] T032 [US3] Implement VIF calculation in `code/diagnostics.py` for multivariate predictors (flag VIF > 5)
- [ ] T033 [US3] Implement power analysis in `code/diagnostics.py` to calculate minimum N for r ≥ 0.3, power ≥ 0.80, α = 0.05
- [ ] T034 [US3] Integrate diagnostics into `code/main.py` and append results to final report
- [ ] T035 [US3] Update `code/report.py` to include "Power Limitation" warnings if N is insufficient

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `README.md`
- [ ] T037 Code cleanup and refactoring
- [ ] T038 Performance optimization across all stories (ensure < 6h runtime)
- [ ] T039 [P] Additional unit tests in `tests/unit/`
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Integration test for missing variable error handling in tests/integration/test_missing_variable.py"

# Launch all models for User Story 1 together:
Task: "Implement validate_variables() in code/ingest.py"
Task: "Implement load_data() in code/ingest.py"
Task: "Implement outlier detection logic in code/ingest.py"
Task: "Implement data filtering step in code/ingest.py"
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

- [P] tasks = different files, no dependencies (except explicit dependencies noted in task description)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence