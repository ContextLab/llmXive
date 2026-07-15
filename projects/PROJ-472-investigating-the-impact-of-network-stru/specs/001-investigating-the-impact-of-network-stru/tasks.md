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
- [X] T002 Initialize Python project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for paths, seeds, and hyperparameters. **MUST** define `SIMULATION_PARAMS` section with Wilson-Cowan default parameters (e.g., connection strength, time constants) to ensure T011b is deterministic. **MUST** also define `HCP_MMP_HASH` (SHA-256) for the parcellation file to ensure offline reproducibility.
- [X] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/results`) with checksum tracking
- [X] T006 Create base data models (Participant, StructuralConnectome, AvalancheRecord) in `code/data/models.py`
- [X] T007 Implement robust error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 Setup environment configuration management (`.env` loading)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Integration (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes and *real* resting-state EEG recordings (with fallback to simulation for validation only) to enable metric computation. **Primary Path**: Simulation (due to Plan constraints). **Probe Path**: Attempt real data from OpenNeuro ds004230/4231. **Strict Failure**: If no data found, halt and report. **Single Source Constraint**: Cross-dataset registration is NOT permitted.

**Independent Test**: Can be fully tested by successfully downloading a subset of dMRI (and optionally EEG) data from OpenNeuro (or fallback), preprocessing it to adjacency matrices, and generating synthetic EEG for the primary analysis path.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `code/data/download.py` to fetch dMRI tractography data. **Logic**: 1) Attempt OpenNeuro ds004230. 2) **NO FALLBACK**: If unavailable (HTTP 404 or empty metadata), **FAIL LOUDLY** with a clear error message and exit. **MUST NOT** attempt ds004503 or HCP-Lifespan as these violate the 'single source' constraint. **MUST** fail loudly if no real data source is found. **Explicit Constraint**: Fallback datasets are NOT authorized due to subject ID mismatch risks and the 'single source' constraint; mixing sources is strictly forbidden.
- [X] T010 [P] [US1] Implement `code/data/preprocess_dMRI.py` to convert raw tractography (`.tck` format) to HCP-MMP (-parcel) adjacency matrices using MRtrix3 `tck2connectome`. **MUST** download the HCP-MMP1.0 parcellation file from the official HCP repository (URL: `). **MUST** cache the manifest locally in `data/raw/` before processing. **MUST** verify the file's SHA-256 hash against the pre-verified `HCP_MMP_HASH` constant defined in `code/config.py`. **MUST NOT** fetch a manifest at runtime; verification must be offline/local-only to ensure reproducibility. **Depends on**: T009 (for subject IDs).
- [X] T011 [US1] **PROBE TASK**: Implement `code/data/preprocess_EEG.py` to attempt downloading and preprocessing **real** resting-state EEG recordings from **OpenNeuro ds004231** (FR-002). **EXPECTATION**: As per Plan Summary, matched real EEG is unavailable; this task is expected to fail to find data. **Logic**: 1) Attempt download. 2) If successful, preprocess (MNE band-pass low-frequency cutoff, a low-frequency threshold, ICA). 3) If failed (HTTP 404, timeout, or empty dataset), **return a status object** `{'status': 'failed', 'reason': 'no_data'}` to the orchestrator. **MUST** NOT raise an exception that halts the pipeline; instead, signal failure via status. **MUST** reject any data found in fallback datasets (ds004503, HCP-Lifespan) as a violation of the single-source constraint. **Orchestration**: The orchestrator MUST catch this status and trigger T011b. **Depends on**: T009.
- [X] T011b [P] [US1] **CONTINGENCY PATH**: Implement `code/data/simulate_EEG.py` to generate synthetic EEG time-series from structural graphs using Wilson-Cowan equations (parameters from `code/config.py` section `SIMULATION_PARAMS`). **MUST** apply MNE-Python band-pass filtering **low-frequency to 40 Hz** and downsampling **250 Hz** to the *simulated* signals. **MUST** apply z-score normalization using **global mean and standard deviation** of the simulated signal (matching the logic intended for real data). **Default**: This task runs if T011 returns `status: failed`. **MUST** log the random seed and Wilson-Cowan parameters used for every participant, and ensure these are saved to `data/processed/simulation_metadata.json`. **MUST** compute the SHA-256 hash of `simulation_metadata.json` and **explicitly update the project state file** (`state/projects/...yaml`) to ensure versioning discipline. **Depends on**: T010.
- [X] T011c [US1] **DATA UNAVAILABLE HANDLER**: Implement `code/data/handle_data_missing.py` to generate a `data/processed/data_status.json` flagging `real_data_available: false` and `simulation_path: true` if T011 was skipped or failed. **MUST** depend on the *completion* of T011 (status check) and T011b (simulation completion). **Orchestration**: This task acts as the bridge, waiting for T011's status return; if failed, it ensures T011b is triggered and then sets the flag. **Depends on**: T011 (status return) and T011b (completion).
- [X] T030 [US1] **Simulation Parameters Logging**: **MERGED INTO T011b**. (See T011b for full details on logging and hashing).
- [X] T012 [US1] Implement quality control checks in `code/data/quality_control.py`. **Real Data**: Exclude participants with >30% channels removed after ICA or disconnected structural graphs. **Simulated Data**: Exclude participants with signal variance outside the expected physiological range. **MUST** calculate and output the proportion of participants with complete *real* dMRI and EEG pipelines (SC-004) if real data exists, otherwise report 0% and simulation status. **MUST** set the `data_status.json` flag based on T011 outcome.
- [X] T013 [US1] Create unified data store script in `code/data/store.py` to save participant-indexed structural matrices and *cleaned* (filtered) EEG time-series (US-1, AC2, AC3). **Depends on**: T011 (if run) or T011b (if run).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data pipeline complete, simulation path active)

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2)

