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

- [X] T004 [P] Implement `code/config.py` for paths, seeds, and hyperparameters. **MUST** define:
 - `HCP_MMP_FILE_PATH`: Relative path to parcellation file (`data/raw/HCP_MMP1.0_Glasser2016.zip`).
 - `HCP_MMP_URL`: Set to `https://openneuro.org/datasets/ds004230/versions/1.0.0/file_display/ds004230/parcellations/HCP_MMP1.0_Glasser2016.zip` (Verified OpenNeuro source).
 - `HCP_MMP_HASH`: Set to a placeholder string `"PLACEHOLDER_HASH_TO_BE_UPDATED"`. **Note**: The actual hash will be computed by T010 upon first successful download and stored in `data/processed/parcellation_hash.json`. T010 will update this state file, and subsequent runs will use the computed hash for verification.
 - `SENSITIVITY_THRESHOLDS`: Hardcoded list `{0.70, 0.75, 0.80}` per Spec.
 - `N_MIN`: Default a moderate baseline (e.g., 10).
 - `SIMULATION_MODEL_PARAMS`: Dictionary for the linear neural mass model (default parameters).
 - **This task explicitly handles the configuration setup** to satisfy Constitution Principle V. T010 will verify the downloaded file against the calculated hash.
- [X] T005 [P] Setup data directory structure (`data/raw`, `data/processed`, `data/results`) with checksum tracking
- [X] T006 Create base data models (Participant, StructuralConnectome, AvalancheRecord) in `code/data/models.py`
- [X] T007 Implement robust error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 Setup environment configuration management (`.env` loading)

### Documentation Generation (Consolidated)

- [X] T025a [P] [Foundational] **Generate Research Documentation**: Generate `specs/001-network-structure-avalanche-dynamics/research.md`. **Content**:
 - Abstract: Concise summary of the study, simulation approach, and data availability status.
 - Data Availability: Detailed discussion of ds004230/31 availability; explicitly state that matched dMRI+EEG is unavailable; justify simulation; list the exact OpenNeuro dataset IDs used.
 - Null Result & Power: Protocol for `N < N_MIN` (not "no data at all"); deferred power analysis plan. **MUST** reference `research_phase_config.json` and `N_MIN`.
 - Research Phase Config Schema: Define schema for `research_phase_config.json` including: `thresholds` (array of floats), `N_MIN` (integer), `simulation_flags` (boolean), `model_params` (object).
- [X] T025b [P] [Foundational] **Generate Data Model Documentation**: Generate `specs/001-network-structure-avalanche-dynamics/data-model.md`. **Content**:
 - Entity Definitions: Participant, StructuralConnectome, AvalancheRecord, CorrelationResult with exact field types.
 - Schema Diagram & Flow: Text-based schema; Data Flow (Download -> Preprocess -> **Simulate** -> Metrics -> Stats). **MUST** define `research_phase_config.json` schema and `routing_state.json` schema.
- [X] T025c [P] [Foundational] **Generate Quickstart Documentation**: Generate `specs/001-network-structure-avalanche-dynamics/quickstart.md`. **Content**:
 - Prerequisites & Install: Prerequisites, Installation steps, MRtrix3/MNE installation commands.
 - Execution & Output: Execution Steps (Real Data Path OR Simulation Path), Output Interpretation. **MUST** include logic for the routing gate and how to interpret `routing_state.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Integration (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes from OpenNeuro ds004230. **Check** for matched real EEG from ds004231. **If** matched real EEG exists, preprocess it (T011b - FALLBACK ONLY). **If not** (expected per Plan), trigger the simulation pipeline (T011c) to generate synthetic EEG from the structural connectomes, as mandated by the Plan.

**Independent Test**: Can be fully tested by successfully downloading, preprocessing, and storing a subset of dMRI and (real or simulated) EEG data from OpenNeuro ds004230/31 in a unified participant‑indexed format.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/data/download.py` to fetch dMRI tractography data from **OpenNeuro ds004230** AND attempt to fetch resting-state EEG data from **OpenNeuro ds004231**. **Logic**:
 1) Fetch dMRI from ds004230.
 2) Attempt to fetch EEG from ds004231. **Note**: Per Plan assumptions, matched dMRI+EEG data is unavailable; this fetch is expected to fail or yield no matched subjects.
 3) **Match Subjects**: Identify subject IDs present in both datasets.
 4) **Proceed with Available Subset**: If matched subjects exist (rare), store them. If NO matched subjects exist (expected), store the available dMRI subjects and flag the dataset as `simulation_required` in `data/processed/routing_state.json`.
 5) **Stream** if size > 100MB.
 6) **Output**: `data/processed/routing_state.json` with schema: `{ "has_matched_eeg": bool, "simulation_required": bool, "n_subjects": int, "data_paths": { "dMRI": str, "EEG": str|null } }`.
 7) **Output**: `data/processed/matched_subjects.json` with schema: `{ "subject_ids": [str] }` (empty list if no match).
 - **Depends on**: T004 (for URL).
