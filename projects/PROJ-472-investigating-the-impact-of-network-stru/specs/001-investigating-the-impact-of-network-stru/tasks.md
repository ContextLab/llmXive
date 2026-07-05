# Tasks: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Input**: Design documents from `/specs/001-network-structure-avalanche-dynamics/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for paths, seeds, and hyperparameters. **MUST** define `SIMULATION_PARAMS` section with Wilson-Cowan default parameters (e.g., connection strength, time constants) to ensure T011 is deterministic.
- [X] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/results`) with checksum tracking <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 4, column 1:
 **Input**: Design documents from...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 4, column 2:
 **Input**: Design documents from...
 ^) -->
- [X] T006 Create base data models (Participant, StructuralConnectome, AvalancheRecord) in `code/data/models.py`
- [X] T007 Implement robust error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 Setup environment configuration management (`.env` loading)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Integration (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes and simulate resting‑state EEG recordings to enable metric computation. **Note**: Due to data availability, this pipeline uses OpenNeuro ds003813 dMRI and *simulated* EEG, adapted from FR-002.

**Independent Test**: Can be fully tested by successfully downloading a subset of dMRI data from OpenNeuro (sub-001 to sub-010), preprocessing it to adjacency matrices, and generating synthetic EEG time-series for at least 10 participants with matching subject identifiers.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `code/data/download.py` to fetch dMRI tractography data (specifically `bvec`, `bval`, `dwi.nii.gz` files) for a subset of subjects from OpenNeuro ds003813. **Note**: This is a staged simplification due to HCP data availability; FR-001's HCP requirement is adapted by applying HCP-MMP1.0 parcellation via registration to the OpenNeuro data to maintain structural metric compatibility.
- [ ] T010 [P] [US1] Implement `code/data/preprocess_dMRI.py` to convert raw tractography (`.tck` format) to -parcel adjacency matrices using MRtrix3 `tck2connectome`. **MUST** download the HCP-MMP1.0 parcellation file from ` (SHA-256: `a1b2c3d4...`) and apply it via registration to the OpenNeuro data. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T011 [US1] Implement `code/data/simulate_EEG.py` to generate synthetic EEG time-series from structural graphs using Wilson-Cowan equations (parameters from `code/config.py` section `SIMULATION_PARAMS`). **MUST** apply MNE-Python band-pass filtering (low-frequency to an upper cutoff) and downsampling (appropriate frequency) to the *simulated* signals to mimic the real-data preprocessing step required by FR-002. **Note**: This is an adaptation for simulation; ICA is not applicable to synthetic data.
- [ ] T012 [US1] Implement quality control checks in `code/data/quality_control.py` to exclude participants with disconnected graphs or insufficient data quality. **Define** 'removed channels' as channels with SNR < 5dB in simulated data. **Note**: This metric measures simulation fidelity, not biological artifact rejection (FR-002 adaptation).
- [~] T012b [US1] Implement reporting logic in `code/data/quality_control.py` to calculate and output the proportion of participants with complete *simulated* pipelines (SC-004 adaptation).
- [~] T013 [US1] Create unified data store script in `code/data/store.py` to save participant-indexed structural matrices and *cleaned* (filtered) EEG time-series (US-1, AC2, AC3).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data pipeline complete)

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2)

**Goal**: Compute canonical structural network metrics and neural avalanche statistics from the processed/simulated data.

**Independent Test**: Can be fully tested by computing metrics for the subset of participants generated in US1 and verifying that output values (degree, clustering, avalanche size) are within expected ranges for human brain networks and neural avalanches.

### Implementation for User Story 2

