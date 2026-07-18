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

- [X] T004 [P] Implement `code/config.py` for paths, seeds, and hyperparameters. **MUST** define `HCP_MMP_FILE_PATH` (relative path to the parcellation file: `data/raw/HCP_MMP1.0_Glasser2016.zip`, to be placed in `data/raw` prior to execution or downloaded if missing), `SENSITIVITY_THRESHOLDS` (hardcoded list `{0.70, 0.75, 0.80}` per Spec), and `N_MIN` (default 10). **MUST** also define a constant `HCP_MMP_HASH` (SHA-256 of the pinned parcellation file) and update `state/projects/PROJ-472-investigating-the-impact-of-network-stru.yaml` with the `HCP_MMP_HASH` and timestamp. **This task explicitly handles the hash calculation and state update** to satisfy Constitution Principle V. The hash must be calculated from the file *after* it is placed in `data/raw` during setup, or verified against a known constant if the file is pre-pinned.
- [X] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/results`) with checksum tracking
- [X] T006 Create base data models (Participant, StructuralConnectome, AvalancheRecord) in `code/data/models.py`
- [X] T007 Implement robust error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 Setup environment configuration management (`.env` loading)
- [X] T025a [P] [US1] **Create `research.md`**: Generate `specs/001-network-structure-avalanche-dynamics/research.md`. **Content Requirements**: 1) Abstract (concise summary), 2) **Data Availability Analysis** (detailed discussion of availability of ds004230, ds004231; explicitly state that matched dMRI+EEG is unavailable), 3) **Simulation Justification** (rationale for pivot to simulation as per Plan Summary), 4) Null Result Justification (protocol if no data at all), 5) Power Analysis Plan (deferred). **MUST** reference the `research_phase_config.json` for deferred values (if applicable).
- [X] T025b [P] [US1] **Create `data-model.md`**: Generate `specs/001-network-structure-avalanche-dynamics/data-model.md`. **Content Requirements**: 1) Entity Definitions (Participant, StructuralConnectome, AvalancheRecord, CorrelationResult), 2) Schema Diagram (text-based), 3) Data Flow Description (Download -> Preprocess -> **Simulate** -> Metrics -> Stats). **MUST** define the `research_phase_config.json` schema for deferred thresholds and N_MIN.
- [X] T025c [P] [US1] **Create `quickstart.md`**: Generate `specs/001-network-structure-avalanche-dynamics/quickstart.md`. **Content Requirements**: 1) Prerequisites, 2) Installation, 3) Execution Steps (Real Data Path OR Simulation Path), 4) Output Interpretation. **MUST** include the logic for the routing gate.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Integration (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes from OpenNeuro ds004230. **If** matched real EEG from ds004231 is available, process it. **If not**, trigger the simulation pipeline (T011b) to generate synthetic EEG from the structural connectomes, as mandated by the Plan.

**Independent Test**: Can be fully tested by successfully downloading, preprocessing, and storing a subset of dMRI and (real or simulated) EEG data from OpenNeuro ds004230/31 in a unified participant‑indexed format.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `code/data/download.py` to fetch dMRI tractography data from **OpenNeuro ds004230** AND attempt to fetch resting-state EEG data from **OpenNeuro ds004231**. **Logic**: 1) Fetch dMRI from ds004230. 2) Attempt to fetch EEG from ds004231. 3) **Match Subjects**: Identify subject IDs present in both datasets. 4) **Proceed with Available Subset**: If matched subjects exist, store them. If NO matched subjects exist, **DO NOT FAIL**; instead, store the available dMRI subjects and flag the dataset as `simulation_required` in `data/processed/routing_state.json`. 5) **Stream** if size > 100MB. **Output**: `data/raw/ds004230/...` and `data/raw/ds004231/...` (if available).
- [X] T010 [P] [US1] Implement `code/data/preprocess_dMRI.py` to convert raw tractography (`.tck` format) to HCP-MMP (multiple parcels) adjacency matrices using MRtrix3 `tck2connectome`. **MUST** verify the presence of the HCP-MMP parcellation file at `data/raw/HCP_MMP1.0_Glasser2016.zip`. **If missing**, download it from the verified HCP source (e.g., `), calculate its SHA-256 hash, and verify against `HCP_MMP_HASH` in `config.py`. **Depends on**: T009 (for subject IDs) and T004 (for hash constant).
- [X] T011 [US1] **Conditional**: Implement `code/data/preprocess_EEG.py` to download and preprocess **real** resting-state EEG recordings from **OpenNeuro ds004231** (FR-002). **Logic**: 1) Check if T009 found matched EEG data. 2) If YES: Preprocess (MNE band-pass -40Hz, downsample Hz, ICA). 3) If NO (or data missing): **DO NOT EXECUTE**; instead, set a flag `use_simulation=True` in `data/processed/routing_state.json` and skip to T011b. **Output**: `data/processed/eeg/sub-{id}/eeg_cleaned.fif` (if real data exists). **Depends on**: T009.
- [X] T011b [US1] **Simulation**: Implement `code/data/simulate_EEG.py` to generate synthetic resting-state EEG time-series from the preprocessed structural connectomes (T010) using a **linear neural mass model**. **Logic**: 1) Read structural adjacency matrices from T010. 2) Simulate time-series for each node. 3) Project to sensor space (optional) or use node signals directly. 4) Output to `data/processed/eeg/sub-{id}/eeg_simulated.fif`. **MUST** use pinned random seeds. **Depends on**: T010, T009.
- [X] T012 [US1] Implement quality control checks in `code/data/quality_control.py`. **Real Data**: Exclude participants with >30% channels removed after ICA. **Simulated Data**: Exclude participants with disconnected structural graphs. **MUST** calculate and output the proportion of participants with complete pipelines (SC-004). **Depends on**: T010, T011, T011b.
- [X] T013 [US1] Create unified data store script in `code/data/store.py` to save participant-indexed structural matrices and cleaned (real or simulated) EEG time-series (US-1, AC2, AC3). **Depends on**: T010, T011, T011b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data pipeline complete, real or simulated data processed)