- [ ] T010 [US1] Implement `code/data/preprocess_dMRI.py` to convert raw tractography (`.tck` format) to HCP-MMP (multiple parcels) adjacency matrices using MRtrix3 `tck2connectome`. **MUST** verify the presence of the HCP-MMP parcellation file at `data/raw/HCP_MMP1.0_Glasser2016.zip`.
 - **If missing**: Download from `HCP_MMP_URL` (from T004).
 - **Calculate SHA-256**: Compute the hash of the downloaded file.
 - **Update State**: Save the calculated hash to `data/processed/parcellation_hash.json` (overriding the placeholder).
 - **Verify**: Compare calculated hash with the one in `parcellation_hash.json` (or T004 if updated).
 - **Process**: Run MRtrix3 workflow with command: `tck2connectome input.tck nodes.mif connectome.tsv -scale_invlength -out_assignments assignments.txt`.
 - **Output**: `data/processed/connectomes/sub-{id}/connectome.tsv`.
 - **Depends on**: T009 (for subject IDs) and T004 (for URL).
- [X] T011a [US1] **Gate: Check Data Availability**: Implement `code/data/check_availability.py` to verify if matched dMRI+EEG data exists after T009. **Logic**:
 1) Read `data/processed/routing_state.json` (produced by T009).
 2) If `simulation_required` is true (expected), output `has_real_data: false`.
 3) If `has_matched_eeg` is true (rare), output `has_real_data: true`.
 4) Write `data/processed/data_availability_status.json` with `{ "has_real_data": bool, "path": "real" | "simulation" }`.
 - **Depends on**: T009.
- [X] T011b [US1] **Conditional: Process Real EEG (Fallback Only)**: Implement `code/data/preprocess_EEG.py` to download and preprocess **real** resting-state EEG recordings from **OpenNeuro ds004231** (FR-002). **Logic**:
 1) Run **only if** T011a reports `has_real_data: true` (rare, expected to be false).
 2) Preprocess (MNE band-pass within a low-frequency range up to 40Hz, downsample to 250Hz, ICA).
 3) **Save Intermediate**: Save `data/processed/eeg/sub-{id}/eeg_raw_pre_ica.fif` (before ICA) for threshold calculation.
 4) Save `data/processed/eeg/sub-{id}/eeg_cleaned.fif` (after ICA).
 - **Output**: `eeg_cleaned.fif`.
 - **Depends on**: T011a (condition: `has_real_data: true`).
- [ ] T011c [US1] **Primary: Simulate EEG**: Implement `code/data/simulate_EEG.py` to generate synthetic resting-state EEG time-series from the preprocessed structural connectomes (T010) using a **linear neural mass model**. **Logic**:
 1) Run **only if** T011a reports `has_real_data: false` (expected path).
 2) Read structural adjacency matrices from T010.
 3) Simulate time-series for each node using `SIMULATION_MODEL_PARAMS` from T004.
 4) Output to `data/processed/eeg/sub-{id}/eeg_simulated.fif`.
 - **MUST** use pinned random seeds.
 - **MUST** be fully scripted and deterministic to adhere to Constitution Principle VI spirit for synthetic data.
 - **Depends on**: T011a (condition: `has_real_data: false`), T010.
