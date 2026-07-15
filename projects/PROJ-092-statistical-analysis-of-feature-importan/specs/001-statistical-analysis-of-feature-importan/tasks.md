# Tasks: Statistical Analysis of Feature Importance Drift in Pre-trained Models

**Input**: Design documents from `/specs/001-feature-importance-drift/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-092-statistical-analysis-of-feature-importan/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup data directory structure (`data/raw`, `data/processed`, `outputs`)
- [X] T005 [P] Implement data download and verification script in `code/download.py` (FR-001)
- [X] T006 [P] Create base configuration and logging infrastructure in `code/utils/`
- [ ] T007 Create data schema definitions in `contracts/` (dataset, drift_metric, importance_profile)
- [ ] T008 [P] Setup pytest environment: create `tests/conftest.py` and verify `pytest --collect-only` returns 0 errors (FR-001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Model Training and Windowed Importance Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest UCI Electricity Load Diagrams dataset, split into 30-day windows, train baseline Random Forest, and compute permutation importance.

**Independent Test**: Verify `code/preprocess.py` generates multiple windows, `code/train_and_importance.py` trains a model with R² > 0.8 on the first window, and `outputs/importance_profiles.csv` is generated with valid scores.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement dataset fetcher in `code/download.py` using `requests` to fetch from UCI archive (FR-001)
- [ ] T010 [US1] Implement preprocessing in `code/preprocess.py`: handle missing values via median imputation and split data into sequential 30-day windows (FR-001, FR-002)
- [ ] T011 [US1] Implement model training in `code/train_and_importance.py`: train `RandomForestRegressor` (n_estimators=100, max_depth=10, seed=42) on first window (FR-003)
- [ ] T012 [US1] Implement R² validation logic in `code/train_and_importance.py`: skip window if R² < 0.8 and log "Model Failure" (FR-003b)
- [X] T012b [US1] **NEW**: Implement stability metric aggregation in `code/utils/stats_aggregator.py`: calculate and report count of successful windows and average R² of valid windows per window (SC-003, FR-003b)
- [X] T013 [US1] Implement permutation importance calculation in `code/train_and_importance.py` using `sklearn.inspection.permutation_importance` (FR-003)
- [X] T014 [US1] Implement window iteration loop in `code/main.py` to process all multiple windows, **integrating the R² < 0.8 skip logic from T012**, **including per-window variance check from T015** to drop zero-variance features per window, **and aggregating stability metrics from T012b** to ensure invalid windows are excluded and metrics are updated per-window, and save `importance_profiles.csv` (FR-003, FR-003b)
- [X] T015 [US1] Add error handling for feature variance in `code/preprocess.py`: implement `variance_check()` function returning dropped_features list; add unit test confirming zero-variance feature is dropped per window (FR-001, Spec Edge Cases) <!-- SKIPPED: non-mapping output -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Drift Quantification via Rank Correlation (Priority: P2)

**Goal**: Calculate Spearman rank correlation between consecutive windows and identify drift magnitude.

**Independent Test**: Execute `code/drift_analysis.py` on `importance_profiles.csv` and verify `outputs/drift_metrics.csv` contains Spearman rho values within the standard theoretical range for adjacent windows.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement Spearman correlation calculator in `code/drift_analysis.py` (FR-004)
- [~] T017 [US2] Implement pairwise drift calculation logic to compare Window T vs Window T+1 (FR-004)
- [~] T019 [US2] Implement writer function in `code/drift_analysis.py` that appends (window_t, window_t+1, rho, p_value) to `outputs/drift_metrics.csv`, ensuring the p-value column is included from the null baseline comparison (FR-006)
- [ ] T020 [US2] Implement Null Model Baseline: shuffle chronological order of time windows (FR-007), re-calculate importance rankings, **calculate mean rho of multiple shuffled runs**, and generate `outputs/null_baseline.json` (FR-007, SC-004). **Note: Implementation follows Spec FR-007 (window shuffling); plan.md vector-permutation is an alternative methodology not implemented in this scope.**
- [X] T023 [US2] Implement block permutation significance test (with a sufficient number of resamples) in `code/significance_test.py` to return p-value for the correlation sequence (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, including Null Model Baseline and p-value calculation

---

## Phase 5: User Story 3 - Statistical Significance Testing and Trend Detection (Priority: P3)

**Goal**: Apply Mann-Kendall trend test and block permutation significance test to validate drift trends.

**Independent Test**: Run `code/significance_test.py` on the correlation sequence; verify it returns a Kendall's Tau statistic and a block permutation p-value, correctly handling small sample sizes (n=5-6).

### Implementation for User Story 3

- [X] T021 [P] [US3] Implement Mann-Kendall trend test in `code/significance_test.py` to return Kendall's Tau (FR-005)
- [~] T022 [US3] Implement trend direction logic: report "monotonic decrease" if Tau < 0 (FR-005)
- [~] T018 [US3] Implement "high drift" flagging logic in `code/drift_analysis.py`: **read `outputs/null_baseline.json` (from T020) and p-value (from T023)**, flag transitions ONLY if the block permutation p-value < 0.05 (FR-004b)
- [~] T024 [US3] Add logic to handle small sample size constraints (n < 10) and rely on permutation p-values (FR-008)
- [ ] T025 [US3] Integrate all metrics (Spearman rho, Kendall tau, p-value) into final `outputs/drift_metrics.csv` (FR-006)
- [X] T026a [US3] Implement aggregation logic in `code/main.py` to **compute global stats from `drift_metrics.csv` and stability metrics from T012b** for robustness measurement (SC-003, FR-006)
- [ ] T026b [US3] Implement final report generation in `outputs/global_stats.json` to serialize aggregated stats with keys: `mean_rho`, `trend_direction`, `p_value`, `stable_window_count` (SC-003, FR-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T027 [P] Documentation updates in `docs/` and `README.md`
- [~] T028 Code cleanup and refactoring for memory efficiency (ensure < 4GB RAM usage) <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [~] T029 Performance optimization for window processing loop
- [~] T030 [P] Additional unit tests in `tests/unit/` for edge cases (missing data, model failure)
- [~] T031 Security hardening for data handling <!-- ATOMIZE: requested -->
- [~] T032 Run quickstart.md validation and verify end-to-end pipeline execution <!-- ATOMIZE: requested -->

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
- **User Story 2 (P2)**: Depends on US1 completion (needs `importance_profiles.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs drift metrics sequence and null baseline)

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
# Launch all models for User Story 1 together:
Task: "Implement dataset fetcher in code/download.py"
Task: "Implement preprocessing in code/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify R² > 0.8 and CSV output)
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
 - Developer A: User Story 1 (Data & Model)
 - Developer B: User Story 2 (Drift Analysis)
 - Developer C: User Story 3 (Statistical Significance)
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
- **Constraint Reminder**: All tasks must run on CPU-only CI with limited cores and memory, without GPU acceleration. No 8-bit quantization or deep learning models allowed.