# Tasks: Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing

**Input**: Design documents from `/specs/001-gene-regulation/`
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

## Phase 0: Research & Feasibility (Plan Phase 0)

**Purpose**: Verify data availability and coordinate alignment before implementation begins.

- [X] T000a [P] [Plan] Verify OpenNeuro dataset `ds000001` (or equivalent HCP) contains at least 50 subjects with both resting-state and task-fMRI data and distinct session IDs. Log results to `data/research/data_availability_log.txt`.
- [X] T000b [P] [Plan] Verify Power 264 atlas coordinates and Ventral Striatum ROI coordinates are compatible with HCP MNI152NLin2009cAsym space. If mismatch, plan resampling strategy. Log results to `data/research/coordinate_alignment_log.txt`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `state/`, `data/research/`, `data/contracts/` (Note: `specs/001-gene-regulation/` is a source artifact, not created here)
- [X] T001b [P] Create `.gitignore` excluding `data/raw/*.nii*`, `data/processed/*.csv`, `data/processed/*.json`, `data/processed/*.png`, `__pycache__`, `*.pyc`, `env/`, `.env`
- [X] T001c [P] Create `README.md` skeleton with project title and empty installation/usage sections
- [X] T001d [P] [Plan] Define and write `data/contracts/csv_time_series.schema.yaml` for extracted BOLD time series.
- [X] T001e [P] [Plan] Define and write `data/contracts/states.schema.yaml` for dynamic state sequences.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scikit-learn, nibabel, scipy, matplotlib, requests, tqdm, bids)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools: Create `setup.cfg` with flake8 rules and `pyproject.toml` for black
- [X] T004 Create `code/config.py` defining paths, seeds (42), and parameters (window sizes: [20, 30, 40])
- [X] T005 [P] Implement `code/state_manager.py` to compute content hashes for artifacts and update `state/` YAML
- [X] T006 [P] Setup `code/__init__.py` and basic logging infrastructure
- [X] T007a [P] Define and write `data/contracts/atlas_power264.json` containing Power node coordinates in MNI space
- [X] T007b [P] Define and write `data/contracts/roi_ventral_striatum.json` containing Ventral Striatum ROI MNI coordinates
- [X] T007c [P] Implement logic to identify and write `data/contracts/Power264_excl_vs_nodes.json` listing Power 264 nodes overlapping with VS ROI to prevent double-dipping
- [X] T008 [P] Implement memory-efficient streaming utilities: Create `code/streaming_utils.py` with function `load_nifti_chunked(input_path, chunk_size)` to load NIfTI data in chunks to ensure <7GB RAM usage
- [X] T009 [P] Setup environment configuration management: Create `code/.env.example` with placeholders for OpenNeuro credentials (OPENNEURO_USER, OPENNEURO_PASS) and implement `code/config.py` to load these securely.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and prepare a subsample of 50 HCP subjects (resting-state and task-fMRI) ensuring memory constraints and data validity.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output directory contains exactly 50 subject folders (or fewer if skipped), with both resting-state and task-fMRI NIfTI files, and that total disk usage is ≤ 14 GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for session ID validation logic in `tests/unit/test_data_ingestion.py`
- [X] T011 [P] [US1] Integration test for data download and checksum verification in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_ingestion.py` to download HCP data from OpenNeuro for 50 subjects (FR-001). **Hashing**: Call `state_manager.hash_artifact("data/raw/*.nii*")` after download to record raw data checksums.
- [X] T012a [US1] Implement logic in `code/data_ingestion.py` to read NIfTI headers and extract Repetition Time (TR) values for validation (Supports T017).
- [X] T013 [US1] **Implement Session Validation, Metrics, Fail-Fast, and Hashing**: Implement logic in `code/data_ingestion.py` to:
 1. Read NIfTI headers for all downloaded subjects.
 2. Validate distinct session IDs (FR-008).
 3. Calculate pass-rate percentage and write `data/processed/session_validation_metrics.json` (SC-005) FIRST. Schema: `{"pass_rate": float, "total_subjects": int, "valid_subjects": int}`.
 4. Write list of excluded subject IDs to `data/processed/excluded_session_ids.csv` FIRST.
 5. **Fail Fast**: If valid subjects < 50, exit with code 1 and error "Error: Insufficient valid subjects (<50)" (FR-010) AFTER files are written.
 6. **Verification**: Assert `session_validation_metrics.json` keys are exactly `["pass_rate", "total_subjects", "valid_subjects"]` and `pass_rate` is a float [0.0, 1.0]. Assert `excluded_session_ids.csv` exists and is consistent.
 7. **Hashing**: Call `state_manager.hash_artifact("data/processed/session_validation_metrics.json")` and `state_manager.hash_artifact("data/processed/excluded_session_ids.csv")`. **Depends on: T012**
- [X] T016 [US1] Implement `code/preprocessing.py` to extract BOLD time series using Power 264 atlas, explicitly excluding nodes listed in `data/contracts/Power264_excl_vs_nodes.json` to prevent double-dipping (FR-002). **Note**: VS ROI is excluded from this extraction per spec; VS time series are extracted separately from task-fMRI in T016c.
- [X] T016c [US1] Implement `code/preprocessing.py` to explicitly extract the Ventral Striatum (VS) ROI time series from task-fMRI NIfTI files for all valid subjects and write to `data/processed/vs_time_series.csv` (FR-002). **Hashing**: Call `state_manager.hash_artifact("data/processed/vs_time_series.csv")`.
- [X] T016b [US1] **Aggregate VS Activation and Verify**: Implement logic in `code/preprocessing.py` to:
 1. Read `data/processed/vs_time_series.csv` (from T016c).
 2. Calculate mean ventral striatum activation magnitude per subject.
 3. Write to `data/processed/ventral_striatum_activation.csv`. Schema: `{"subject_id": str, "mean_activation": float}`.
 4. **Verification**: Assert file exists, is not empty, and contains columns `["subject_id", "mean_activation"]`. Verify `mean_activation` is the average of the VS ROI time series across reward cue epochs (identified via event file JSON sidecar or fixed time window defined in `code/config.py`).
 5. **Hashing**: Call `state_manager.hash_artifact("data/processed/ventral_striatum_activation.csv")`. **Depends on: T016c**
- [X] T016d [US1] **Log Excluded Nodes**: Implement logic in `code/preprocessing.py` to write the list of Power 264 nodes excluded (those overlapping VS) to `data/contracts/Power264_excluded_vs_nodes_log.csv` to satisfy Constitution Principle VI. **Hashing**: Call `state_manager.hash_artifact("data/contracts/Power264_excluded_vs_nodes_log.csv")`. **Depends on: T007c**
- [X] T017 [US1] Verify TR of downloaded data matches expected values for window calculations; fail with non-zero exit code and "Error: TR mismatch" if invalid (Assumption). **Depends on: T012a**.
- [X] T018 [US1] Ensure memory footprint of loaded data never exceeds 7 GB during processing (SC-001). Generate `data/processed/memory_profile.json` logging peak RAM usage and assert peak < 7GB. **Depends on: T008 (existence)**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (valid CSV time series generated for 50 subjects)

---

## Phase 4: User Story 2 - Dynamic Connectivity and Flexibility Calculation (Priority: P2)

**Goal**: Compute dynamic functional connectivity (dFC) metrics and derive a "flexibility" score for each subject using sliding window K-means.

**Independent Test**: The calculation can be tested independently by running the dFC module on a small synthetic dataset with known switching patterns and verifying the flexibility score correlates with ground truth and produces identical results on repeated runs (seed=42).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for K-means clustering determinism (seed=42) in `tests/unit/test_connectivity.py`
- [X] T020 [P] [US2] Unit test for flexibility score calculation against known ground truth in `tests/unit/test_connectivity.py`

### Implementation for User Story 2

- [X] T020b [US2] Generate synthetic ground truth dataset with known switching patterns to validate the flexibility calculation logic. Write to `data/synthetic/ground_truth_seed.csv` with columns: `subject_id`, `state_sequence`, `flexibility_score`
- [X] T021a [US2] Refactor `code/connectivity.py` sliding window function to accept `window_size` as a parameter (default 30) to support sensitivity analysis (FR-009).
- [X] T021 [US2] Implement sliding window functional connectivity calculation (window=30 TR, step=1 TR) in `code/connectivity.py` (FR-003). **Depends on: T021a**.
- [X] T021b [US2] **Sensitivity Analysis Loop**: Implement sensitivity analysis loop in `code/connectivity.py` to execute sliding window calculation for window sizes **[20, 30, 40]** TRs and store intermediate state sequences. **Depends on: T021, T021a**.
- [X] T022 [US2] Implement K-means clustering (K=4, K-means++, seed=42) to define state space in `code/connectivity.py` (FR-003a). **Explicitly use `init='k-means++'`**.
- [X] T023 [US2] Implement flexibility score calculation (state switching frequency) normalized for scan length in `code/connectivity.py` (FR-004)
- [X] T025 [US2] **Handle Zero-Variance, Align Data, and Verify**: Implement logic in `code/connectivity.py` to:
 1. Flag and exclude subjects with zero variance flexibility scores.
 2. Write excluded subject IDs to `data/processed/excluded_zero_variance_subjects.csv`.
 3. Filter `data/processed/ventral_striatum_activation.csv` (from T016b) to match the remaining subject list.
 4. **Verification**: Assert `excluded_zero_variance_subjects.csv` exists and contains valid subject IDs. Verify the filtered activation CSV contains only subject IDs present in the flexibility score output and excludes those in `excluded_zero_variance_subjects.csv`.
 5. **Hashing**: Call `state_manager.hash_artifact("data/processed/excluded_zero_variance_subjects.csv")`. **Depends on: T023, T016b**
- [X] T026 [US2] Ensure output files are CSVs containing time-series state sequences and scalar flexibility scores

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (flexibility scores generated for 50 subjects)

---

## Phase 5: User Story 3 - Correlation Analysis and Significance Testing (Priority: P3)

**Goal**: Correlate flexibility scores with ventral striatum activation and perform permutation testing to establish significance.

**Independent Test**: The analysis can be tested independently by providing a mock dataset with a known correlation coefficient and verifying the Pearson correlation calculation and permutation p-value match expected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for Pearson correlation and p-value calculation in `tests/unit/test_analysis.py`
- [X] T028 [P] [US3] Unit test for permutation test logic (a sufficient number of iterations) in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement Pearson correlation analysis between flexibility scores and ventral striatum activation in `code/analysis.py` (FR-005). **Depends on: T025**
- [X] T029b [US3] **Sensitivity Analysis and Verify**: Implement sensitivity analysis loop for window sizes **[20, 30, 40]** in `code/analysis.py`:
 1. Calculate correlation and p-value for each window size.
 2. Write results to `data/processed/sensitivity_analysis.csv` with columns: `window_size`, `correlation_coefficient`, `p_value`.
 3. **Verification**: Assert file exists, contains exactly 3 rows with `window_size` values [20, 30, 40], and that `correlation_coefficient` and `p_value` are numeric.
 4. **Hashing**: Call `state_manager.hash_artifact("data/processed/sensitivity_analysis.csv")`. **Depends on: T021b, T025**
- [X] T030 [US3] Implement permutation test with exactly 1,000 iterations to calculate empirical p-value in `code/analysis.py` (FR-006)
- [X] T031 [US3] Handle edge case: report p < 1/1001 if permutation p-value is exactly 0 (Edge Case)
- [X] T032 [US3] Generate scatter plot with regression line for the correlation result. Output to `data/processed/correlation_plot.png` using `matplotlib.pyplot.scatter` with regression line overlay
- [X] T033 [US3] **Generate Report and Verify**: Implement `code/reporting.py` to:
 1. Generate final markdown report containing "associational relationship" and excluding "causal" (FR-007).
 2. Include sensitivity analysis results (window sizes 20, 30, 40) from `data/processed/sensitivity_analysis.csv` (FR-009).
 3. **Verification**: Assert the final report contains "associational relationship" and excludes "causal".
 4. **Hashing**: Call `state_manager.hash_artifact("paper/results.md")`. **Depends on: T032, T029b**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `README.md` with installation instructions and CLI usage examples
- [X] T035b [P] Update `specs/001-gene-regulation/` documentation with final data flow diagrams
- [X] T036a Code cleanup: fix linting errors in `code/`
- [X] T036b Code cleanup: remove dead code and unused imports in `code/`
- [X] T037c [P] Benchmark pipeline runtime on a small subset (e.g., 5 subjects) to establish a baseline and verify the time constraint before full execution (FR-009/Assumptions)
- [X] T037b [P] Performance optimization: ensure total runtime stays <6h for 50 subjects based on T037c results (FR-009/Assumptions). **Deliverable**: Refactored code and benchmark log. **Verification**: Run benchmark script and log total time < 6h.
- [X] T037a Performance optimization: ensure peak RAM usage stays < 7GB during processing (matches SC-001). **Deliverable**: Refactored streaming code and benchmark log. **Verification**: Run benchmark script and log peak RAM < 7GB.
- [X] T038 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T039 Run `quickstart.md` validation
- [X] T040 Verify `state/` YAML contains hashes for all artifacts in `data/processed/` and `paper/` (Constitution V)

---

## Phase 7: Execution & Run-Book Reconciliation

**Purpose**: Ensure the execution environment can successfully run the pipeline as defined.

- [X] T041 [P] Create `code/main.py` as the orchestration entry point defined in plan.md Phase 2. **Action**: Create the file if missing, or update it to invoke the correct scripts. **Verification**: Run `python code/main.py` successfully.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution (Phase 7)**: Depends on all implementation phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (specifically T016b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and metrics from US2

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
Task: "Unit test for session ID validation logic in tests/unit/test_data_ingestion.py"
Task: "Integration test for data download and checksum verification in tests/integration/test_ingestion_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download HCP data..."
Task: "Implement code/preprocessing.py to extract BOLD time series..."
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