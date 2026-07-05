# Tasks: Brain Network Efficiency and Fluid Intelligence

**Input**: Design documents from `/specs/001-brain-network-efficiency-fluid-intelligence/`
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

- [ ] T001 Create project structure per implementation plan by running `mkdir -p data/raw data/processed code/tests results/figures results/reports state/`

- [ ] T002 Create requirements.txt with pinned versions: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `requests`, `tqdm`, `pyyaml`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure: `data/raw`, `data/processed`, `results/figures`, `results/reports`, `state/`
- [ ] T005 [P] Implement state management utility to record checksums in `state/*.yaml` (Constitution Principle III)
- [ ] T006 [P] Create base logging configuration and error handling wrappers
- [ ] T007 Implement adaptive sampling logic: Create `code/sampling.py` with function `select_subjects(n_target=500, max_runtime=21600)`. Logic: Attempt N=500; if runtime > 21600s, re-run with N=200. Return list of subject IDs (FR-011)
- [ ] T008 Setup CI configuration (GitHub Actions) with limited CPU, Limited RAM constraints

The research question, method, and references remain as stated in the original planning document. and h timeout

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Download and Preprocess HCP Data (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data and fluid intelligence scores, preprocess with nuisance regression and band-pass filtering, and prepare for graph analysis.

**Independent Test**: Verify downloaded and preprocessed data files exist with expected dimensions, checksums match `state/*.yaml`, and mean framewise displacement ≤0.2 mm.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for download retry logic (≥1 retry) in `tests/unit/test_download.py`
- [ ] T011 [P] [US1] Unit test for FD calculation and exclusion threshold in `tests/unit/test_preprocess.py`
- [ ] T012 [P] [US1] Integration test verifying data integrity after preprocessing in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download.py`: Fetch HCP resting-state fMRI and NIH Toolbox Fluid Intelligence scores (≥95% subjects) with retry logic (FR-001)
- [ ] T014 [US1] Implement `code/preprocess.py`: Apply nuisance regression and band-pass filtering at low frequencies (FR-002)

### Sub-phase 3B: Validation & Exclusion (Depends on T013/T014 completion)

- [ ] T015 [US1] Implement framewise displacement (FD) calculation and subject exclusion (>0.5 mm) with logging (Edge Cases)
- [ ] T016 [US1] Implement missing score exclusion logic and logging (Edge Cases)
- [ ] T017 [US1] Create `code/validate_data.py` to verify preprocessed time series dimensions and quality metrics; check mean FD <= 0.2; exit 0 if pass, 1 if fail
- [ ] T018 [US1] Record data checksums in `state/data_manifest.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Graph Efficiency Metrics (Priority: P2)
**Depends on Phase 3 completion (US1 data output must exist)**

**Goal**: Parcellate brains using Schaefer atlas, compute connectivity matrices, and calculate global/frontoparietal efficiency metrics.

**Independent Test**: Verify efficiency metrics exist for ≥95% subjects, edge density is within ±1% of target, and robustness checks (400-ROI, weighted) are computed.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Schaefer atlas loading and ROI mapping in `tests/unit/test_atlas.py`
- [ ] T020 [P] [US2] Unit test for connectivity matrix thresholding and density verification in `tests/unit/test_graph_metrics.py`
- [ ] T021 [P] [US2] Unit test for global efficiency calculation on disconnected graphs (harmonic mean) in `tests/unit/test_graph_metrics.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/graph_metrics.py`: Load Schaefer atlas and parcellate preprocessed time series (FR-003)
- [ ] T023 [US2] Implement functional connectivity matrix computation (Pearson correlation, retain positive edges only and exclude negative edges) (FR-003)
- [ ] T024 [US2] Implement binary graph thresholding at a low density to identify the core structural component. and verify sparsity (FR-003)
- [ ] T025 [US2] Compute global efficiency and frontoparietal subgraph efficiency (using Yeo cortical parcellation definition) for a set of ROIs.; document Yeo-7 definition in `results/reports/methodology.md` to avoid circular bias (FR-004, FR-014)
- [ ] T026 [US2] Implement robustness check: Compute efficiency using the Schaefer atlas with a high-resolution parcellation scheme. (FR-012)
- [ ] T027 [US2] Implement robustness check: Compute weighted-graph efficiency alongside binary metrics (FR-013)
- [ ] T028 [US2] Save all metrics to `data/processed/graph_metrics.csv` with subject IDs and atlas resolution tags
- [ ] T029 [US2] Validate that frontoparietal subgraph definition is non-circular and append section 3.2 to `results/reports/methodology.md` documenting Yeo-7 definition (FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Reporting (Priority: P3)
**Depends on Phase 4 completion (US2 metrics must exist)**

**Goal**: Run correlation/regression analyses with permutation testing, VIF checks, and generate final results.

**Independent Test**: Verify statistical outputs include correlation coefficients, FWE-corrected p-values, effect sizes, and VIF reports.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for permutation testing logic (max statistic generation) in `tests/unit/test_stats.py`
- [ ] T031 [P] [US3] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Unit test for ridge regression fallback when VIF > 5 in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/stats.py`: Compute Pearson/Spearman correlations between efficiency metrics and fluid intelligence (FR-005)
- [ ] T034 [US3] Implement multiple linear regression with covariates (age, sex, mean FD) (FR-006)
- [ ] T035 [US3] Implement permutation testing (Perform a sufficient number of permutations to ensure statistical robustness.; reduce count ONLY if runtime exceeds a predefined threshold (6 hours)) for FWE correction (FR-007)
- [ ] T036 [US3] Implement VIF calculation; if VIF > 5, flag collinearity and run orthogonalized/ridge regression (FR-009)
- [ ] T037 [US3] Generate results report: Correlation coefficients, FWE-corrected p-values, effect sizes for Global/FP efficiency; explicitly document findings as associational and Yeo-7 definition (FR-008, FR-014)
- [ ] T038 [US3] Compute robustness check stability: Compare effect direction consistency across 400-ROI; validate against ≥80% consistency threshold; if threshold is not met, log failure and exit with code 1; output to `results/reports/robustness_log.json` (SC-003)
- [ ] T039 [US3] Add citation to NIH Toolbox validation study in `results/reports/results.md` (FR-010)
- [ ] T040 [US3] Document findings as associational, not causal, in final report (FR-008)
- [ ] T041 [US3] Run `code/power_analysis.py` with effect_size=0.25; re-run if N < 500; fail if power < 80% (SC-005)
- [ ] T042 [US3] Generate final `results/reports/final_analysis.md` with all metrics, plots, and citations
- [ ] T050 [US3] Document that the frontoparietal subgraph is defined by the Yeo-7 atlas and findings are associational in `results/reports/final_analysis.md` (FR-014, FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Update `quickstart.md` with execution instructions for the full pipeline
- [ ] T044 Run `bash quickstart.sh`; verify exit code 0 and no errors in logs; verify runtime logs exist (SC-004)
- [ ] T045 Code cleanup: Ensure all scripts handle edge cases (missing data, disconnected graphs) gracefully
- [ ] T046 Verify `state/*.yaml` timestamps update on every artifact change (Constitution Principle V)
- [ ] T047 Instrument runtime measurement in `code/main.py` and log against the 6-hour constraint (SC-004)
- [ ] T048 [P] Verify actual runtime against 6-hour limit by parsing logs; fail build if > 6 hours (SC-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: 
  - User Story 1 (P1): Can start after Foundational (Phase 2) - No dependencies on other stories
  - User Story 2 (P2): **MUST WAIT** for Phase 3 completion (T018 must complete). Data flow: US1 -> US2.
  - User Story 3 (P3): **MUST WAIT** for Phase 4 completion (T028 must complete). Data flow: US2 -> US3.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Execution Rules

- **NO PARALLEL EXECUTION ACROSS USER STORIES**: US2 cannot start until US1 data is generated. US3 cannot start until US2 metrics are generated.
- **Parallelism within Phases**: Tasks marked [P] within the same phase (e.g., T010-T012) can run in parallel.
- **Sequential Flow**: T013/T014 -> T015/T016 -> T017 -> T018 -> T022... -> T028 -> T033...

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
3. Add User Story 2 → Test independently → Deploy/Demo (Wait for US1 output)
4. Add User Story 3 → Test independently → Deploy/Demo (Wait for US2 output)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2 (waits for US1 data)
   - Developer C: User Story 3 (waits for US2 data)
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
- **Constraint**: All analysis must run on CPU-only CI (cores, ~7GB RAM) within 6 hours. No GPU, no deep learning, no 8-bit models.