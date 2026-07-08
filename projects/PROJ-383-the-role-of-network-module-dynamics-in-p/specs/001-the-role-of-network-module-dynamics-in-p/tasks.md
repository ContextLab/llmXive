# Tasks: Network Module Dynamics in Predicting Working Memory

**Input**: Design documents from `/specs/001-the-role-of-network-module-dynamics-in-p/`
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

- [X] T001a [P] Create root project directories: `code/`, `data/`, `tests/`
- [X] T001b [P] Initialize Python 3.11 project with dependencies (`numpy`, `pandas`, `scikit-learn`, `networkx`, `leidenalg`, `nilearn`, `psutil`, `openneuro-py`, `scipy`, `pytest`) in `code/requirements.txt`
- [X] T001c [P] Create `.gitignore` and configure linting (flake8/pylint) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup memory monitoring utility `code/utils/memory_monitor.py` using `psutil` to track peak RSS and enforce ≤7GB limit
- [X] T005 [P] Create configuration module `code/utils/config.py` with pinned random seeds (numpy, random, networkx, leidenalg) and window length parameters {60, 90, and additional intermediate values} [UNRESOLVED-CLAIM: c_8d975114 — status=not_enough_info]
- [X] T006 [P] Initialize specific subdirectory structure (`data/raw_fmri`, `data/raw_behavior`, `data/processed`, `data/results`) and create checksum validation scripts. **Depends on T001a**.
- [ ] T007 [P] Implement dataset ingestion validator `code/ingestion/validate_source.py` to verify OpenNeuro **ds** availability and abort on mismatch. **Note: Validates ds001734 as per plan.md; spec.md ds000224 reference is a known contradiction [UNRESOLVED-CLAIM: c_c9bda30b — status=not_enough_info] flagged for kickback.**
- [X] T008 Setup logging infrastructure to record subject exclusions and memory usage events
- [X] T037 [P] Create `code/preprocessing/fmriprep.conf` configuration file and `code/preprocessing/README.md` justification to satisfy Constitution Principle VI
- [X] T038 [P] Implement `code/ingestion/validate_columns.py` to verify presence of motion parameters and FD estimates in the dataset before ingestion

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess a subset of resting-state fMRI data and behavioral scores from HCP (ds001734) ensuring memory constraints are met.

