# Tasks: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Input**: Design documents from `/specs/001-neural-correlates-social-exclusion/`
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

- [ ] T001 Create directory structure: `data/raw`, `data/processed`, `data/results`, `src`, `tests`
- [ ] T002 Create `src/__init__.py` and `tests/__init__.py` to initialize Python packages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (numpy, pandas, scipy, scikit-learn, nibabel, nilearn, pyyaml, requests, matplotlib, pytest)
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`
- [ ] T005 [P] Implement `config.yaml` with paths, motion threshold (a defined value), atlas names, and simulation parameters
- [ ] T006 [P] Create base utility modules for logging and error handling (`src/utils.py`)
- [ ] T007 Implement data integrity checker (SHA-256) for `data/` artifacts and hash storage in `state/`
- [ ] T008 Setup `pytest` configuration in `tests/conftest.py` with seed pinning for reproducibility

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Quality Control (Priority: P1) 🎯 MVP

**Goal**: Download real fMRI data from OpenNeuro, calculate motion metrics, and enforce strict QC thresholds (FR-002, FR-009, FR-010).

**Independent Test**: Can be fully tested by executing the data pipeline on a single subject file, verifying the motion parameter output, and confirming the subject is either retained or excluded based on the >3mm threshold.

### Tests for User Story 1
> Note: Tasks T009-T011 are implemented as failing stubs first. They will intentionally fail until the corresponding implementation tasks (T012-T018) are completed, adhering to the "tests first" methodology. These tests are NOT parallel-safe [P] as they depend on the existence of the implementation code to run.

- [ ] T009 [US1] Unit test for motion calculation logic in `tests/unit/test_qc.py` (STUB: verify displacement math, currently fails)
- [ ] T010 [US1] Unit test for `test_motion_hard_stop` in `tests/unit/test_qc.py` (STUB: verify pipeline halts if all subjects fail, currently fails)
- [ ] T011 [US1] Unit test for `test_condition_completeness` in `tests/unit/test_qc.py` (STUB: verify exclusion of subjects missing one condition, currently fails)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/data_loader.py` to fetch OpenNeuro dataset `ds` using `requests` with retry logic; raise `ERR_DATA_UNAVAILABLE` if download fails or `events.tsv` lacks "Inclusion"/"Exclusion" markers
- [ ] T013 [US1] Implement `src/qc.py` to calculate head motion displacement (Framewise Displacement) for every subject from motion parameters
- [ ] T014 [US1] Implement `src/qc.py` to filter and return a list of subjects with max displacement <= 3mm (per-subject exclusion, FR-002)
- [ ] T015 [US1] Implement `src/qc.py` to check the count of filtered subjects; if < 10, raise `ERR_N_INSUFFICIENT` (FR-009, global halt logic)
- [ ] T016 [US1] Implement `src/qc.py` to verify each subject has valid time-series data for BOTH Inclusion and Exclusion conditions; exclude if missing (FR-010)
- [ ] T017 [US1] Implement `src/main.py` orchestrator to integrate download, run QC (T013-T016), handle exceptions, and output `data/processed/subjects_metadata.json` listing retained subjects

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Connectivity Metric Computation (Priority: P2)

**Goal**: Extract ROI time-series, compute correlation matrices, and derive connectivity strength metrics (FR-003, FR-004, FR-005).

**Independent Test**: Can be tested by running the calculation on a synthetic time-series dataset with known correlations and verifying the output matches the expected mean absolute correlation value.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for preprocessing logic in `tests/unit/test_preprocessing.py` (verify nuisance regression)
- [ ] T021 [P] [US2] Unit test for ROI extraction logic in `tests/unit/test_extraction.py` (verify signal extraction from PCC, mPFC, Angular)
- [ ] T022 [P] [US2] Unit test for correlation calculation in `tests/unit/test_connectivity.py` (verify Pearson correlation and MAC math)

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `src/preprocessing.py` to perform nuisance regression (motion params + derivatives, WM, CSF) using memory-mapped NIfTI loading (`nilearn.image.load_img` with `mmap=True`); **DO NOT** include global signal regression as it is not in scope.
- [ ] T024 [US2] Implement `src/extraction.py` to extract BOLD time-series from PCC, mPFC, and angular gyrus using AAL/Harvard-Oxford atlas (FR-003); ensure memory usage < 7GB by processing subject-by-subject
- [ ] T025 [US2] Implement `src/connectivity.py` to segment time-series by Inclusion/Exclusion event markers (Consumes output from T024)
- [ ] T026 [US2] Implement `src/connectivity.py` to compute Pearson correlation matrices per condition from segmented data (FR-004)
- [ ] T027 [US2] Implement `src/connectivity.py` to calculate Mean Absolute Correlation (MAC) as the primary metric per FR-005; store global mean metric in `data/processed/connectivity_metrics.json`
- [ ] T028 [US2] Implement `src/main.py` logic to save `data/processed/connectivity_metrics.json` (subject-level MAC)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Hypothesis Testing (Priority: P3)

