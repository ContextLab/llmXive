# Tasks: Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys

**Input**: Design documents from `/specs/001-evaluating-imputation-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

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

- [ ] T001 Create project structure per implementation plan (code/, data/raw, data/processed, tests/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (pandas, numpy, scipy, scikit-learn, statsmodels, pyyaml, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/data_ingestion.py` with canonical HuggingFace URL fetcher for GSS/ACS data
- [ ] T005 [P] Implement `code/synthetic_generator.py` to create datasets with known ground-truth parameters and controlled missingness (MCAR/MAR)
- [ ] T006 Create base data contracts in `specs/contracts/` (dataset.schema.yaml, imputation_result.schema.yaml)
- [ ] T007 Implement `code/update_state.py` to generate content hashes for artifacts and update state YAML (Constitution Principle V)
- [ ] T008 [P] Implement `code/config.py` SeedManager utility to derive distinct per-chain seeds from a base seed (e.g., base_seed + chain_id) to ensure reproducible convergence diagnostics for MICE, ensuring 4 distinct chains do not initialize identically. **Must explicitly implement logic to generate 4 unique seeds for downstream MICE runs.**
- [ ] T009 Implement design-based variance estimation utility in `code/variance_estimator.py` (Taylor series linearization, no i.i.d. fallback)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Pipeline & Baseline Variance Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest a complex survey dataset, apply complete-case analysis, and calculate baseline variance estimates using design weights.

**Independent Test**: Run pipeline on a small, known subset of GSS data; verify mean and variance match GSS documentation or manual `survey` package logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_data_ingestion.py`
- [ ] T011 [P] [US1] Integration test for complete-case variance calculation in `tests/integration/test_baseline_variance.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement GSS/ACS data loading in `code/data_ingestion.py` handling weights, strata, and PSU
- [ ] T013 [US1] Implement missingness detection and variable filtering (skip >30% missing, log warning) in `code/data_ingestion.py`
- [ ] T014 [US1] Implement Complete-Case analysis logic in `code/imputation_pipeline.py`
- [ ] T015 [US1] Implement design-based variance calculation (Taylor series) for complete-case data in `code/variance_estimator.py`
- [ ] T016 [US1] Output JSON summary with status "success" for US1 in `data/processed/baseline_results.json`
- [ ] T017 [US1] Add robust error handling for small cluster sizes (PSU=1) with warning and exclusion logic

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Validation & Imputation Method Implementation (Priority: P2)

**Goal**: Validate imputation methods using synthetic data (known ground truth) and apply to real-world datasets for relative efficiency comparison.

**Independent Test**: Run synthetic generator, apply MICE (m=5) and Single Mean Imputation; verify MICE variance estimates are closer to true variance than Single Imputation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for synthetic data generation in `tests/contract/test_synthetic_generator.py`
- [ ] T019 [P] [US2] Integration test for MICE convergence and bias calculation in `tests/integration/test_imputation_validation.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement Single Mean Imputation as a reusable function in `code/imputation_pipeline.py`
- [ ] T021 [US2] Implement MICE pipeline in `code/imputation_pipeline.py` as a reusable function that: (1) **Explicitly runs 4 independent instances** of `sklearn.IterativeImputer` with `max_iter=1000` each, deriving distinct seeds from T008 for each instance to ensure chain divergence; (2) **Discards the first 500 iterations** of each run as burn-in; (3) **Handles binary outcomes** using Predictive Mean Matching (PMM) with `estimator=RandomForestRegressor` and `random_state` derived from T008; (4) **Enforces R-hat < 1.05 convergence** for binary chains, **retrying up to 3 times** with new seeds before aborting the variable; (5) Returns the pooled variance estimate from the final 500 iterations. **This task must explicitly satisfy FR-002's 4-chain/1000-iter/500-burn-in requirement via independent runs.**
- [ ] T022 [US2] Implement convergence check (R-hat < 1.05) and retry logic (max 3 attempts) for MICE in `code/imputation_pipeline.py` (Integrated into T021)
- [ ] T023 [US2] Implement bias calculation in `code/analysis.py` that: (1) Consumes output artifacts from T005 (synthetic ground truth), T020 (Single Mean), and T021 (MICE); (2) Validates the artifact schema; (3) Calculates percentage bias; (4) **Computes the ratio (|MICE_bias| / |Single_bias|)**; (5) **Asserts that MICE bias magnitude is <= 80% of Single Imputation bias magnitude** in synthetic MAR scenarios, flagging the result as pass/fail against SC-002.
- [ ] T024 [US2] Implement relative efficiency calculation against Jackknife/BRR benchmark for real data in `code/analysis.py`
- [ ] T025 [US2] Generate comparison table (percentage bias) for synthetic and real datasets in `data/processed/imputation_comparison.json`
- [ ] T026 [US2] **REMOVED**: Merged into T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis & Methodological Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on imputation thresholds and generate a report with multiplicity corrections and associational framing.

**Independent Test**: Verify report contains "Multiplicity Correction" section and "Sensitivity Analysis" table varying a parameter (e.g., m or iterations).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`
- [ ] T028 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement Bonferroni correction for p-values in paired t-tests in `code/analysis.py`
- [ ] T030 [US3] Implement sensitivity analysis sweep in `code/analysis.py` that: (1) Orchestrates a loop over the reusable functions defined in T020 and T021; (2) **Sweeps the parameter `m` (number of imputations) over the concrete set {5, 10, 20}**; (3) **Reports the variation in variance bias rate** for each value in the set.
- [ ] T031 [US3] Generate final report in `data/processed/final_report.md` that: (1) **Explicitly inserts the phrase "associational"** to label all findings; (2) **Strictly avoids causal language**; (3) Satisfies FR-006.
- [ ] T032 [US3] Include "Multiplicity Correction" and "Sensitivity Analysis" sections in final report
- [ ] T033 [US3] Verify all statistical tests use design-based estimators, not i.i.d. assumptions

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `docs/`
- [ ] T035 Code cleanup and refactoring in `code/`
- [ ] T036 Performance optimization to ensure runtime < 6 hours on CPU-only runner
- [ ] T037 [P] Additional unit tests in `tests/unit/` for edge cases (MNAR handling, PSU=1 detection)
- [ ] T038 Run quickstart.md validation
- [ ] T039 Final verification of all JSON outputs against contract schemas

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
Task: "Contract test for data ingestion schema in tests/contract/test_data_ingestion.py"
Task: "Integration test for complete-case variance calculation in tests/integration/test_baseline_variance.py"

# Launch all models for User Story 1 together:
Task: "Implement GSS/ACS data loading in code/data_ingestion.py"
Task: "Implement missingness detection and variable filtering in code/data_ingestion.py"
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