---

## Phase 3.5: Sample Size Gate (Blocking)

**Purpose**: Enforce minimum sample size before statistical analysis.

- [X] T029c [US3] **Runtime Gate: Sample Size Check**: Implement the 'Sample Size Check' in `code/main.py` as an explicit **runtime gate** task. **Logic**: 1) Count usable subjects N after QC (T012). 2) Read `N_MIN` from `code/config.py`. 3) If N < N_MIN: **GENERATE** `data/results/insufficient_sample_report.md` documenting the limited sample size and proceed to analysis **IF** N > 0. If N = 0: **HALT** with error. 4) If N >= N_MIN: **CONTINUE** to correlation analysis. 5) Write `data/processed/routing_state.json` with `path: correlation` or `path: limited_sample`, `N: <N>`, `N_MIN: <N_MIN>`, `status: proceed` or `status: limited`. **This task explicitly routes execution** and produces a state file that T019/T020 depend on. **Depends on**: T012.

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2)

**Goal**: Compute canonical structural network metrics and neural avalanche statistics from the processed (real or simulated) data.

**Independent Test**: Can be fully tested by computing metrics for the subset of participants generated in US1 and verifying that output values (degree, clustering, avalanche size) are within expected ranges for human brain networks and neural avalanches.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `code/analysis/metrics.py` to compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX and BCTpy (FR-003). **Depends on**: T010 completion. **Can run in parallel** with T015.
- [X] T015 [US2] Implement `code/analysis/avalanches.py` to detect neural avalanches from **real** EEG (if available) (FR-004). **Logic**: 1) Apply z-score normalization (global mean and std) to the EEG signal. 2) Calculate the 75th percentile amplitude **from the RAW signal distribution** (per-participant) BEFORE z-scoring. 3) Threshold the **z-scored signal** at the value calculated from the RAW signal. **MUST** proceed only if T011 succeeded. **Output**: `data/processed/avalanches/sub-{id}/avalanche_events.csv`. **Depends on**: T011.
- [X] T015b [US2] Implement `code/analysis/avalanches.py` (Simulated Path) to detect neural avalanches from **simulated** EEG (T011b). **Logic**: Same as T015, but applied to `eeg_simulated.fif`. **MUST** use the same z-score and thresholding logic. **Output**: `data/processed/avalanches/sub-{id}/avalanche_events.csv`. **Depends on**: T011b.
- [X] T015c [US2] Implement `code/analysis/aggregate_avalanches.py` to produce a deterministic artifact `data/processed/avalanche_metrics.csv` containing size, duration, and power-law exponents for all participants (Real or Simulated). **Logic**: Read output from T015 and T015b. **Filter**: Exclude participants where power-law fit failed or was rejected by likelihood ratio test (per FR-011, T033). **Depends on**: T015, T015b, T029c (routing state).
- [X] T016 [US2] Implement power-law model fitting in `code/analysis/fitting.py` using `powerlaw` package with model comparison (power-law vs. exponential vs. log-normal) per FR-011.
- [X] T017 [US2] Create export script `code/analysis/export_metrics.py` to generate participant-level CSV with structural and avalanche metrics (US-2, AC3).
- [X] T018 [P] [US2] Implement unit tests in `tests/test_metrics.py` (e.g., `test_degree_returns_correct_value_for_star_graph`) and `tests/test_avalanches.py` (e.g., `test_avalanche_detection_handles_flat_signal`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (metrics computed)

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction for multiple comparisons and threshold sensitivity.

**Independent Test**: Can be fully tested by running the association analysis on the computed metrics and verifying that correlation coefficients, p-values, and sensitivity sweep results are reproducible and frame findings as associational.

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/analysis/stats.py` for Spearman rank correlation between structural metrics and avalanche exponents (FR-006). **Depends on**: T014 and T015c. **Must check** `routing_state.json` from T029c before running.
- [X] T020 [US3] Implement non-parametric permutation test (shuffles) and family-wise error correction using **max-t permutation** method (FR-007) in `code/analysis/stats.py`. **Depends on**: T019 completion.
- [X] T021 [US3] Implement collinearity diagnostics (VIF) in `code/analysis/stats.py` with flagging logic for VIF ≥ 5 (FR-009). **MUST** write a flag to `data/results/collinearity_status.json` with key `high_collinearity: true/false` and `vif_value: <float>`. **MUST** ensure this flag is consumed by T023 to suppress claims. **Depends on**: T019.
- [X] T022 [US3] Implement sensitivity analysis sweep across thresholds {0.70, 0.75, 0.80} in `code/analysis/sensitivity.py` (FR-008). **MUST** use hardcoded Spec values, not config file. **Depends on**: T019.
- [X] T023 [US3] Create final report generator `code/analysis/report.py` ensuring all findings are framed as associational (FR-010). **MUST** read `data/results/collinearity_status.json` from T021 and suppress any claims of independent predictive effects if `high_collinearity` is true. **Depends on**: T021.
- [X] T024 [P] [US3] Implement integration tests in `tests/test_stats.py` using a mock dataset of a small cohort of participants with known ground-truth correlations; assert p_value < 0.05 for known correlation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Compliance (Addressing Review Concerns)

**Goal**: Resolve specific gaps identified in the specification vs. plan alignment and ensure strict adherence to data integrity rules. **MUST** run before Phase 7 (Polish) and T029 (Validation).

### Implementation for Revision

- [X] T031 [US3] **Standardize Sensitivity Sweep Range**: Update `code/analysis/sensitivity.py` to use hardcoded threshold values `{0.70, 0.75, 0.80}` from `code/config.py` (defined in T004). **MUST NOT** load from `research_phase_config.json`. **Rationale**: SC-002 requires measuring stability across specific thresholds; "deferred" in code leads to inconsistent execution, but the Spec defines the values.
- [X] T032 [US3] **Enforce Associational Framing**: Add a validation step in `code/analysis/report.py` that scans the generated text for causal keywords (e.g., "causes", "drives", "leads to") and raises a `RuntimeError` if found, forcing the user to rephrase. **Rationale**: FR-010 and US-3 explicitly forbid causal claims; automated enforcement ensures compliance.
- [X] T033 [US2] **Validate Power-Law Fit Convergence**: Update `code/analysis/fitting.py` to explicitly handle the `powerlaw` package's convergence failure by logging a specific error code and excluding the participant from the correlation matrix, rather than silently returning NaN. **Rationale**: FR-011 requires model comparison; silent failures corrupt the statistical association in US-3.
- [X] T027a [US3] **Optimize Permutation Loop**: Profile `code/analysis/stats.py` and optimize the permutation loop using multiprocessing and **chunked processing** to ensure total runtime ≤ 6 hours on CPU-only runner for **N=len(participants)** (SC-006). **MUST** dynamically load and adapt to the actual number of subjects found in `data/processed` (not hardcoded N=50).
- [X] T027b [US3] **Enforce Runtime Limit**: Implement a timeout wrapper in `code/main.py` that enforces a hard limit on the entire pipeline execution. If exceeded, gracefully terminate and generate a `runtime_timeout_report.md`. **Depends on**: T027a.

**Checkpoint**: Revision tasks complete; logic for validation is now in place.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] **Add Unit Test for Disconnected Graphs and Edge Cases**: Implement `tests/test_edge_cases.py` to verify that `metrics.py` and `quality_control.py` correctly handle and exclude participants with disconnected structural graphs (sparse connectivity) and that `fitting.py` correctly handles power-law convergence failures. **Depends on**: T010, T012, T033.
- [X] T036 [P] [US3] **Add Unit Test for Null Result Protocol**: Implement `tests/test_null_result.py` to verify that the `main.py` logic correctly generates the `insufficient_sample_report.md` when N < N_MIN (but N > 0), ensuring the routing state file is written correctly. **Depends on**: T029c.
- [X] T037 [P] [US3] **Add Unit Test for Causal Framing Validator**: Implement `tests/test_report_framing.py` to verify that `report.py` correctly raises a `RuntimeError` when causal keywords ("causes", "drives") are detected in the output text. **Depends on**: T032.
- [X] T038 [P] [US2] **Add Unit Test for Power-Law Convergence Handling**: Implement `tests/test_fitting.py` to verify that `fitting.py` correctly logs a specific error code and excludes a participant when `powerlaw` convergence fails, rather than returning NaN. **Depends on**: T033.
- [X] T039 [P] [US3] **Add Unit Test for Sensitivity Sweep**: Implement `tests/test_sensitivity.py` to verify that `sensitivity.py` correctly uses the hardcoded thresholds {0.70, 0.75, 0.80} and produces consistent results. **Depends on**: T031.
- [X] T041 [P] [US3] **Add Unit Test for Streaming Data Handling**: Implement `tests/test_streaming.py` to verify that `download.py` correctly streams datasets larger than 100MB without exceeding memory limits, ensuring the logic in T009 functions as specified for large real datasets. **Depends on**: T009.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 metric output and T029c gate**

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
- **T009** (download) must implement the full spec-authorized logic (ds004230 for dMRI, ds004231 for EEG) with a fallback to simulation if unmatched.
- **T011** (Real EEG) is **CONDITIONAL**. It runs after T009 completes. If T011 fails to find data, it triggers T011b (Simulation). **If successful, it proceeds to T015.**
- **T011b** (Simulated EEG) is the **ALTERNATIVE PATH** if T011 fails. It proceeds to T015b.
- **T015** (Real Avalanches) and **T015b** (Simulated Avalanches) are **UNCONDITIONAL** (given T011 or T011b success).
- **T015c** (Unified Metrics) produces the deterministic artifact for T019.
- **T019** (stats.py) **MUST** run after T014 and T015c.
- **T020** (permutation) **MUST** run after T019.
- **T029c** (Runtime Gate) is now in Phase 3.5, **before** T019/T020.
- **T035** (Streaming) is required if the primary dataset is large. **NO FALLBACKS**. **MUST** stream unconditionally.
- **T035** logic has been merged into T009 to ensure streaming is implemented as part of the core download logic.

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
3. Complete Phase 3: User Story 1 (Real Data OR Simulation)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Real Data OR Simulation) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Real Data OR Simulation)
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
- **Real OR Simulated Data**: The Plan states simulation is required if real data is unavailable. T011 and T011b handle both paths. **NO SIMULATION IF REAL DATA EXISTS** (T011 takes precedence).
- **Fallback Logic**: T009 implements the full spec-authorized logic (ds004230 -> ds004231 -> Simulation if unmatched). **NO FALLBACKS** to unauthorized datasets.
- **Revision Protocol**: Tasks T031-T033 are mandatory to address specific reviewer concerns regarding data source verification, failure handling, and statistical rigor. These must be completed before the project is considered "Clean" and before Phase 7 (Polish) and T029 (Validation).
- **Validation Logic**: T029c handles the routing logic (Correlation vs Limited Sample) as a valid completion, avoiding the logical contradiction of a single task asserting both. T029c produces `routing_state.json`.
- **Documentation Path**: All documentation must reside in `specs/001-network-structure-avalanche-dynamics/` per the Plan. **`docs/` is deprecated**.
- **Removed T026**: The vague "refactor for modularity" task was removed as the Plan already defines the modular structure.
- **Removed T034**: The "GPU Offload" task was removed as it contradicts the Plan's "No GPU" constraint. **This removal resolves the executability concern for T034.**
- **T035 Merged**: Streaming logic is now integrated into T009 with a size check (>100MB).
- **T030 Merged**: T030 was merged into T011b (removed). Logging and hashing logic is now intrinsic to T004.
- **T011 Logic**: T011 is conditional. If real data missing, T011b runs. **If successful, it proceeds to T015/T015b.**
- **T015 Logic**: T015 and T015b explicitly define z-score normalization parameters and the correct thresholding logic (z-score signal, then threshold at 75th percentile of RAW signal).
- **Config Logic**: T031 now uses hardcoded Spec values; no config file dependency for thresholds.
- [X] T036 [P] [US3] **Add Unit Test for Null Result Protocol**: Implement `tests/test_null_result.py` to verify that the `main.py` logic correctly generates the `insufficient_sample_report.md` when N < N_MIN (but N > 0), ensuring the routing state file is written correctly. **Depends on**: T029c.
- [X] T037 [P] [US3] **Add Unit Test for Causal Framing Validator**: Implement `tests/test_report_framing.py` to verify that `report.py` correctly raises a `RuntimeError` when causal keywords ("causes", "drives") are detected in the output text. **Depends on**: T032.
- [X] T038 [P] [US2] **Add Unit Test for Power-Law Convergence Handling**: Implement `tests/test_fitting.py` to verify that `fitting.py` correctly logs a specific error code and excludes a participant when `powerlaw` convergence fails, rather than returning NaN. **Depends on**: T033.
- [X] T039 [P] [US3] **Add Unit Test for Sensitivity Sweep**: Implement `tests/test_sensitivity.py` to verify that `sensitivity.py` correctly uses the hardcoded thresholds {0.70, 0.75, 0.80} and produces consistent results. **Depends on**: T031.