**Independent Test**: The script successfully downloads a sample of subjects, loads preprocessed fMRI time series and 2-back accuracy scores, and outputs a consolidated Parquet file without exceeding 7GB RAM. [UNRESOLVED-CLAIM: c_67ea39af — status=not_enough_info]

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for memory limit enforcement in `tests/unit/test_memory_monitor.py`
- [ ] T010 [P] [US1] Integration test for data download and exclusion logic in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/ingestion/download_hcp.py` to fetch rs-fMRI and n-back data for 100 subjects from OpenNeuro **ds001734**
- [X] T012a [US1] Implement subject exclusion logic in `code/ingestion/preprocess.py`: exclude subjects with mean FD > 0.2mm [UNRESOLVED-CLAIM: c_ec7a957b — status=not_enough_info]
- [~] T012b [US1] Implement motion scrubbing and regression in `code/ingestion/preprocess.py`: Regress out rigid-body motion parameters, their temporal derivatives, and mean FD using OLS; scrub time points with FD > 0.2mm [UNRESOLVED-CLAIM: c_8c909c97 — status=not_enough_info]; **output scrubbed time series to `data/processed/scrubbed_timeseries.parquet`**
- [~] T013 [US1] Implement data consolidation logic to merge cleaned time series and behavioral scores into `data/processed/consolidated_data.parquet`
- [~] T014 [US1] Add logging for subject exclusions due to missing behavioral scores or excessive motion
- [~] T015 [US1] Integrate `psutil` peak RSS checks into the ingestion pipeline to verify ≤7GB constraint (FR-010)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Flexibility Metric Computation (Priority: P2)

**Goal**: Compute the "temporal flexibility" metric for each subject using **Multilayer Modularity Optimization (MMO)** with `leidenalg` to satisfy CPU constraints.

**Independent Test**: The pipeline processes loaded time series, applies sliding window (fixed duration, fixed step) and MMO, and outputs a single flexibility score per subject within a normalized range.

### Tests for User Story 2

- [~] T016 [P] [US2] Unit test for sliding window generation and window length validation
- [~] T017 [P] [US2] Unit test for flexibility score calculation (range check [0,1] and NaN check)

### Implementation for User Story 2

- [~] T018 [P] [US2] Implement `code/analysis/dynamic_connectivity.py` to compute time-varying functional connectivity matrices using sliding windows (primary duration, step size)
- [~] T019 [US2] Implement **Multilayer Modularity Optimization (MMO)** using `leidenalg` (resolution sufficient for the analysis, 100 iterations [UNRESOLVED-CLAIM: c_c9494970 — status=not_enough_info]) on **`data/processed/scrubbed_timeseries.parquet`** to identify network modules; calculate flexibility metric as probability of node switching (FR-003, FR-004) <!-- ATOMIZE: requested -->
- [~] T020 [US2] Handle edge cases: skip subjects if window size leaves insufficient time points; flag errors instead of crashing
- [~] T021 [US2] Output flexibility scores to `data/processed/flexibility_scores.parquet`
- [~] T022 [US2] Implement sensitivity analysis runner: repeat process for a range of window lengths, **calculate max absolute difference between p-values, assert < 0.05 [UNRESOLVED-CLAIM: c_bcdca9b7 — status=not_enough_info]**, and write results to `data/results/sensitivity_analysis.json` (FR-009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform partial Spearman correlation, permutation test, and sensitivity analysis to determine the association between flexibility and working memory.

**Independent Test**: The analysis script outputs a partial correlation coefficient, corrected p-value (A large number of permutations), and a report confirming associational nature, motion control, and sensitivity analysis results.

### Tests for User Story 3

- [~] T023 [P] [US3] Unit test for partial Spearman correlation with motion control
- [~] T024 [P] [US3] Unit test for permutation test logic (1,000 permutations [UNRESOLVED-CLAIM: c_dd905ff4 — status=not_enough_info], p-value correction)

### Implementation for User Story 3

- [~] T025 [P] [US3] Implement `code/analysis/statistics.py` for partial Spearman correlation controlling for mean FD (FR-005)
- [~] T026 [US3] Implement non-parametric permutation test with standard p-value correction for discrete sampling (FR-006)
- [~] T027 [US3] Implement sensitivity analysis logic to compare p-values across window lengths (30s, 60s, 90s) [UNRESOLVED-CLAIM: c_4ef0f77c — status=not_enough_info] and verify stability (max diff < 0.05 [UNRESOLVED-CLAIM: c_425405c9 — status=not_enough_info]) (FR-009)
- [~] T028 [US3] Implement `code/results/generate_report.py` to generate final statistics, **including sensitivity analysis results from `data/results/sensitivity_analysis.json`**, ensuring all findings are framed as "**associational**" (exact string) and confirming motion control was applied (FR-007, FR-009)
- [~] T029 [US3] Generate visualizations: histogram of null distribution and sensitivity analysis plot using `matplotlib`, saving to `data/results/plots/null_dist.png` and `data/results/plots/sensitivity_plot.png`
- [~] T030 [US3] Save final results to `data/results/statistical_report.json` and `data/results/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031 [P] Documentation updates in `docs/` including quickstart and API references
- [~] T032 Code cleanup and refactoring for memory efficiency <!-- ATOMIZE: requested -->
- [~] T033 Run full integration test suite to verify end-to-end pipeline
- [ ] T034 [P] Add contract tests to verify data schema compliance
- [ ] T035 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for flexibility scores

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for memory limit enforcement in tests/unit/test_memory_monitor.py"
Task: "Integration test for data download and exclusion logic in tests/integration/test_ingestion.py"

# Launch implementation tasks:
Task: "Implement code/ingestion/download_hcp.py to fetch rs-fMRI and 2-back data"
Task: "Implement code/ingestion/preprocess.py for motion scrubbing"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Flexibility Metric)
 - Developer C: User Story 3 (Statistics)
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
- **Dataset Note**: Tasks implement `ds001734` per `plan.md`. `spec.md` references `ds000224`; this is a known contradiction requiring `spec.md` update.