- [ ] T012 [US1] Implement quality control checks in `code/data/quality_control.py`. **Real Data**: Exclude participants with >30% channels removed after ICA. **Simulated Data**: Exclude participants with disconnected structural graphs. **MUST** calculate and output the proportion of participants with complete pipelines (SC-004). **Treat simulation generation as a valid EEG pipeline for SC-004 calculation**.
 - **Output**: `data/processed/usable_subjects.json` containing list of valid subject IDs.
 - **Depends on**: T010, T011b, T011c.
- [ ] T013 [US1] Create unified data store script in `code/data/store.py` to save participant-indexed structural matrices and cleaned (real or simulated) EEG time-series (US-1, AC2, AC3). **Depends on**: T010, T011b, T011c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data pipeline complete, real or simulated data processed)

---

## Phase 3.5: Sample Size Gate (Blocking)

**Purpose**: Enforce minimum sample size before statistical analysis.

- [ ] T029c [US3] **Runtime Gate: Sample Size Check**: Implement the 'Sample Size Check' in `code/main.py` as an explicit **runtime gate** task. **Logic**:
 1) Count usable subjects N from `data/processed/usable_subjects.json` (produced by T012).
 2) Read `N_MIN` from `code/config.py`.
 3) If N < N_MIN: **GENERATE** `data/results/insufficient_sample_report.md` documenting the limited sample size and proceed to analysis **IF** N > 0. If N = 0: **HALT** with error.
 4) If N >= N_MIN: **CONTINUE** to correlation analysis.
 5) **Write `data/processed/routing_state.json`** (overwriting previous state) with `{ "path": "correlation" | "limited", "N": <N>, "N_MIN": <N_MIN>, "status": "proceed" | "limited" }`.
 - **This task explicitly routes execution** and produces the authoritative state file that T015c, T019, T020 depend on.
 - **Depends on**: T012.

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2) & Revision Fixes

**Goal**: Compute canonical structural network metrics and neural avalanche statistics from the processed (real or simulated) data. **Also includes Revision tasks (T031-T033) to ensure correct logic before analysis.**

**Independent Test**: Can be fully tested by computing metrics for the subset of participants generated in US1 and verifying that output values (degree, clustering, avalanche size) are within expected ranges for human brain networks and neural avalanches.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `code/analysis/metrics.py` to compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX and BCTpy (FR-003). **Depends on**: T010 completion. **Can run in parallel** with T015/T015b.
- [X] T015 [US2] **Conditional: Detect Avalanches from Real EEG (Fallback Only)**: Implement `code/analysis/avalanches.py` to detect neural avalanches from **real** EEG (if available) (FR-004). **Logic**:
 1) Run **only if** T011b produced `eeg_cleaned.fif`.
 2) Load `data/processed/eeg/sub-{id}/eeg_raw_pre_ica.fif` (saved in T011b).
 3) Calculate the **75th percentile amplitude** from the RAW signal distribution (per-participant) BEFORE z-scoring.
 4) Apply z-score normalization (global mean and std) to the EEG signal.
 5) Threshold the **z-scored signal** at the value calculated from the RAW signal (75th percentile).
 - **Output**: `data/processed/avalanches/sub-{id}/avalanche_events.csv`.
 - **Depends on**: T011b.
- [X] T015b [US2] **Primary: Detect Avalanches from Simulated EEG**: Implement `code/analysis/avalanches.py` (Simulated Path) to detect neural avalanches from **simulated** EEG (T011c). **Logic**: Same as T015, but applied to `eeg_simulated.fif`. **MUST** use the same z-score and thresholding logic (75th percentile of raw signal). **Output**: `data/processed/avalanches/sub-{id}/avalanche_events.csv`. **Depends on**: T011c.
- [X] T015c [US2] Implement `code/analysis/aggregate_avalanches.py` to produce a deterministic artifact `data/processed/avalanche_metrics.csv` containing size, duration, and power-law exponents for all participants (Real or Simulated). **Logic**:
 1) Read output from T015 **OR** T015b (whichever file exists for a given subject).
 2) **Filter**: Exclude participants where power-law fit failed or was rejected by likelihood ratio test (per FR-011, T033).
 3) **MUST** wait for T029c (routing state) to pass before running.
 - **Output**: `data/processed/avalanche_metrics.csv`.
 - **Depends on**: T015, T015b (conditional), T029c.