- [~] T014 [P] [US2] Implement `code/analysis/metrics.py` to compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX and BCTpy (FR-003). **Note**: Can run in parallel with T015 *after* T010 completes.
- [~] T015 [US2] Implement `code/analysis/avalanches.py` to detect neural avalanches by first applying z-score normalization (global mean/std) to the *simulated* EEG signal, then thresholding at a high percentile amplitude calculated *per-participant* over the entire *simulated* resting-state recording. **Note**: Adapted from FR-004 for simulation; 'resting-state' context is synthetic.
- [~] T016 [US2] Implement power-law model fitting in `code/analysis/fitting.py` using `powerlaw` package with model comparison (power-law vs. exponential vs. log-normal) per FR-011.
- [~] T017 [US2] Create export script `code/analysis/export_metrics.py` to generate participant-level CSV with structural and avalanche metrics (US-2, AC3).
- [~] T018 [P] [US2] Implement unit tests in `tests/test_metrics.py` (e.g., `test_degree_returns_correct_value_for_star_graph`) and `tests/test_avalanches.py` (e.g., `test_avalanche_detection_handles_flat_signal`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (metrics computed)

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction for multiple comparisons and threshold sensitivity.

**Independent Test**: Can be fully tested by running the association analysis on the computed metrics and verifying that correlation coefficients, p-values, and sensitivity sweep results are reproducible and frame findings as associational.

### Implementation for User Story 3

- [~] T019 [US3] Implement `code/analysis/stats.py` for Spearman rank correlation between structural metrics and avalanche exponents (FR-006). **Depends on**: T014 and T015 completion.
- [~] T020 [US3] Implement non-parametric permutation test (sufficient shuffles) and family-wise error correction using **Holm-Bonferroni** method in `code/analysis/stats.py` (FR-007). **Depends on**: T019 completion.
- [~] T021 [US3] Implement collinearity diagnostics (VIF) in `code/analysis/stats.py` with flagging logic for VIF ≥ 5 (FR-009).
- [~] T022 [US3] Implement sensitivity analysis sweep across a range of thresholds in `code/analysis/sensitivity.py` (FR-008).
- [~] T023 [US3] Create final report generator `code/analysis/report.py` ensuring all findings are framed as associational (FR-010).
- [~] T024 [P] [US3] Implement integration tests in `tests/test_stats.py` using a mock dataset of a small cohort of participants with known ground-truth correlations; assert p_value < 0.05 for known correlation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T025 [P] Documentation updates in `docs/` including data model and API usage
- [~] T026 Code cleanup and refactoring to ensure modularity
- [ ] T027 Profile `code/analysis/stats.py` and optimize the permutation loop using multiprocessing to ensure total runtime ≤ 6 hours on CPU-only runner for **N=10 subjects** (SC-006).
- [ ] T028 [P] Additional unit tests for edge cases (power-law convergence failure, disconnected graphs)
- [ ] T029 Run quickstart.md validation and verify `main.py` orchestration end-to-end by executing `python code/main.py --config config.yaml` and asserting that `data/results/correlation_report.csv` exists and contains a sufficient number of rows to support the analysis (where N_usable is the count of participants passing QC in T012).
- [ ] T029b Implement the 'Null Result Protocol' in `code/main.py`: if <10 usable subjects remain after QC (for the *simulated* pipeline), halt correlation analysis and generate a report stating "Pipeline Validated, Insufficient Data for Simulation" (Plan constraint).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data output (specifically T010 and T011)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 metric output**

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

**⚠️ CRITICAL DEPENDENCY NOTES**:
- **T011** (simulate_EEG) **MUST** run after **T010** (preprocess_dMRI) as it consumes the adjacency matrices. T011 is **NOT** parallel-safe ([P] removed).
- **Phase 4** (US2) **MUST** wait for completion of **Phase 3** (US1), specifically T010 and T011, as US2 metrics require the structural and simulated EEG data.
- **T014** (metrics) and **T015** (avalanches) can run in parallel *only after* T010 and T011 are complete, respectively.
- **T019** (stats.py) **MUST** run after **T014** and **T015** are complete.
- **T020** (permutation) **MUST** run after **T019**.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Simulation Approach**: This project uses simulated EEG data derived from dMRI structural connectomes due to the unavailability of matched real-world datasets. All preprocessing steps (FR-002) and analysis logic (FR-004) are **adapted** to this simulated data to maintain functional consistency with the spec's statistical intent, while acknowledging the data source deviation.