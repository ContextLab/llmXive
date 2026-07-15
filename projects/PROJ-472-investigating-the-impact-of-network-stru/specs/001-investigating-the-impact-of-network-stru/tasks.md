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

- [X] T004 [P] Implement `code/config.py` for paths, seeds, and hyperparameters. **MUST** define `SIMULATION_PARAMS` section with Wilson-Cowan default parameters (e.g., connection strength, time constants) to ensure T011b is deterministic.
- [X] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/results`) with checksum tracking
- [X] T006 Create base data models (Participant, StructuralConnectome, AvalancheRecord) in `code/data/models.py`
- [X] T007 Implement robust error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 Setup environment configuration management (`.env` loading)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Integration (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes and *real* resting-state EEG recordings (with fallback to simulation for validation only) to enable metric computation. **Primary Path**: Simulation (due to Plan constraints). **Probe Path**: Attempt real data from OpenNeuro ds004230/4231. **Fallback Path**: Alternative datasets (ds004503, HCP-Lifespan) if primary fails. **Strict Failure**: If no data found, halt and report.

**Independent Test**: Can be fully tested by successfully downloading a subset of dMRI (and optionally EEG) data from OpenNeuro (or fallback), preprocessing it to adjacency matrices, and generating synthetic EEG for the primary analysis path.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `code/data/download.py` to fetch dMRI tractography data. **Logic**: 1) Attempt OpenNeuro ds004230. 2) If unavailable, attempt OpenNeuro ds004503 or HCP-Lifespan (as per Spec Assumptions). 3) If no matched dMRI+EEG found, **FAIL LOUDLY** with a clear error message and exit. **MUST** implement the full fallback chain before failing. **MUST** fail loudly if no real data source is found.
- [X] T010 [P] [US1] Implement `code/data/preprocess_dMRI.py` to convert raw tractography (`.tck` format) to HCP-MMP (-parcel) adjacency matrices using MRtrix3 `tck2connectome`. **MUST** download the HCP-MMP1.0 parcellation file from the official HCP repository (or verified mirror) and **dynamically verify** its SHA-256 hash by fetching the manifest file from the source (do NOT hardcode a hash). **Depends on**: T009 (for subject IDs).
- [X] T011 [US1] **PROBE TASK**: Implement `code/data/preprocess_EEG.py` to attempt downloading and preprocessing **real** resting-state EEG recordings from **OpenNeuro ds004231** (FR-002). **EXPECTATION**: As per Plan Summary, matched real EEG is unavailable; this task is expected to fail to find data. **Logic**: 1) Attempt download. 2) If successful, preprocess (MNE band-pass low-frequency cutoff, 250 Hz, ICA). 3) If failed (data unavailable), raise a specific `DataUnavailableError` to trigger the simulation path. **MUST NOT** proceed with simulation if real data is found; **MUST** trigger simulation only if real data is missing. **Depends on**: T009.
- [X] T011b [P] [US1] **PRIMARY PATH**: Implement `code/data/simulate_EEG.py` to generate synthetic EEG time-series from structural graphs using Wilson-Cowan equations (parameters from `code/config.py` section `SIMULATION_PARAMS`). **MUST** apply MNE-Python band-pass filtering **1–40 Hz** and downsampling **250 Hz** to the *simulated* signals. **Default**: This task runs unless T011 successfully produced real data. **Depends on**: T010.
- [X] T011c [US1] **DATA UNAVAILABLE HANDLER**: Implement `code/data/handle_data_missing.py` to generate a `data/processed/data_status.json` flagging `real_data_available: false` and `simulation_path: true` if T011 was skipped or failed. **Depends on**: T011 (if skipped) or T011b (if run).
- [X] T012 [US1] Implement quality control checks in `code/data/quality_control.py`. **Real Data**: Exclude participants with >30% channels removed after ICA or disconnected structural graphs. **Simulated Data**: Exclude participants with signal variance outside the expected physiological range. **MUST** calculate and output the proportion of participants with complete *real* dMRI and EEG pipelines (SC-004) if real data exists, otherwise report 0% and simulation status.
- [X] T013 [US1] Create unified data store script in `code/data/store.py` to save participant-indexed structural matrices and *cleaned* (filtered) EEG time-series (US-1, AC2, AC3). **Depends on**: T011 (if run) or T011b (if run).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data pipeline complete, simulation path active)

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2)

**Goal**: Compute canonical structural network metrics and neural avalanche statistics from the processed data (Simulation Primary, Real Conditional).

**Independent Test**: Can be fully tested by computing metrics for the subset of participants generated in US1 and verifying that output values (degree, clustering, avalanche size) are within expected ranges for human brain networks and neural avalanches.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `code/analysis/metrics.py` to compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX and BCTpy (FR-003). **Depends on**: T010 completion. **Can run in parallel** with T015 (if T011 ran) or T015b.
- [X] T015 [US2] **CONDITIONAL**: Implement `code/analysis/avalanches.py` to detect neural avalanches by first applying z-score normalization (global mean/std) to the **real** EEG signal, then thresholding at the **75th percentile** amplitude (calculated per-participant over the entire resting-state recording) to identify contiguous spatiotemporal events across channels. **CONDITIONAL**: Only execute if T011 successfully produced real data. **Depends on**: T011.
- [X] T015b [P] [US2] **PRIMARY PATH**: Implement `code/analysis/avalanches.py` (or `avalanches_sim.py` if separation preferred) to detect avalanches from *simulated* EEG (from T011b) using the same 75th percentile threshold. **Default**: Runs if T011 was skipped. **Depends on**: T011b.
- [X] T016 [US2] Implement power-law model fitting in `code/analysis/fitting.py` using `powerlaw` package with model comparison (power-law vs. exponential vs. log-normal) per FR-011.
- [X] T017 [US2] Create export script `code/analysis/export_metrics.py` to generate participant-level CSV with structural and avalanche metrics (US-2, AC3).
- [X] T018 [P] [US2] Implement unit tests in `tests/test_metrics.py` (e.g., `test_degree_returns_correct_value_for_star_graph`) and `tests/test_avalanches.py` (e.g., `test_avalanche_detection_handles_flat_signal`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (metrics computed)

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction for multiple comparisons and threshold sensitivity.

**Independent Test**: Can be fully tested by running the association analysis on the computed metrics and verifying that correlation coefficients, p-values, and sensitivity sweep results are reproducible and frame findings as associational.

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/analysis/stats.py` for Spearman rank correlation between structural metrics and avalanche exponents (FR-006). **Depends on**: T014 and T015 (if run) or T015b (if run).
- [X] T020 [US3] Implement non-parametric permutation test (shuffles) and family-wise error correction using **max-t permutation** method (FR-007) in `code/analysis/stats.py`. **Depends on**: T019 completion.
- [X] T021 [US3] Implement collinearity diagnostics (VIF) in `code/analysis/stats.py` with flagging logic for VIF ≥ 5 (FR-009).
- [X] T022 [US3] Implement sensitivity analysis sweep across a range of thresholds in `code/analysis/sensitivity.py` (FR-008).
- [X] T023 [US3] Create final report generator `code/analysis/report.py` ensuring all findings are framed as associational (FR-010).
- [X] T024 [P] [US3] Implement integration tests in `tests/test_stats.py` using a mock dataset of a small cohort of participants with known ground-truth correlations; assert p_value < 0.05 for known correlation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Compliance (Addressing Review Concerns)