**Goal**: Execute permutation tests, apply FDR correction, generate sensitivity curves, and frame results correctly (FR-006, FR-007, FR-008, FR-011, SC-005).

**Independent Test**: Can be tested by running the permutation test on a dataset where the null hypothesis is known to be true (random noise) and verifying the p-value distribution is uniform.

### Tests for User Story 3

- [ ] T029 [P] [US3] Unit test for `test_permutation_logic` in `tests/unit/test_stats.py` (verify shift detection in synthetic data)
- [ ] T030 [P] [US3] Unit test for `test_edge_wise_fdr` in `tests/unit/test_stats.py` (verify FDR correction application)
- [ ] T031 [P] [US3] Unit test for `test_sensitivity_curve` in `tests/unit/test_stats.py` (verify generation of curve across thresholds)
- [ ] T032 [P] [US3] Unit test for stability metric calculation in `tests/unit/test_stats.py` (verify null distribution std dev calculation)

### Implementation for User Story 3

- [ ] T033 [US3] Implement `src/stats.py` with non-parametric paired permutation test (adaptive iterations, subject-level) for MAC; ensure function is parameterized to allow re-execution with different motion thresholds (FR-006)
- [ ] T034 [US3] Implement `src/stats.py` for edge-wise statistical testing with FDR correction (q ≤ 0.05) applied **only** to the set of multiple edge-wise p-values; **DO NOT** apply FDR to the single global mean metric (FR-011, FR-008)
- [ ] T035 [US3] Implement `src/stats.py` to calculate the standard deviation of the permutation null distribution, then calculate the stability of the connectivity strength metric as the ratio `|mean_MAC - mean_null| / std_dev_null`; store both the null std dev and the calculated stability ratio in `data/results/stability_metric.json` (SC-002)
- [ ] T036 [US3] Implement `src/stats.py` to generate a sensitivity curve measuring the **proportion of subjects retained** across motion thresholds {, 3.0, 4.0} mm, using the **fixed set of subjects retained at the threshold** (re-evaluating their motion metrics only, not re-running full QC exclusion logic); save to `data/results/sensitivity_curve.csv` with columns: threshold, retention_proportion (SC-005)
- [ ] T037 [US3] Implement `src/stats.py` logic to check `randomization_verified` flag in dataset metadata; if false or missing, the output report MUST explicitly contain the literal string "associational" (FR-007)
- [ ] T038 [US3] Implement `src/visualization.py` to generate bar plots with confidence intervals and null distribution histograms
- [ ] T039 [US3] Implement `src/main.py` to orchestrate statistical testing, save `data/results/statistical_report.json`, and generate final PDF/HTML report

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Create `quickstart.md` in `specs/001-neural-correlates-social-exclusion/`
- [ ] T041 [P] Create `data-model.md` in `specs/001-neural-correlates-social-exclusion/`
- [ ] T042 Code cleanup and refactoring of `src/main.py` orchestrator
- [ ] T043 Performance optimization: Ensure memory usage stays within 7GB limit during permutation tests (chunking if necessary)
- [ ] T044 [P] Additional unit tests for edge cases (missing files, malformed JSON) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure end-to-end pipeline execution on CPU-only runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires QC output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires Connectivity Metrics from US2

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
- All tests for a user story marked [P] can run in parallel (once implementation exists)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation exists):
Task: "Unit test for motion calculation logic in tests/unit/test_qc.py"
Task: "Unit test for test_motion_hard_stop in tests/unit/test_qc.py"
Task: "Unit test for test_condition_completeness in tests/unit/test_qc.py"

# Launch implementation tasks (sequentially due to dependencies):
Task: "Implement src/data_loader.py (download)"
Task: "Implement src/qc.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & QC)
4. **STOP and VALIDATE**: Test data pipeline and QC logic on real data (or fail gracefully if data unavailable)
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
   - Developer A: User Story 1 (Data & QC)
   - Developer B: User Story 2 (Connectivity)
   - Developer C: User Story 3 (Stats & Viz)
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
- **Real Data Only**: T012 must fetch real data from OpenNeuro. Simulation is only for unit tests, not the main pipeline.
- **CPU Constraints**: All tasks must be feasible on Multiple CPU cores, 7GB RAM, no GPU.