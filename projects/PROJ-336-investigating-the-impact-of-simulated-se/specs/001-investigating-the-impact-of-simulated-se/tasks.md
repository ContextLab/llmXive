# Tasks: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

**Input**: Design documents from `/specs/001-sensory-deprivation-network-dynamics/`
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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `results/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (nibabel, numpy, pandas, networkx, scikit-learn, scipy, matplotlib, seaborn, bids-validator, requests, fsl-afni-wrappers)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `src/config.py` to define paths, thresholds (FD > 0.5mm), and dataset IDs (ds001770, ds003820)
- [ ] T005 [P] Implement `src/utils/atlas.py` to download and cache Schaefer/AAL atlas (-400 ROIs) from GitHub with version pinning
- [ ] T006 [P] Implement `src/data/quality_check.py` to compute Framewise Displacement (FD) from JSON sidecars, exclude subjects with >10% high-motion volumes, **log the exclusion count**, and **halt with an error if the remaining sample size drops below n ≥ 20 **. This task produces an **exclusion manifest** that is a blocking dependency for T011/T012.
- [ ] T007 [P] Create `main.py` orchestration script with checkpointing logic that saves state at each subject completion and supports resumption from last completed stage on timeout/disk overflow
- [ ] T008 [P] Implement disk quota enforcement logic (compress intermediates, checkpointing) in `main.py` — **raw NIfTI files must be preserved for reproducibility**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Acquire and preprocess resting-state fMRI data with deprivation conditions (Priority: P1) 🎯 MVP

**Goal**: Download, validate, and preprocess fMRI data from OpenNeuro ds001770 (or fallback ds003820), ensuring pre/post deprivation labels exist and motion artifacts are handled.

**Independent Test**: Can be fully tested by successfully downloading a sample dataset (e.g., 1 subject's pre/post scans), preprocessing it through the motion correction and normalization pipeline, and outputting clean BOLD time series files that pass quality checks.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for dataset label validation in `tests/unit/test_download.py` (verifies 'task-rest' + deprivation labels)
- [ ] T010 [P] [US1] Unit test for FD calculation in `tests/unit/test_quality_check.py` (verifies FD > 0.5mm threshold logic)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `src/data/download.py` to fetch ds001770/ds003820 from OpenNeuro, verify BIDS structure, and halt if labels missing
- [ ] T012 [US1] Implement `src/data/preprocess.py` for CPU-compatible pipeline: motion correction, normalization, bandpass filtering (low-frequency range) **using version-locked FSL or AFNI pipelines only** (no nilearn fallback) to ensure Neuroimaging Preprocessing Integrity.
- [ ] T013 [US1] Implement `src/data/preprocess.py` logic to output preprocessed BOLD time series files — **raw NIfTI files must be preserved unchanged** for reproducibility (Constitution Principle III).
- [ ] T014a [US1] Implement specific validation in `src/data/download.py` to **raise ValueError if BIDS structure is invalid** with a specific error message directing to verify dataset availability.
- [ ] T014b [US1] Implement specific validation in `src/data/download.py` to **raise ValueError if motion covariates are missing** with a specific error message directing to verify dataset metadata.
- [ ] T015 [US1] Add logging for user story 1 operations (download stats, exclusion counts, preprocessing times)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute functional connectivity and network topology metrics (Priority: P2)

**Goal**: Calculate functional connectivity matrices and network metrics (modularity, global efficiency, node strength) from preprocessed fMRI data using CPU-tractable algorithms.

**Independent Test**: Can be fully tested by running the metric computation pipeline on a single subject's pre- and post-deprivation scans and producing numerical outputs for modularity, global efficiency, and node strength that are reproducible across runs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for correlation matrix symmetry in `tests/unit/test_connectivity.py`
- [ ] T017 [P] [US2] Unit test for network metric calculation (modularity, efficiency) in `tests/unit/test_metrics.py` using a small dummy graph

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `src/analysis/connectivity.py` to compute Pearson correlation matrices from BOLD time series for each ROI pair (hundreds of ROIs)
- [ ] T019 [US2] Implement `src/analysis/metrics.py` to calculate modularity using Louvain algorithm (networkx/brain connectivity toolbox CPU version)
- [ ] T020 [US2] Implement `src/analysis/metrics.py` to calculate global efficiency using networkx and node strength for each subject/condition
- [ ] T021 [US2] Integrate with User Story 1 components: load preprocessed BOLD data and atlas ROIs, output `.npy` matrices and `results/metrics.csv`
- [ ] T022 [US2] Ensure all metric outputs are stored with documented precision (≥ 4 decimal places) and compressed formats
- [ ] T023 [US2] Implement `src/analysis/aggregate.py` to load individual subject metrics, pair pre/post conditions, and output `results/paired_metrics.csv` for statistical testing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform statistical comparison and generate visualizations (Priority: P3)

**Goal**: Compare network metrics between pre-deprivation and post-deprivation conditions using paired t-tests with FDR correction and permutation testing, and generate visualizations.

**Independent Test**: Can be fully tested by running the statistical analysis on the computed metrics and producing p-values (FDR-corrected), effect sizes (Cohen's d), and visualization files (degree plots, edge weight heatmaps) that confirm the analysis completed successfully.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_stats.py`
- [ ] T025 [P] [US3] Integration test for full statistical pipeline (paired t-test + permutation) in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `src/analysis/stats.py` to perform paired t-tests on pre/post metrics with FDR correction (scipy.stats)
- [ ] T027 [US3] Implement `src/analysis/stats.py` to run permutation testing (≥1,000 iterations, sign-flip strategy) for empirical p-values
- [ ] T028 [US3] Implement `src/analysis/stats.py` to compute effect sizes (Cohen's d) and perform sensitivity analysis sweeps for **motion, effect, and p-value/FDR thresholds** as required by SC-005.
- [ ] T029 [US3] Implement `src/viz/plot_networks.py` to generate degree distribution plots and edge weight heatmaps showing pre/post differences
- [ ] T030 [US3] Implement `src/viz/plot_metrics.py` to visualize pre/post comparisons and statistical significance
- [ ] T031 [US3] Generate final `results/stats.csv` with all p-values, effect sizes, and permutation results

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and mandatory reporting artifacts

- [ ] T032 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T033 [P] Generate `results/statistical_framing.md` documenting inference type (associational/causal) based on dataset randomization status per SC-002: **check dataset metadata for randomization flags; if absent, default to 'associational'**.
- [ ] T034 [P] Generate `results/sensitivity_report.md` documenting metric significance across motion/effect/p-value thresholds per SC-005: **include one-line rationale for each cutoff and sensitivity analysis sweeping the p-value/FDR parameter**.
- [ ] T035 [P] Generate `results/power_analysis.md` documenting sample size (n≥20) and power limitations per SC-004: **document the method used for power consideration and acknowledge any power limitations**.
- [ ] T036 [P] Code cleanup and refactoring for memory efficiency (ensure <7GB RAM usage)
- [ ] T037 [P] Performance optimization: parallelize subject processing where possible (within 6h limit)
- [ ] T038 [P] Additional unit tests for edge cases (missing data, empty subjects list) in `tests/unit/`
- [ ] T039 [P] Run `quickstart.md` validation to ensure reproducibility on fresh environment

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (preprocessed BOLD)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data output (paired_metrics.csv from T023)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel IF data dependencies are mocked or handled by a stub
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with data dependency awareness)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for dataset label validation in tests/unit/test_download.py"
Task: "Unit test for FD calculation in tests/unit/test_quality_check.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py"
Task: "Implement src/data/quality_check.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Acquisition & Preprocessing)
4. **STOP and VALIDATE**: Test US1 independently with a sample subject
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Metrics - can use mock data initially)
 - Developer C: User Story 3 (Stats - can use mock data initially)
3. Stories complete and integrate independently once real data flows through US1

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST be CPU-tractable (no GPU/CUDA, <7GB RAM, <6h runtime).
- **Critical Constraint**: No fake data generation; all analysis must use real downloaded datasets (ds001770/ds003820).
- **Critical Constraint**: Raw data must be preserved unchanged for reproducibility (Constitution Principle III).
- **Critical Constraint**: Preprocessing must use version-locked FSL/AFNI pipelines (Constitution Principle VI).