**Goal**: Resolve specific gaps identified in the specification vs. plan alignment and ensure strict adherence to data integrity rules. **MUST** run before Phase 7 (Polish) and T029 (Validation).

### Implementation for Revision

- [ ] T030 [US2] **Clarify Simulation Parameters**: Update `code/data/simulate_EEG.py` to explicitly log the random seed and Wilson-Cowan parameters used for every participant, and ensure these are saved to `data/processed/simulation_metadata.json`. **Rationale**: Reproducibility (Constitution Principle I) requires that the exact synthetic generation parameters be traceable for every result.
- [ ] T031 [US3] **Standardize Sensitivity Sweep Range**: Update `code/analysis/sensitivity.py` to explicitly replace all instances of the string "[deferred]" with the list `[0.70, 0.75, 0.80]` in the threshold configuration block, per FR-008. **Rationale**: SC-002 requires measuring stability across specific thresholds; "deferred" in code leads to inconsistent execution.
- [ ] T032 [US3] **Enforce Associational Framing**: Add a validation step in `code/analysis/report.py` that scans the generated text for causal keywords (e.g., "causes", "drives", "leads to") and raises a `RuntimeError` if found, forcing the user to rephrase. **Rationale**: FR-010 and US-3 explicitly forbid causal claims; automated enforcement ensures compliance.
- [ ] T033 [US2] **Validate Power-Law Fit Convergence**: Update `code/analysis/fitting.py` to explicitly handle the `powerlaw` package's convergence failure by logging a specific error code and excluding the participant from the correlation matrix, rather than silently returning NaN. **Rationale**: FR-011 requires model comparison; silent failures corrupt the statistical association in US-3.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Documentation updates in `docs/` including data model and API usage
- [ ] T026 Code cleanup and refactoring to ensure modularity
- [X] T027 Profile `code/analysis/stats.py` and optimize the permutation loop using multiprocessing and **chunked processing** to ensure total runtime ≤ 6 hours on CPU-only runner for **N=50 subjects** (SC-006).
- [ ] T028 [P] Additional unit tests for edge cases (power-law convergence failure, disconnected graphs)
- [X] T029a [US3] **Validation A (Correlation Path)**: Run end-to-end validation for **Correlation Path**. **Logic**: 1) Count usable subjects N after QC. 2) If N >= 10: Assert `data/results/correlation_report.csv` exists and contains >= 10 rows. 3) If N < 10: Assert `data/results/correlation_report.csv` does NOT exist. **MUST** fail if conditions are violated. **Depends on**: T023, T012.
- [X] T029b [US3] **Validation B (Null Result Path)**: Run end-to-end validation for **Null Result Path**. **Logic**: 1) Count usable subjects N after QC. 2) If N < 10: Assert `data/results/null_result_report.md` exists (per Plan Null Result Protocol) and `correlation_report.csv` does NOT exist. 3) If N >= 10: Assert `data/results/null_result_report.md` does NOT exist. **MUST** fail if conditions are violated. **Depends on**: T023, T012.
- [X] T029c [US3] Implement the 'Null Result Protocol' in `code/main.py`: if <10 usable subjects remain after QC (for the *real* pipeline), halt correlation analysis and generate a report stating "Pipeline Validated, Insufficient Data for Simulation" (Plan constraint).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 6)**: **MUST** be completed before Phase 7 (Polish) and T029 (Validation) to ensure data integrity and specification compliance.
- **Polish (Phase 7)**: Depends on Revision and all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data output (specifically T010 and T011/T011b)**
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
- **T009** (download) must implement the full fallback logic (ds004230 -> ds004503/HCP-Lifespan -> Fail) before T010 runs.
- **T011** (Real EEG) is **CONDITIONAL**. If T009 fails to find real EEG, T011 is **SKIPPED**.
- **T011b** (Simulation) is the **PRIMARY** path. It runs if T011 is skipped.
- **T015** (Real Avalanches) is **CONDITIONAL**. It runs only if T011 ran. If T011 is skipped, T015 is **SKIPPED**.
- **T015b** (Sim Avalanches) is the **PRIMARY** path. It runs if T011 is skipped.
- **T019** (stats.py) **MUST** run after T014 and the active avalanche task (T015 or T015b).
- **T020** (permutation) **MUST** run after T019.
- **T030-T033** (Revision) **MUST** run after the initial implementation of the respective user stories to ensure the fixes are applied to the correct logic, and **MUST** complete before Phase 7 (Polish) and T029 (Validation).
- **T029a** and **T029b** are split validation tasks to handle mutually exclusive outcomes (Correlation vs Null Result) without logical contradiction. T029a asserts correlation report existence only if N>=10. T029b asserts null result report existence only if N<10.

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
3. Complete Phase 3: User Story 1 (Simulation Primary Path)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Simulation Primary) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Primary)
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
- **Simulation Primary**: The Plan states real EEG is unavailable. T011b is the default path. T011 is a probe.
- **Fallback Logic**: T009 implements the full spec-authorized fallback chain (ds004230 -> ds004503 -> HCP-Lifespan -> Fail).
- **Revision Protocol**: Tasks T030-T033 are mandatory to address specific reviewer concerns regarding data source verification, failure handling, and statistical rigor. These must be completed before the project is considered "Clean" and before Phase 7 (Polish) and T029 (Validation).
- **Validation Logic**: T029a and T029b handle the mutually exclusive outcomes (>=10 subjects or <10 subjects) as valid completions, avoiding the logical contradiction of a single task asserting both. T029a validates the correlation path; T029b validates the null result path.