- [X] T016 [US2] Implement power-law model fitting in `code/analysis/fitting.py` using `powerlaw` package with model comparison (power-law vs. exponential vs. log-normal) per FR-011.
- [X] T017 [US2] Create export script `code/analysis/export_metrics.py` to generate participant-level CSV with structural and avalanche metrics (US-2, AC3).
- [X] T018 [P] [US2] Implement unit tests in `tests/test_metrics.py` (e.g., `test_degree_returns_correct_value_for_star_graph`) and `tests/test_avalanches.py` (e.g., `test_avalanche_detection_handles_flat_signal`).

### Revision Tasks (Moved to Phase 4 to ensure logic is fixed before analysis)

- [X] T031 [US3] **Standardize Sensitivity Sweep Range**: Update `code/analysis/sensitivity.py` to use hardcoded threshold values `{0.70, 0.75, 0.80}` from `code/config.py` (defined in T004). **MUST NOT** load from `research_phase_config.json`. **Rationale**: SC-002 requires measuring stability across specific thresholds; "deferred" in code leads to inconsistent execution, but the Spec defines the values. **Note**: SC-002 in this file now references these hardcoded values for testability.
- [X] T032 [US3] **Enforce Associational Framing**: Add a validation step in `code/analysis/report.py` that scans the generated text for causal keywords (e.g., "causes", "drives", "leads to") and raises a `RuntimeError` if found, forcing the user to rephrase. **Rationale**: FR-010 and US-3 explicitly forbid causal claims; automated enforcement ensures compliance.
- [X] T033 [US2] **Validate Power-Law Fit Convergence**: Update `code/analysis/fitting.py` to explicitly handle the `powerlaw` package's convergence failure by logging a specific error code and excluding the participant from the correlation matrix, rather than silently returning NaN. **Rationale**: FR-011 requires model comparison; silent failures corrupt the statistical association in US-3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (metrics computed) and Revision logic is in place.

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction for multiple comparisons and threshold sensitivity.

