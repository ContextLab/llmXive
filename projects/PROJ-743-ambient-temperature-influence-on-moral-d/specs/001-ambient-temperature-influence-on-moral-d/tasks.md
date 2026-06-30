# Tasks: Ambient Temperature Influence on Moral Decision Speed

**Input**: Design documents from `/specs/001-ambient-temp-moral-speed/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `tests/`
- [ ] T002 Initialize a Python project with dependencies (pandas, numpy, statsmodels, scikit-learn, requests, pyyaml, seaborn, matplotlib, geopandas) in requirements.txt
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Create base configuration module `code/config.py` defining paths, random seeds, and distance thresholds (default 100km)
- [ ] T005 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`
- [ ] T006 [P] Implement checksum generation and verification for `data/raw/` and `data/processed/` files in `code/utils.py`
- [ ] T007 Create data loading utilities that handle CSV/Parquet ingestion with memory-mapping for large files
- [ ] T008 [P] Setup unit test framework (pytest) with configuration for CPU-only execution and stratified sampling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with NOAA temperature data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`
- [ ] T010 [P] [US1] Integration test for NOAA data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/ingestion.py` to load Moral Machine dataset and filter records with missing location data or impossible response times (<100ms or >10,000ms) (FR-002, FR-010)
- [ ] T012 [US1] Implement NOAA data fetching logic in `code/ingestion.py` using canonical sources: NOAA GHCN-Daily or ERA5-Land (FR-001)
- [ ] T013 [US1] Implement geospatial matching logic in `code/ingestion.py` to link Moral Machine records to nearest NOAA station within 100km threshold, flagging low-confidence matches (FR-009)
- [ ] T014 [US1] Implement time-based interpolation for missing NOAA hourly values in `code/ingestion.py`: apply linear interpolation ONLY if the gap is ≤2 hours; otherwise, use the nearest available hourly reading (Edge Case: Missing Temp)
- [ ] T015 [US1] Create `code/ingestion.py` function to log excluded records with reasons (e.g., "NOAA coverage gap", "Low confidence match") to `data_quality_log` (US-1, FR-002)
- [ ] T016 [US1] Implement output generation to save merged dataset to `data/processed/merged_dataset.parquet` and log success rate (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre-processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for log-transformation and outlier handling in `tests/test_modeling.py`
- [ ] T018 [P] [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/modeling.py` to perform log-transformation of response times and handle non-convergence by switching to GLMM (FR-003)
- [ ] T020 [US2] Implement primary Linear Mixed-Effects Model in `code/modeling.py` with fixed effects: temperature, dilemma complexity, time-of-day, age, gender, dilemma choice; and random intercepts for participant ID and cultural region (FR-003, FR-004, FR-011)
- [ ] T021 [US2] Implement non-linearity test in `code/modeling.py` by adding quadratic term (temperature^2) or spline basis and comparing model fit (FR-013)
- [ ] T022 [US2] Implement likelihood-ratio test in `code/modeling.py` comparing full model vs. null model (without temperature) and record p-value (FR-005, SC-002)
- [ ] T023 [US2] Implement diagnostic plot generation (QQ-plot, residual vs. fitted) in `code/plots.py` and save to `results/figures/` (FR-007, SC-005)
- [ ] T024 [US2] Export model coefficients, standard errors, p-values, and random effect variances to `results/logs/model_results.csv` (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`
- [ ] T026 [P] [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/robustness.py` to calculate alternative temperature metrics (e.g., 3-hour moving average) and re-run modeling (FR-006)
- [ ] T028 [US3] Implement sensitivity analysis in `code/robustness.py` sweeping temperature outlier thresholds (e.g., 2SD, 3SD, 4SD) and reporting coefficient variation (FR-006, SC-003)
- [ ] T029 [US3] Implement indoor/outdoor confound analysis in `code/robustness.py` by stratifying data or applying proxy adjustment; if metadata missing, report limitation and quantify noise impact (FR-012)
- [ ] T030 [US3] Generate comparison table in `code/robustness.py` showing temperature coefficient and p-value for primary vs. alternative models (US-3)
- [ ] T031 [US3] Save all robustness figures (scatter plots, conditional effect plots) to `results/figures/` (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Limitations & Reporting (Priority: P3 - Revision)

**Goal**: Address the absence of baseline data and arousal proxies by documenting them as limitations, as required by the spec's assumptions.

**Independent Test**: Verify that the results log explicitly states the inability to control for baseline speed and arousal due to data absence.

### Implementation for Limitations

- [ ] T041 [US3] Update `code/robustness.py` or `code/plots.py` to generate a final limitations report in `results/logs/limitations.md` explicitly stating: (1) No individual baseline reaction time data exists in the dataset; (2) Arousal/micro-climate effects are unmeasured noise; (3) These factors are not controlled for, only reported (FR-012, Spec Assumptions)

**Checkpoint**: Limitations documented; analysis complete within data constraints.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `quickstart.md` including instructions for running with sampled data
- [ ] T037 Code cleanup and refactoring to ensure modularity
- [ ] T038 Performance optimization: Ensure dataset sampling logic in `code/ingestion.py` prevents memory overflow on 7GB RAM runners
- [ ] T039 [P] Additional unit tests for edge cases (e.g., all records excluded due to distance)
- [ ] T040 Run quickstart.md validation to ensure full pipeline completes within 4 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Limitations (Phase 6)**: Depends on US3 completion (to summarize findings)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires merged data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model output from US2
- **Limitations (Phase 6)**: Requires US3 implementation to summarize findings

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion (US1) before Modeling (US2)
- Modeling (US2) before Robustness (US3)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for location validation and exclusion logic in tests/test_ingestion.py"
Task: "Integration test for NOAA data fetching and merging with sample Moral Machine data in tests/test_ingestion.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/ingestion.py to load Moral Machine dataset..."
Task: "Implement NOAA data fetching logic in code/ingestion.py..."
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
5. Add Limitations (Phase 6) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Ingestion)
   - Developer B: User Story 2 (Modeling)
   - Developer C: User Story 3 (Robustness)
3. Stories complete and integrate independently
4. Developer D (or A/B/C rotation): Limitations (Phase 6) to document constraints

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must be designed to run on 2 CPU cores, ~7 GB RAM. Use stratified sampling if dataset size exceeds memory.
- **NO GPU**: No 8-bit/4-bit quantization, no CUDA dependencies. Use standard precision models.
- **Data Constraints**: Do not attempt to simulate missing data (baseline, arousal). Document limitations instead.