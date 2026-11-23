# Tasks: The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

**Input**: Design documents from `/specs/001-the-influence-of-network-topology-on-neu/`
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

- [ ] T001 Create project structure per implementation plan: `mkdir -p projects/PROJ-358-the-influence-of-network-topology-on-neu/{code/data,code/analysis,tests/unit,tests/integration,data/raw,data/processed,docs,contracts}`
- [ ] T002 Initialize Python 3.11 project: Create `projects/PROJ-358-the-influence-of-network-topology-on-neu/code/requirements.txt` containing pinned versions of `numpy`, `scipy`, `pandas`, `nibabel`, `networkx`, `nilearn`, `requests`, `tqdm`, `pytest`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup directory structure for `data/raw`, `data/processed`, `code/data`, `code/analysis`, `tests/`
- [X] T005 [P] Create `code/__init__.py` and `tests/__init__.py`
- [X] T006 [P] Implement basic logging infrastructure in `code/utils/logger.py`
- [X] T007 Create base configuration management in `code/config.py` with keys: `OPENNEURO_ID` (ds000246), `N_SUBJECTS` (30), `FD_THRESHOLD` (0.5), `MNI_TEMPLATE` (MNI152NLin2009cAsym), `THRESHOLD_DEFAULT` (0.20).
- [X] T008 Setup error handling utilities for network retries in `code/utils/retry.py`
- [ ] T009 [P] Create `docs/spec_amendment_001.md` documenting the deviation from Spec FR-001 (HCP N=100 -> OpenNeuro N=30). **DEP**: Requires completion of T009a, T009b, T009c. <!-- FAILED: unspecified -->
- [ ] T009a [P] Update `spec.md` FR-001 to explicitly state: "System MUST download resting-state and task-based fMRI data for exactly N=30 subjects from OpenNeuro ds000246, ensuring total data size fits within 2 GB disk space. [UNRESOLVED-CLAIM: c_d46f5af7 — status=not_enough_info] "
- [ ] T009b [P] Update `spec.md` SC-004 to explicitly state: "{{claim:c_2e38bc66}}"
- [ ] T009c [P] Update `spec.md` SC-005 to explicitly state: "The memory usage of the preprocessing and calculation steps must not exceed a standard operational threshold at any point, measured as peak Resident Set Size (RSS) via /proc/self/status. [UNRESOLVED-CLAIM: c_ea8d83d3 — status=not_enough_info] "

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download N=30 subjects from OpenNeuro ds000246 (per approved spec amendment T009a-c), preprocess (motion correction, MNI normalization, filtering, nuisance regression), and parcellate into a multi-region time-series.

**Independent Test**: Run pipeline on a single subject; verify output is a cleaned 4D NIfTI (or processed time-series CSV) with motion parameters < 0.5mm and memory usage < 6.5 GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for data download logic in `tests/unit/test_download.py` (mock OpenNeuro API)
- [ ] T011 [P] [US1] Integration test for full preprocessing flow on 1 subject in `tests/integration/test_preprocess_flow.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py`: Fetch OpenNeuro ds000246 data for N=30 subjects using `nilearn.datasets.fetch_openneuro` combined with manual chunked downloading via `requests` (stream=True) for large files. Implement exponential backoff for 429 errors. **FAIL LOUDLY** if real data fetch fails (no synthetic fallback). **DEP**: Executes the approved deviation from FR-001 as documented in T009a.
- [ ] T013 [US1] Implement `code/data/preprocess.py`: Motion correction, spatial normalization to MNI space using `nilearn.image.resample_to_img` with `MNI152NLin2009cAsym` template (explicitly defined as the canonical MNI space for FR-002), temporal low-pass filtering, and nuisance regression (motion, CSF, WM).
- [ ] T014 [US1] Implement parcellation logic in `code/data/preprocess.py`: Fetch `Schaefer_200Parcels_7Networks` atlas using `nilearn.datasets.fetch_atlas_schaefer_2018` if not present, and apply it to extract time-series matrices (200 regions x timepoints).
- [ ] T015 [US1] Implement subject exclusion logic: Calculate Frame Displacement (FD) using `sum of absolute derivatives of the 6 rigid-body motion parameters` via `nilearn.image.compute_motion_parameters`; exclude subjects with FD > 0.5mm and log reasons.
- [ ] T016 [US1] Create `code/main.py` orchestration script to run download -> preprocess -> save to `data/processed/`. **THIS IS A GATE TASK**: Phase 4/5 cannot begin until T016 completes.
- [ ] T017a [US1] Implement hard memory guard in `code/utils/memory_guard.py` which raises `MemoryError` if RSS > 6.5 GB during execution and logs peak RSS to stderr for verification. **DEP**: Replaces T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Metric and Synchrony Calculation (Priority: P2)

**Goal**: Compute resting-state graph metrics (clustering, path length, efficiency, modularity) and task-based synchrony (Mean FC) for the preprocessed data.

**Independent Test**: Run on subjects; verify output CSV has no NaNs, values within theoretical bounds (efficiency [0,1]), and completes within 2 hours.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for graph metric calculation in `tests/unit/test_graph_metrics.py` (verify bounds and connectivity)
- [ ] T018a [P] [US2] Add unit test `tests/unit/test_graph_metrics.py::test_efficiency_bounds` to explicitly verify theoretical bounds.
- [ ] T019 [P] [US2] Unit test for synchrony calculation in `tests/unit/test_synchrony.py` (verify correlation logic)