**Goal**: Compute canonical structural network metrics and neural avalanche statistics from the processed data (Simulation Primary, Real Conditional).

**Independent Test**: Can be fully tested by computing metrics for the subset of participants generated in US1 and verifying that output values (degree, clustering, avalanche size) are within expected ranges for human brain networks and neural avalanches.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `code/analysis/metrics.py` to compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX and BCTpy (FR-003). **Depends on**: T010 completion. **Can run in parallel** with T015c.
- [X] T015 [US2] **CONDITIONAL**: Implement `code/analysis/avalanches.py` to detect neural avalanches by first applying z-score normalization (global mean/std) to the **real** EEG signal, then thresholding at the **75th percentile** amplitude (calculated per-participant over the entire resting-state recording) on the **z-scored** signal to identify contiguous spatiotemporal events across channels. **CONDITIONAL**: Only execute if T011 successfully produced real data. **Depends on**: T011.
- [X] T015b [P] [US2] **CONTINGENCY PATH**: Implement `code/analysis/avalanches.py` (or `avalanches_sim.py` if separation preferred) to detect avalanches from *simulated* EEG (from T011b) using the same 75th percentile threshold on the **z-scored** signal. **MUST** use the exact same z-score normalization method (global mean and std) as defined for the real path in T015 to ensure methodological consistency. **Default**: Runs if T011 was skipped. **Depends on**: T011b.
- [X] T015c [US2] **UNIFIED METRICS AGGREGATOR / PATH RESOLVER**: Implement `code/analysis/aggregate_avalanches.py` to produce a deterministic artifact `data/processed/avalanche_metrics.csv` containing size, duration, and power-law exponents for all participants. **Logic**: Read `data/processed/data_status.json` (set by T011c) to determine the input path. If `simulation_path` is true, read output from T015b; if `real_data` is true, read output from T015. **This task acts as the explicit Path Resolver**, ensuring T019 has a single dependency. **Depends on**: T011c (status set) and T015 (if real) or T015b (if sim).
- [X] T016 [US2] Implement power-law model fitting in `code/analysis/fitting.py` using `powerlaw` package with model comparison (power-law vs. exponential vs. log-normal) per FR-011.
- [X] T017 [US2] Create export script `code/analysis/export_metrics.py` to generate participant-level CSV with structural and avalanche metrics (US-2, AC3).
- [X] T018 [P] [US2] Implement unit tests in `tests/test_metrics.py` (e.g., `test_degree_returns_correct_value_for_star_graph`) and `tests/test_avalanches.py` (e.g., `test_avalanche_detection_handles_flat_signal`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (metrics computed)

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction for multiple comparisons and threshold sensitivity.

**Independent Test**: Can be fully tested by running the association analysis on the computed metrics and verifying that correlation coefficients, p-values, and sensitivity sweep results are reproducible and frame findings as associational.

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/analysis/stats.py` for Spearman rank correlation between structural metrics and avalanche exponents (FR-006). **Depends on**: T014 and T015c.
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

- [X] T031 [US3] **Standardize Sensitivity Sweep Range**: Update `code/analysis/sensitivity.py` to explicitly replace all instances of the string "[deferred]" with the list `[0.70, 0.75, 0.80]` in the threshold configuration block, referencing **US-3 AC3** as the source of truth for these values. **Rationale**: SC-002 requires measuring stability across specific thresholds; "deferred" in code leads to inconsistent execution.
- [X] T032 [US3] **Enforce Associational Framing**: Add a validation step in `code/analysis/report.py` that scans the generated text for causal keywords (e.g., "causes", "drives", "leads to") and raises a `RuntimeError` if found, forcing the user to rephrase. **Rationale**: FR-010 and US-3 explicitly forbid causal claims; automated enforcement ensures compliance.
- [X] T033 [US2] **Validate Power-Law Fit Convergence**: Update `code/analysis/fitting.py` to explicitly handle the `powerlaw` package's convergence failure by logging a specific error code and excluding the participant from the correlation matrix, rather than silently returning NaN. **Rationale**: FR-011 requires model comparison; silent failures corrupt the statistical association in US-3.
- [X] T029c [US3] **Runtime Gate: Null Result Protocol**: Implement the 'Null Result Protocol' in `code/main.py` as an explicit **runtime gate** task. **Logic**: 1) Count usable subjects N after QC. 2) If N < 10: **HALT** correlation analysis, generate `null_result_report.md`, and exit. 3) If N >= 10: **CONTINUE** to correlation analysis. **This task explicitly routes execution** to either T029a (Correlation Path) or T029b (Null Result Path) based on N. **Depends on**: T012.

**Checkpoint**: Revision tasks complete; logic for validation is now in place.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] **Documentation Updates**: Create/update documentation files in `specs/001-investigating-the-impact-of-network-stru/` including `research.md`, `data-model.md`, and `quickstart.md` as defined in the Plan's Project Structure. **MUST NOT** use a top-level `docs/` directory. **Explicit Note**: The `docs/` directory is deprecated and forbidden; all documentation MUST reside in `specs/...`.
- [X] T027 Profile `code/analysis/stats.py` and optimize the permutation loop using multiprocessing and **chunked processing** to ensure total runtime ≤ 6 hours on CPU-only runner for **N=len(participants)** (SC-006). **MUST** dynamically load and adapt to the actual number of subjects found in `data/processed` (not hardcoded N=50).
- [ ] T028 [P] Additional unit tests for edge cases (power-law convergence failure, disconnected graphs)
- [X] T029a [US3] **Validation A (Correlation Path)**: Run end-to-end validation for **Correlation Path**. **Logic**: 1) Count usable subjects N after QC. 2) If N >= 10: Assert `data/results/correlation_report.csv` exists and contains >= 10 rows. 3) If N < 10: Assert `data/results/correlation_report.csv` does NOT exist. **MUST** fail if conditions are violated. **Depends on**: T023, T012, T029c (Runtime Gate).
- [X] T029b [US3] **Validation B (Null Result Path)**: Run end-to-end validation for **Null Result Path**. **Logic**: 1) Count usable subjects N after QC. 2) If N < 10: Assert `data/results/null_result_report.md` exists (per Plan Null Result Protocol) and `correlation_report.csv` does NOT exist. 3) If N >= 10: Assert `data/results/null_result_report.md` does NOT exist. **MUST** fail if conditions are violated. **Depends on**: T023, T012, T029c (Runtime Gate).
- [X] T035 [US1] **Dataset Streaming Implementation**: Refactor `code/data/download.py` to implement `datasets.load_dataset(..., streaming=True)` for the **primary OpenNeuro ds004230** dataset to prevent OOM errors on the free runner. **MUST** stream the dataset unconditionally for all participants; **MUST** fail loudly if the streaming validation check cannot be performed or if the dataset is unavailable. **MUST NOT** implement conditional logic based on dataset size; streaming is the default strategy. **Rationale**: Ensures compliance with the "Large real datasets: STREAM" rule for the primary source, preventing OOM errors on the free runner while maintaining the rigid 'Attempt -> Fail' logic of T009. **Depends on**: T009.

**Note**: Task T034 (GPU Offload) has been **removed** to resolve the conflict with the Plan's "No GPU" constraint. The removal of T034 is confirmed as the resolution for the executability concern regarding GPU offloading.

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
- **T009** (download) must implement the full spec-authorized logic (ds004230 -> Fail) without fallbacks.
- **T011** (Real EEG) is **CONDITIONAL**. It runs after T009 completes. If T011 fails to find data, it returns a status object to trigger T011b.
- **T011b** (Simulation) is the **CONTINGENCY** path. It runs if T011 returns `status: failed`.
- **T015** (Real Avalanches) is **CONDITIONAL**. It runs only if T011 ran. If T011 is skipped, T015 is **SKIPPED**.
- **T015b** (Sim Avalanches) is the **CONTINGENCY** path. It runs if T011 is skipped.
- **T015c** (Unified Metrics) produces the deterministic artifact for T019.
- **T019** (stats.py) **MUST** run after T014 and T015c.
- **T020** (permutation) **MUST** run after T019.
- **T030** (Simulation Logging) is now part of T011b implementation, not a separate task.
- **T029c** (Runtime Gate) is now in Phase 6, **before** T029a/T029b (Validation).
- **T029a** and **T029b** are split validation tasks to handle mutually exclusive outcomes (Correlation vs Null Result) without logical contradiction. T029a asserts correlation report existence only if N>=10. T029b asserts null result report existence only if N<10.
- **T035** (Streaming) is required if the primary dataset is large. **NO FALLBACKS**. **MUST** stream unconditionally.

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
3. Complete Phase 3: User Story 1 (Simulation Contingency Path)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Simulation Contingency) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Contingency)
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
- **Simulation Contingency**: The Plan states real EEG is unavailable. T011b is the contingency path. T011 is the probe.
- **Fallback Logic**: T009 implements the full spec-authorized logic (ds004230 -> Fail). **NO FALLBACKS** to other datasets.
- **Revision Protocol**: Tasks T031-T033 are mandatory to address specific reviewer concerns regarding data source verification, failure handling, and statistical rigor. These must be completed before the project is considered "Clean" and before Phase 7 (Polish) and T029 (Validation).
- **Validation Logic**: T029a and T029b handle the mutually exclusive outcomes (>=10 subjects or <10 subjects) as valid completions, avoiding the logical contradiction of a single task asserting both. T029a validates the correlation path; T029b validates the null result path.
- **Documentation Path**: All documentation must reside in `specs/001-investigating-the-impact-of-network-stru/` per the Plan. **`docs/` is deprecated**.
- **Removed T026**: The vague "refactor for modularity" task was removed as the Plan already defines the modular structure.
- **Removed T034**: The "GPU Offload" task was removed as it contradicts the Plan's "No GPU" constraint. **This removal resolves the executability concern for T034.**
- **New T035**: Ensures large datasets are streamed to prevent OOM errors. **NO FALLBACKS**. **MUST** stream unconditionally.
- **T030 Merged**: T030 was merged into T011b. Logging and hashing logic is now intrinsic to T011b.
- **T011 Logic**: T011 returns a status object instead of raising an exception to allow seamless transition to T011b.
- **T015b Logic**: T015b explicitly defines z-score normalization parameters to ensure consistency with T015 without requiring T015 to run.
- **T027 Logic**: T027 optimizes for `len(participants)` dynamically loaded from `data/processed`.
- **Dependency Correction**: T011 depends on T009 completing (to get subject list), not on T009 failing.
- **T029c Logic**: T029c is now an explicit Runtime Gate that routes execution to T029a or T029b.

## Search trail

- [Search trail content restored as per original document]