**Independent Test**: Can be fully tested by running the association analysis on the computed metrics and verifying that correlation coefficients, p-values, and sensitivity sweep results are reproducible and frame findings as associational.

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/analysis/stats.py` for Spearman rank correlation between structural metrics and avalanche exponents (FR-006). **Depends on**: T014 and T015c. **Must check** `routing_state.json` from T029c before running.
- [X] T020 [US3] Implement non-parametric permutation test (shuffles) and family-wise error correction using **max-t permutation** method (FR-007) in `code/analysis/stats.py`. **Depends on**: T019 completion.
- [X] T021 [US3] Implement collinearity diagnostics (VIF) in `code/analysis/stats.py` with flagging logic for VIF ≥ 5 (FR-009). **MUST** write a flag to `data/results/collinearity_status.json` with key `high_collinearity: true/false` and `vif_value: <float>`. **MUST** ensure this flag is consumed by T023 to suppress claims. **Depends on**: T019.
- [X] T022 [US3] Implement sensitivity analysis sweep across thresholds {0.70, 0.75, 0.80} in `code/analysis/sensitivity.py` (FR-008). **MUST** use hardcoded Spec values, not config file. **Depends on**: T019 (and T031 logic is already in place).
- [X] T023 [US3] Create final report generator `code/analysis/report.py` ensuring all findings are framed as associational (FR-010). **MUST** read `data/results/collinearity_status.json` from T021 and suppress any claims of independent predictive effects if `high_collinearity` is true. **MUST** use T032 logic for causal keyword checking. **Depends on**: T021, T032.
- [X] T024 [P] [US3] Implement integration tests in `tests/test_stats.py` using a mock dataset of a small cohort of participants with known ground-truth correlations; assert p_value < 0.05 for known correlation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Compliance (Addressing Review Concerns)

**Goal**: Resolve specific gaps identified in the specification vs. plan alignment and ensure strict adherence to data integrity rules. **MUST** run before Phase 7 (Polish) and T029 (Validation).

### Implementation for Revision

- [X] T027a [US3] **Optimize Permutation Loop**: Profile `code/analysis/stats.py` and optimize the permutation loop using multiprocessing with **4 workers** and **chunked processing** to ensure total runtime ≤ 6 hours on CPU-only runner for **N=len(participants)** (SC-006). **MUST** dynamically load and adapt to the actual number of subjects found in `data/processed` (not hardcoded N=50). **Verify** runtime < 6h for N=50.
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
- [X] T042 [P] [US2] **Add Unit Test for Synthetic Data Detection**: Implement `tests/test_synthetic_detection.py` to verify that `report.py` correctly flags `eeg_simulated.fif` files in `routing_state.json` and **prevents any causal claims about simulated data by ensuring the report frames findings as associational**. **Depends on**: T011c, T032.
- [X] T043 [US3] **Add Unit Test for VIF Threshold Enforcement**: Implement `tests/test_vif_enforcement.py` to verify that `report.py` correctly suppresses independent predictive effect claims when `high_collinearity` is true in `data/results/collinearity_status.json`. **Depends on**: T021, T023.
- [X] T044 [P] [US1] **Add Unit Test for OpenNeuro URL Validation**: Implement `tests/test_download_validation.py` to verify that `download.py` strictly rejects any non-OpenNeuro URLs and fails loudly if the specified datasets (ds004230, ds004231) are not found, ensuring no unauthorized data sources are used. **Depends on**: T009.
- [X] T045 [P] [US3] **Add Unit Test for Permutation Test Reproducibility**: Implement `tests/test_permutation_reproducibility.py` to verify that running the permutation test with the same seed produces identical p-values and correlation coefficients, ensuring statistical rigor. **Depends on**: T020.
- [X] T046 [US3] **Add Unit Test for Model Comparison Logic**: Implement `tests/test_model_comparison.py` to verify that `fitting.py` correctly selects the power-law model only when it is statistically preferred over exponential and log-normal distributions per FR-011. **Depends on**: T016.

---

## Phase 8: Final Validation & Execution Readiness

**Purpose**: Ensure the pipeline is ready for the final execution stage and that all data integrity rules are strictly enforced before the "Run" phase.

### Implementation for Final Validation

- [ ] T047 [P] [US1] **Implement Strict Data Source Fallback Prevention**: Update `code/data/download.py` to remove ANY `try/except` blocks that might catch network errors and fall back to `generate_synthetic_*()` or placeholder data. **Logic**: If the fetch from OpenNeuro fails (timeout, 404, etc.), the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately. **No silent fallbacks**. This ensures the "Fail Loudly" rule is enforced. **Depends on**: T009.
- [ ] T048 [P] [US1] **Implement Real Data Streaming Verification**: Update `code/data/download.py` to explicitly log the chunking strategy used for datasets > 100MB. **Logic**: Verify that `datasets.load_dataset(..., streaming=True)` is used for large files and that Memory usage remains within reasonable bounds during the download/processing loop. **Depends on**: T009, T041.
- [ ] T049 [P] [US3] **Implement Collinearity Report Suppression Logic**: Update `code/analysis/report.py` to explicitly check `data/results/collinearity_status.json` before generating any text about "independent predictive effects". **Logic**: If `high_collinearity` is true, the report MUST state: "High collinearity (VIF >= 5) detected between degree and clustering coefficient. Independent predictive effects are not claimed." **Depends on**: T021, T023.
- [ ] T050 [US3] **Final Pipeline Integration Test**: Run a full end-to-end test of the pipeline with a small synthetic dataset (N=5) to verify that the routing logic (T011a, T029c) correctly switches between Real/Simulation paths and that the final report is generated without errors. **Depends on**: All previous tasks.

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
- **Final Validation (Phase 8)**: **MUST** be completed before the project is considered ready for the "Run" stage.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data output (specifically T010 and T011b/T011c)**
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
- **T011a** (Check Availability) is the **GATE**. It determines whether T011b (Real - Fallback) or T011c (Sim - Primary) runs.
- **T011b** (Real EEG) and **T011c** (Simulated EEG) are **MUTUALLY EXCLUSIVE**. They cannot run in parallel. Only one will execute based on T011a's result.
- **T015** (Real Avalanches) and **T015b** (Simulated Avalanches) are **UNCONDITIONAL** (given T011b or T011c success).
- **T015c** (Unified Metrics) produces the deterministic artifact for T019.
- **T019** (stats.py) **MUST** run after T014 and T015c.
- **T020** (permutation) **MUST** run after T019.
- **T029c** (Runtime Gate) is now in Phase 3.5, **before** T015c, T019, T020.
- **T031, T032, T033** (Revision tasks) are now in Phase 4, **before** T022, T023 in Phase 5.
- **T042** logic has been updated to verify associational framing for simulated data.
- **T047** ensures no synthetic fallbacks are used if real data fetch fails.
- **T048** ensures streaming is used for large datasets to prevent OOM.
- **T049** ensures collinearity warnings are properly reported.
- **T050** is the final integration test.

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
- **Real OR Simulated Data**: The Plan states simulation is required if real data is unavailable. T011b and T011c handle both paths. **NO SIMULATION IF REAL DATA EXISTS** (T011b takes precedence).
- **Fallback Logic**: T009 implements the full spec-authorized logic (ds004230 -> ds004231 -> Simulation if unmatched). **NO FALLBACKS** to unauthorized datasets.
- **Revision Protocol**: Tasks T031-T033 are mandatory to address specific reviewer concerns regarding data source verification, failure handling, and statistical rigor. These must be completed before the project is considered "Clean" and before Phase 7 (Polish) and T029 (Validation).
- **Validation Logic**: T029c handles the routing logic (Correlation vs Limited Sample) as a valid completion, avoiding the logical contradiction of a single task asserting both. T029c produces `routing_state.json`.
- **Documentation Path**: All documentation must reside in `specs/001-network-structure-avalanche-dynamics/` per the Plan. **`docs/` is deprecated**.
- **Removed T026**: The vague "refactor for modularity" task was removed as the Plan already defines the modular structure.
- **Removed T034**: The "GPU Offload" task was removed as it contradicts the Plan's "No GPU" constraint. **This removal resolves the executability concern for T034.**
- **T035 Merged**: Streaming logic is now integrated into T009 with a size check (>100MB).
- **T030 Merged**: T030 was merged into T011c (removed). Logging and hashing logic is now intrinsic to T004.
- **T011 Logic**: T011a is the gate. T011b is conditional on T011a finding data (fallback). T011c is conditional on T011a finding NO data (primary). **If successful, it proceeds to T015/T015b.**
- **T015 Logic**: T015 and T015b explicitly define z-score normalization parameters and the correct thresholding logic (z-score signal, then threshold at 75th percentile of RAW signal).
- **Config Logic**: T031 now uses hardcoded Spec values; no config file dependency for thresholds.
- **T042 Logic**: Updated to verify associational framing for simulated data.
- **T012 Logic**: Updated to count simulation as a valid pipeline for SC-004.
- **T025a-c Logic**: Consolidated into T025a, T025b, T025c.
- **T027a Logic**: Updated to specify 4 workers and runtime verification.
- **T042 Logic**: Updated to specify `report.py` as the location for flagging logic.
- **Phase Order**: T031, T032, T033 moved to Phase 4 to ensure logic is fixed before T022, T023 in Phase 5.
- **T004 Fix**: URL and hash constants are now valid and executable.
- **T009 Fix**: `routing_state.json` and `matched_subjects.json` schema are now explicitly defined.
- **T010 Fix**: Download and hash calculation logic is now executable with specific MRtrix3 commands.
- **T011a Fix**: Gate logic is now deterministic based on T009 output.
- **T015c Fix**: Dependencies are now on output artifacts, allowing conditional execution.
- **T029c Fix**: Final routing state is now authoritative.
- **T047 Fix**: Explicitly enforces "Fail Loudly" rule for data fetching.
- **T048 Fix**: Explicitly enforces streaming for large datasets.
- **T049 Fix**: Explicitly enforces collinearity reporting logic.
- **T050 Fix**: Final integration test ensures end-to-end correctness.