### Implementation for User Story 2

- [ ] T020a [US2] Document default threshold (0.20) in `code/config.py` and `data-model.md` to explicitly separate it from the sensitivity sweep range.
- [ ] T020 [US2] Implement `code/analysis/graph_metrics.py`: Calculate clustering coefficient, characteristic path length, global efficiency, and modularity using `networkx` on proportional threshold (default configurable percentage). Handle disconnected graphs by logging warnings. **DEP**: Requires T020a completion.
- [ ] T021 [US2] Implement `code/analysis/synchrony.py`: Calculate Mean Functional Connectivity (Pearson correlation) for frontoparietal and default mode networks during working memory epochs. **DEP**: Requires T016 execution, T014 (Parcellation), and T012-T015 completion. Isolate epochs by parsing `events.tsv` files for `trial_type` column values '2back' and '0back'.
- [ ] T023 [US2] Save metrics to `data/processed/graph_metrics.csv` and `data/processed/synchrony_metrics.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Association and Sensitivity Analysis (Priority: P3)

**Goal**: Perform Pearson correlations between topology and synchrony, apply FDR correction, and run sensitivity analysis on thresholds {0.10, 0.20, 0.30}.

**Independent Test**: Run on generated metrics; verify output includes r, p, q-values (FDR), and sensitivity report showing r variation across thresholds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for FDR correction in `tests/unit/test_stats.py` (verify q-value calculation)
- [ ] T025 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_sensitivity.py`
- [ ] T025a [P] [US3] Add integration test `tests/integration/test_sensitivity.py::test_variation_output` to explicitly verify the variation metric output.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis/stats.py`: Perform Pearson correlation between resting-state metrics and task synchrony using `scipy.stats.pearsonr` with `nan_policy='omit'`. Frame results strictly as associational. **DEP**: Requires T023 and T021 completion.
- [ ] T027 [US3] Implement FDR correction (Benjamini-Hochberg) for the family of tests (metrics x networks) in `code/analysis/stats.py`.
- [ ] T028 [US3] Implement sensitivity analysis: Re-execute the logic of T020 (graph metric calculation) with proportional thresholds explicitly set to the set {0.10, 0.20, 0.30}. Calculate correlation coefficients, significance status, and variation (standard deviation and range) for each sweep point. Output to `data/processed/sensitivity_report.json`. **DEP**: Requires T020 logic, T023, and T021 completion.
- [ ] T029 [US3] Generate final results report in `data/processed/results_summary.csv` and `data/processed/sensitivity_report.json` including the calculated variation metrics.
- [ ] T030 [US3] Create visualization script in `code/analysis/plot_results.py` to generate `data/processed/fig_correlation.png` (Seaborn scatterplot with regression line) and `data/processed/fig_sensitivity.pdf` (sensitivity chart).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates: Update `quickstart.md` with run instructions for OpenNeuro dataset.
- [ ] T032 Code cleanup: Ensure all imports are explicit and dependencies are pinned in `requirements.txt`.
- [ ] T032a [P] Generate `methodology.yaml` documenting graph library versions and parameter settings (thresholding logic, connectivity matrix construction details) to satisfy Constitution Principle VII.
- [ ] T033 Performance optimization: Profile `code/analysis/graph_metrics.py` to ensure CPU vectorization is effective. **Metric**: Reduce runtime compared to loop-based version. **Output**: `data/processed/profile_report.txt`.
- [ ] T034 Run `pytest` on full suite to verify end-to-end pipeline integrity. **DEP**: Requires T016 execution, T023, and T029 completion. (NOT Parallel)
- [ ] T035 Validate `quickstart.md` instructions against a fresh clone.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **DEP**: Requires successful execution of US1 pipeline (T012-T015) and T016 completion first.
 - **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **DEP**: Requires T023 (graph metrics) and T021 (synchrony metrics) to complete first.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
Task: "Unit test for data download logic in tests/unit/test_download.py"
Task: "Integration test for full preprocessing flow on 1 subject in tests/integration/test_preprocess_flow.py"

# Launch implementation tasks for User Story 1 together (where independent):
Task: "Implement code/data/download.py"
Task: "Implement code/data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data download and preprocessing on 1 subject).
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Metrics Calculation) - *Can start once T016 completes*
 - Developer C: User Story 3 (Statistics) - *Can start once T023/T021 complete*
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
- **Data Integrity**: All data loading tasks MUST fail loudly on real data fetch errors; no synthetic fallbacks allowed.
- **Dataset**: Use OpenNeuro ds000246 (N=30) as per approved spec amendment (T009a-c).
- **Normalization**: Uses `nilearn.image.resample_to_img` with `MNI152NLin2009cAsym` template (canonical MNI space).
- **Memory Guard**: Hard limit of 6.5 GB enforced by T017a.
- **Variation Metric**: Sensitivity analysis (T028) must output variation (std/range) for thresholds {0.10, 0.20, 0.30}.
- **Methodology**: `methodology.yaml` generated by T032a.