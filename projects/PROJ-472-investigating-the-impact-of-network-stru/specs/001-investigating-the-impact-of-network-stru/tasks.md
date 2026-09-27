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
 - `HCP_MMP_HASH`: Set to `"PENDING_HASH"` (a sentinel value). **Note**: T010 will compute the actual hash upon first download and update this value in `data/processed/parcellation_hash.json`. The pipeline will verify against this file.
 - `SENSITIVITY_THRESHOLDS`: Hardcoded list `{0.70, 0.75, 0.80}`. **Rationale**: SC-002 lists these as "[deferred]" in the spec; this task resolves the deferred status as a design decision for the "Pipeline Validation Study" to enable deterministic testing.
 - `N_MIN`: Default a moderate baseline (e.g., 10).
 - `SIMULATION_MODEL_PARAMS`: Dictionary for the linear neural mass model (default parameters).
 - **This task explicitly handles the configuration setup** to satisfy Constitution Principle V.
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

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes from OpenNeuro ds004230 AND resting-state EEG from OpenNeuro ds004231 as SEPARATE datasets. **NO MATCHING** is attempted as per Plan. **Trigger** the simulation pipeline (T011c) for pipeline continuity and T011d for unit test ground truth.

**Independent Test**: Can be fully tested by successfully downloading, preprocessing, and storing a subset of dMRI and (separate) EEG data from OpenNeuro ds004230/31 in a unified participant‑indexed format (with N=0 matched subjects).

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/data/download.py` to fetch dMRI tractography data from **OpenNeuro ds004230** AND resting-state EEG data from **OpenNeuro ds004231** as **SEPARATE** datasets. **Logic**:
 1) Fetch dMRI from ds004230.
 2) Fetch EEG from ds004231.
 3) **DO NOT** attempt to match subjects. **Record** N=0 matched subjects.
 4) **Flag** the dataset as `simulation_required` in `data/processed/routing_state.json` immediately.
 5) **Stream** if size > 100MB.
 6) **Output**: `data/processed/routing_state.json` with schema: `{ "has_matched_eeg": false, "simulation_required": true, "n_subjects_dMRI": int, "n_subjects_EEG": int, "data_paths": { "dMRI": str, "EEG": str } }`.
 7) **Output**: `data/processed/matched_subjects.json` with schema: `{ "subject_ids": [] }` (empty list).
 - **Depends on**: T004 (for URL).
- [X] T010 [US1] Implement `code/data/preprocess_dMRI.py` to convert raw tractography (`.tck` format) to HCP-MMP (multiple parcels) adjacency matrices using MRtrix3 `tck2connectome`. **MUST** verify the presence of the HCP-MMP parcellation file at `data/raw/HCP_MMP1.0_Glasser2016.zip`.
 - **Input**: Raw tractography files from `data/raw/ds004230/sub-*/dwi/*.tck`.
 - **If missing**: Download from `HCP_MMP_URL` (from T004) or locate tractography files.
 - **Calculate SHA-256**: Compute the hash of the downloaded file.
 - **Update State**: Save the calculated hash to `data/processed/parcellation_hash.json` (overriding the "PENDING_HASH" sentinel).
 - **Verify**: Compare calculated hash with the one in `parcellation_hash.json`.
 - **Process**: Run MRtrix3 workflow with command: `tck2connectome input.tck nodes.mif connectome.tsv -scale_invlength -out_assignments assignments.txt`.
 - **Output**: `data/processed/connectomes/sub-{id}/connectome.tsv`.
 - **Depends on**: T009 (for subject IDs) and T004 (for URL).
- [X] T011a [US1] **Gate: Check Data Availability**: Implement `code/data/check_availability.py` to verify the state after T009. **Logic**:
 1) Read `data/processed/routing_state.json` (produced by T009).
 2) Since `has_matched_eeg` is always false (per Plan), output `has_real_data: false`.
 3) Write `data/processed/data_availability_status.json` with `{ "has_real_data": false, "path": "simulation" }`.
 - **Depends on**: T009.
- [X] T011b [US1] **Primary: Process Real EEG**: Implement `code/data/preprocess_EEG.py` to download and preprocess **real** resting-state EEG recordings from **OpenNeuro ds004231** (FR-002). **Logic**:
 1) Run **only if** T011a reports `has_real_data: true` (Expected: False, but kept for robustness).
 2) Preprocess (MNE band-pass within a low-frequency range up to 40 Hz, downsample to 250Hz, ICA).
 3) **Save Intermediate**: Save `data/processed/eeg/sub-{id}/eeg_raw_pre_ica.fif` (before ICA) for threshold calculation.
 4) Save `data/processed/eeg/sub-{id}/eeg_cleaned.fif` (after ICA).
 - **Output**: `eeg_cleaned.fif`.
 - **Depends on**: T011a (condition: `has_real_data: true`).
- [X] T011c [US1] **Pipeline Continuity: Simulate EEG**: Implement `code/data/simulate_EEG.py` to generate synthetic resting-state EEG time-series from the preprocessed structural connectomes (T010) using a **linear neural mass model**. **Logic**:
 1) Run **only if** T011a reports `has_real_data: false` (Expected path).
 2) Read structural adjacency matrices from T010.
 3) Simulate time-series for each node using `SIMULATION_MODEL_PARAMS` from T004.
 4) Output to `data/processed/eeg/sub-{id}/eeg_simulated.fif`.
 - **MUST** use pinned random seeds.
 - **MUST** be fully scripted and deterministic.
 - **Purpose**: This task ensures the full pipeline code paths (preprocess -> metrics -> stats) can run end-to-end for validation, but results are marked `simulation_only` and **excluded** from biological claims.
 - **Depends on**: T011a (condition: `has_real_data: false`), T010.
- [X] T011d [US1] **Unit Test Ground Truth: Generate Synthetic Data with Injected Coupling**: Implement `code/data/generate_unit_test_data.py` to create a small, controlled dataset with **known injected correlations** between structural metrics and avalanche exponents. **Logic**:
 1) Generate synthetic structural metrics (degree, clustering) with known distribution.
 2) Generate synthetic avalanche exponents with a **known correlation** (e.g., rho=0.7) to the structural metrics.
 3) Output to `data/processed/unit_test/metrics_ground_truth.csv`.
 4) **Purpose**: This dataset is used **exclusively** by T024/T045 to validate the statistical logic (Spearman, Permutation, VIF) as required by Plan Phase 3. It is NOT used for the main pipeline flow.
 - **Depends on**: T004.
- [X] T012 [US1] Implement quality control checks in `code/data/quality_control.py`. **Real Data**: Exclude participants with >30% channels removed after ICA. **Simulated Data**: Exclude participants with disconnected structural graphs. **MUST** calculate and output the proportion of participants with complete pipelines (SC-004). **Treat simulation generation as a valid EEG pipeline for SC-004 calculation**.
 - **Input**: `data/processed/unified_participant_store.json` (produced by T013).
 - **Logic**: Read the `data_type` field. If `real`, apply ICA artifact rules. If `simulated`, apply connectivity rules.
 - **Output**: `data/processed/usable_subjects.json` containing list of valid subject IDs.
 - **Depends on**: T010, T011b (if real), T011c (if simulated), T013.
- [X] T013 [US1] Implement `code/data/store.py` to save participant-indexed structural matrices and cleaned (real or simulated) EEG time-series (US-1, AC2, AC3). **Logic**:
 1) Read output from T010 (structural) and T011b/T011c (EEG).
 2) Read `data/processed/usable_subjects.json` from T012 to filter for valid subjects.
 3) Create a unified participant index JSON: `data/processed/unified_participant_store.json`.
 4) **Schema**: `{ "subject_id": str, "structural_path": str, "eeg_path": str, "data_type": "real" | "simulated" }`.
 5) **Verification**: Assert that all subject IDs from `data/processed/usable_subjects.json` are present in the store and that the file contains no null paths.
 - **Output**: `data/processed/unified_participant_store.json`.
 - **Depends on**: T010, T011b, T011c, T012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data pipeline complete, real or simulated data processed)

---

## Phase 3.5: Sample Size Gate (Blocking)

**Purpose**: Enforce minimum sample size before statistical analysis.

- [X] T029c [US3] **Runtime Gate: Sample Size Check**: Implement the 'Sample Size Check' in `code/main.py` as an explicit **runtime gate** task. **Logic**:
 1) Count usable subjects N from `data/processed/usable_subjects.json` (produced by T012). **Note**: T012 depends on T015c for the count of valid subjects with metrics.
 2) Read `N_MIN` from `code/config.py`.
 3) If N < N_MIN: **SET** status='limited', **GENERATE** `data/results/insufficient_sample_report.md` documenting the limited sample size, and **PROCEED** to analysis (for validation purposes). If N = 0: **HALT** with error.
 4) If N >= N_MIN: **SET** status='proceed', **CONTINUE** to correlation analysis.
 5) **Write `data/processed/routing_state.json`** (overwriting previous state) with `{ "path": "correlation" | "limited" | "unit_test", "N": <N>, "N_MIN": <N_MIN>, "status": "proceed" | "limited" }`.
 - **This task explicitly routes execution** and produces the authoritative state file that T015c, T019, T020 depend on.
 - **Depends on**: T015c (to get the count of valid subjects with metrics).

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2) & Revision Fixes

**Goal**: Compute canonical structural network metrics and neural avalanche statistics from the processed (real or simulated) data. **Also includes Revision tasks (T031-T033) to ensure correct logic before analysis.**

**Independent Test**: Can be fully tested by computing metrics for the subset of participants generated in US1 and verifying that output values (degree, clustering, avalanche size) are within expected ranges for human brain networks and neural avalanches.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `code/analysis/metrics.py` to compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX and BCTpy (FR-003). **Depends on**: T010 completion. **Can run in parallel** with T015.
- [X] T015 [US2] **Unified: Detect Avalanches**: Implement `code/analysis/avalanches.py` to detect neural avalanches from **real or simulated** EEG. **Logic**:
 1) **Conditional Branch**:
    - **If Real EEG (T011b)**: Load `data/processed/eeg/sub-{id}/eeg_cleaned.fif`.
    - **If Simulated EEG (T011c)**: Load `data/processed/eeg/sub-{id}/eeg_simulated.fif`.
 2) **Thresholding Logic**:
    - Calculate the **75th percentile amplitude** from the **RAW signal distribution** (per-participant) BEFORE z-scoring. Let this be `T_raw`.
    - Apply z-score normalization (global mean and std) to the EEG signal. Let the normalized signal be `Z`.
    - Threshold the **z-scored signal** `Z` at the value `T_z = (T_raw - mean) / std`.
 3) **Output**: `data/processed/avalanches/sub-{id}/avalanche_events.csv`.
 - **Depends on**: T011b (if real) OR T011c (if simulated).
- [X] T015c [US2] Implement `code/analysis/aggregate_avalanches.py` to produce a deterministic artifact `data/processed/avalanche_metrics.csv` containing size, duration, and power-law exponents for all participants (Real or Simulated). **Logic**:
 1) Read output from T015.
 2) **Filter**: Exclude participants where power-law fit failed or was rejected by likelihood ratio test (per FR-011, T033).
 3) **MUST** check `data/processed/routing_state.json` from T029c. If `status` is "limited", skip execution and generate a limited report. If "proceed", continue. If `path` is "real" and `n_matched` is 0, **SKIP** aggregation and generate a "no_data" report (Plan: Biological association suspended).
 4) **Output**: `data/processed/avalanche_metrics.csv` (or "no_data" report).
 - **Output**: `data/processed/avalanche_metrics.csv`.
 - **Depends on**: T015, T029c (status: "proceed").
- [X] T016 [US2] Implement power-law model fitting in `code/analysis/fitting.py` using `powerlaw` package with model comparison (power-law vs. exponential vs. log-normal) per FR-011. **Depends on**: T033.
- [X] T017 [US2] Create export script `code/analysis/export_metrics.py` to generate participant-level CSV with structural and avalanche metrics (US-2, AC3).
- [X] T018 [P] [US2] Implement unit tests in `tests/test_metrics.py` (e.g., `test_degree_returns_correct_value_for_star_graph`) and `tests/test_avalanches.py` (e.g., `test_avalanche_detection_handles_flat_signal`).

### Revision Tasks (Moved to Phase 2 to ensure logic is fixed before analysis)

- [X] T031 [US3] **Standardize Sensitivity Sweep Range**: Update `code/analysis/sensitivity.py` to use hardcoded threshold values `{0.70, 0.75, 0.80}` from `code/config.py` (defined in T004). **MUST NOT** load from `research_phase_config.json`. **Rationale**: SC-002 requires measuring stability across specific thresholds; "deferred" in code leads to inconsistent execution. **Note**: SC-002 in this file now references these hardcoded values for testability, resolving the "[deferred]" status as a design decision.
- [X] T032 [US3] **Enforce Associational Framing**: Add a validation step in `code/analysis/report.py` that scans the generated text for causal keywords (e.g., "causes", "drives", "leads to") and raises a `RuntimeError` if found, forcing the user to rephrase. **Rationale**: FR-010 and US-3 explicitly forbid causal claims; automated enforcement ensures compliance.
- [X] T033 [US2] **Validate Power-Law Fit Convergence**: Update `code/analysis/fitting.py` to explicitly handle the `powerlaw` package's convergence failure by logging a specific error code and excluding the participant from the correlation matrix, rather than silently returning NaN. **Rationale**: FR-011 requires model comparison; silent failures corrupt the statistical association in US-3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (metrics computed) and Revision logic is in place.

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction for multiple comparisons and threshold sensitivity. **NOTE**: For Real Data, this is **SUSPENDED** (Plan). For Unit Tests, this is **ACTIVE** (T024/T045).

**Independent Test**: Can be fully tested by running the association analysis on the computed metrics and verifying that correlation coefficients, p-values, and sensitivity sweep results are reproducible and frame findings as associational.

### Implementation for User Story 3

- [X] T019 [US3] Implement `code/analysis/stats.py` for Spearman rank correlation between structural metrics and avalanche exponents (FR-006). **Depends on**: T014 and T015c. **Must check** `routing_state.json` from T029c before running. **GATING**: If `path` is "real" and `n_matched` is 0, **SKIP** execution and log "Biological association suspended due to N=0 matched subjects".
- [X] T020 [US3] Implement non-parametric permutation test (shuffles) and family-wise error correction using **max-t permutation** method (FR-007) in `code/analysis/stats.py`. **Depends on**: T019 completion. **GATING**: Same as T019.
- [X] T021 [US3] Implement collinearity diagnostics (VIF) in `code/analysis/stats.py` with flagging logic for VIF ≥ 5 (FR-009). **MUST** write a flag to `data/results/collinearity_status.json` with key `high_collinearity: true/false` and `vif_value: <float>`. **MUST** ensure this flag is consumed by T049 to suppress claims. **Depends on**: T019.
- [X] T022 [US3] Implement sensitivity analysis sweep across thresholds {0.70, 0.75, 0.80} in `code/analysis/sensitivity.py` (FR-008). **MUST** use hardcoded Spec values, not config file. **Depends on**: T019 (and T031 logic is already in place).
- [X] T023 [US3] Create final report generator `code/analysis/report.py` ensuring all findings are framed as associational (FR-010). **MUST** read `data/results/collinearity_status.json` from T021 and suppress any claims of independent predictive effects if `high_collinearity` is true. **MUST** use T032 logic for causal keyword checking. **Depends on**: T021, T032.
- [X] T024 [P] [US3] Implement integration tests in `tests/test_stats.py` using the **Synthetic Ground Truth** from T011d. **Logic**:
 1) Load `data/processed/unit_test/metrics_ground_truth.csv` (from T011d).
 2) Assert that Spearman correlation detects the injected coupling (rho ≈ a strong positive value).
 3) Assert that Permutation test correctly identifies significance.
 4) Assert that VIF diagnostics correctly flag collinearity if injected.
 5) **This is the PRIMARY VALIDATION PATH** for FR-006/007 as per Plan Phase 3.
 - **Depends on**: T011d.

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

- [X] T047 [P] [US1] **Implement Strict Data Source Fallback Prevention**: Update `code/data/download.py` to remove ANY `try/except` blocks that might catch network errors and fall back to `generate_synthetic_*()` or placeholder data. **Logic**: If the fetch from OpenNeuro fails (timeout, 404, etc.), the script MUST raise a `ConnectionError` or `FileNotFoundError` immediately. **No silent fallbacks**. This ensures the "Fail Loudly" rule is enforced. **Depends on**: T009.
- [X] T048 [P] [US1] **Implement Real Data Streaming Verification**: Update `code/data/download.py` to explicitly log the chunking strategy used for datasets > 100MB. **Logic**: Verify that `datasets.load_dataset(..., streaming=True)` is used for large files and that Memory usage remains within reasonable bounds during the download/processing loop. **Depends on**: T009, T041.
- [X] T049 [US3] **Implement Collinearity Report Suppression Logic**: Update `code/analysis/report.py` to explicitly check `data/results/collinearity_status.json` before generating any text about "independent predictive effects". **Logic**: If `high_collinearity` is true, the report MUST state: "High collinearity (VIF >= 5) detected between degree and clustering coefficient. Independent predictive effects are not claimed." **Verification**: Assert that the report contains this specific string when VIF >= 5. **Depends on**: T021, T023.
- [X] T050 [US3] **Final Pipeline Integration Test**: Run a full end-to-end test of the pipeline with a small synthetic dataset (N=5) to verify that the routing logic (T011a, T029c) correctly switches between Real/Simulation paths and that the final report is generated without errors. **Command**: `python code/main.py --test-mode --n-subjects=5`. **Output**: Generate `data/results/integration_test_report.md` with pass/fail status and execution logs. **Success Criteria**: Report generated, no errors, routing logic verified. **Depends on**: All previous tasks.

---

## Phase 9: Post-Analysis Review & Correction (Addressing New Review Concerns)

**Goal**: Address specific concerns raised by the `/speckit.analyze` run regarding data source verification, threshold handling, and statistical framing. These tasks are triggered by the analysis report and must be completed before the project can transition to `analyzed`. **NOTE**: These tasks are updated to reflect the "Pipeline Validation Study" scope (separate datasets, unit test validation).

**Independent Test**: Can be verified by running the pipeline again and confirming that the new tasks resolve the specific issues flagged in the analysis report.

### Implementation for Post-Analysis Review

- [ ] T051 [US3] **Verify Data Source Integrity**: Update `code/data/download.py` to include a checksum validation step for the downloaded dMRI and EEG datasets from **SEPARATE** sources (ds004230, ds004231). **Logic**: After downloading, compute the SHA-256 hash of the file and compare it against the expected hash from `data/processed/parcellation_hash.json` (for dMRI) or a new `eeg_hash.json` (for EEG). **Failure**: Raise an error if the hash does not match. **Depends on**: T009, T047.
- [ ] T052 [US3] **Standardize Threshold Handling**: Update `code/analysis/avalanches.py` to ensure the 75th percentile threshold is calculated on the **raw, un-normalized** signal, and then applied to the **z-scored** signal after normalization. **Logic**: Explicitly document this two-step process in the code comments and verify the output against a known test case. **Depends on**: T015.
- [ ] T053 [US3] **Enforce Associational Framing in All Outputs**: Update `code/analysis/report.py` to include a comprehensive check for causal language not just in the main report, but also in any generated plots, tables, and intermediate logs. **Logic**: Scan all output strings for keywords like "cause", "effect", "drive", "influence" and raise a `RuntimeError` if found. **Depends on**: T032, T023.
- [ ] T054 [US3] **Validate Power-Law Model Selection**: Update `code/analysis/fitting.py` to ensure that the power-law model is only selected if it is statistically preferred over both the exponential and log-normal models according to the likelihood ratio test. **Logic**: Implement a clear decision tree in the code that logs the result of each comparison and excludes the participant if no model is preferred. **Depends on**: T016, T033.
- [ ] T055 [US3] **Implement Robust Error Handling for Permutation Tests**: Update `code/analysis/stats.py` to handle cases where the permutation test fails to converge or produces invalid p-values. **Logic**: Implement a retry mechanism with a maximum number of attempts and a fallback to a conservative p-value estimate if convergence is not achieved. **Depends on**: T020.
- [ ] T056 [US3] **Document Simulation Parameters**: Update `code/config.py` to include a detailed description of the simulation parameters used in `simulate_EEG.py`, including the rationale for each parameter choice. **Logic**: Add docstrings and comments to the `SIMULATION_MODEL_PARAMS` dictionary. **Depends on**: T004.
- [ ] T057 [US3] **Add Unit Test for Threshold Sensitivity**: Implement `tests/test_threshold_sensitivity.py` to verify that the sensitivity analysis correctly produces different results for different threshold values. **Logic**: Run the analysis with thresholds {0.70, 0.75, 0.80} and assert that the correlation coefficients and p-values are different. **Depends on**: T022.
- [ ] T058 [US3] **Add Unit Test for Collinearity Diagnostics**: Implement `tests/test_collinearity_diagnostics.py` to verify that the VIF calculation is correct and that the flagging logic for VIF ≥ 5 works as expected. **Logic**: Create a mock dataset with known collinearity and assert that the VIF value is correctly calculated and the flag is set. **Depends on**: T021.
- [ ] T059 [US3] **Add Unit Test for Data Quality Filtering**: Implement `tests/test_data_quality_filtering.py` to verify that the quality control checks correctly exclude participants with excessive artifact or disconnected graphs. **Logic**: Create mock datasets with known quality issues and assert that they are correctly excluded from the analysis. **Depends on**: T012.
- [ ] T060 [US3] **Final Compliance Check**: Run a comprehensive compliance check against all functional requirements (FR-001 to FR-011) and success criteria (SC-001 to SC-006). **Logic**: Implement a script that automatically checks each requirement and criterion and generates a compliance report. **Depends on**: All previous tasks.

**Checkpoint**: All post-analysis review tasks are complete, and the pipeline is fully compliant with the specification and analysis findings.

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
- **Post-Analysis Review (Phase 9)**: **MUST** be completed after the initial `/speckit.analyze` run and before the project can transition to `analyzed`.

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
- **T009** (download) must implement the full spec-authorized logic (ds004230 for dMRI, ds004231 for EEG) as **SEPARATE** datasets with NO matching.
- **T011a** (Check Availability) is the **GATE**. It determines whether T011b (Real - Primary) or T011c (Sim - Fallback) runs.
- **T011b** (Real EEG) and **T011c** (Simulated EEG) are **MUTUALLY EXCLUSIVE**. They cannot run in parallel. Only one will execute based on T011a's result.
- **T011d** (Unit Test Ground Truth) is **INDEPENDENT** and runs for validation tests.
- **T015** (Unified Avalanches) is **UNCONDITIONAL** (given T011b or T011c success).
- **T015c** (Unified Metrics) produces the deterministic artifact for T019.
- **T019** (stats.py) **MUST** run after T014 and T015c.
- **T020** (permutation) **MUST** run after T019.
- **T029c** (Runtime Gate) is now in Phase 3.5, **after** T015c (to count valid subjects).
- **T031, T032, T033** (Revision tasks) are now in Phase 2, **before** T016, T022, T023.
- **T042** logic has been updated to verify associational framing for simulated data.
- **T047** ensures no synthetic fallbacks are used if real data fetch fails.
- **T048** ensures streaming is used for large datasets to prevent OOM.
- **T049** ensures collinearity warnings are properly reported.
- **T050** is the final integration test.
- **T051-T060** (Post-Analysis Review) are triggered by the `/speckit.analyze` run and must be completed before the project can transition to `analyzed`.

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
- **T011 Logic**: T011a is the gate. T011b is conditional on T011a finding data (primary). T011c is conditional on T011a finding NO data (fallback). **If successful, it proceeds to T015.**
- **T015 Logic**: T015 explicitly defines z-score normalization parameters and the correct thresholding logic (z-score signal, then threshold at 75th percentile of RAW signal).
- **Config Logic**: T031 now uses hardcoded Spec values; no config file dependency for thresholds.
- **T042 Logic**: Updated to verify associational framing for simulated data.
- **T012 Logic**: Updated to count simulation as a valid pipeline for SC-004.
- **T025a-c Logic**: Consolidated into T025a, T025b, T025c.
- **T027a Logic**: Updated to specify 4 workers and runtime verification.
- **T042 Logic**: Updated to specify `report.py` as the location for flagging logic.
- **Phase Order**: T031, T032, T033 moved to Phase 2 to ensure logic is fixed before T016, T022, T023.
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
- **T051-T060 Fix**: Address specific concerns raised by the `/speckit.analyze` run regarding data source verification, threshold handling, and statistical framing. These tasks are triggered by the analysis report and must be completed before the project can transition to `analyzed`.