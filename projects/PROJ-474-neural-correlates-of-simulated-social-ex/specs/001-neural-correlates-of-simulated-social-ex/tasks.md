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

- [X] T001 Create directory structure: `data/raw`, `data/processed`, `data/results`, `src`, `tests`, `state`
- [X] T002 Create `src/__init__.py` and `tests/__init__.py` to initialize Python packages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (numpy, pandas, scipy, scikit-learn, nibabel, nilearn, pyyaml, requests, matplotlib, pytest)
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`
- [X] T005 [P] Implement `config.yaml` with paths, seeds, constants (DEFAULT a moderate threshold, DMN ROIs)
- [ ] T006 [P] Create base utility modules for logging and error handling (`src/utils.py`); **MUST implement** custom exception classes `ERR_DATA_UNAVAILABLE` and `ERR_N_INSUFFICIENT` in `src/exceptions.py` with specific message templates: `ERR_DATA_UNAVAILABLE`: "Data unavailable: {reason}", `ERR_N_INSUFFICIENT`: "Insufficient subjects (N={count}) for valid permutation test." **Inheritance**: Subclass `ValueError`.
- [X] T007 [P] Implement data integrity checker (SHA-256) utility function in `src/integrity.py` to compute checksums and update `state/projects/PROJ-474-neural-correlates-social-ex.yaml` under `artifact_hashes`; **DO NOT** perform the actual download or checksumming of raw data in this task; this task provides the **utility function** that T012 and T014 MUST call. **Schema**: `artifact_hashes`: `{ "raw/{filename}": "<sha256>", "processed/{filename}": "<sha256>" }`. **Dependencies**: T006 (for utility functions).
- [X] T008 Setup `pytest` configuration in `tests/conftest.py` with seed pinning for reproducibility

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Quality Control (Priority: P1) 🎯 MVP

**Goal**: Download real fMRI data from OpenNeuro, calculate motion metrics, and enforce strict QC thresholds (FR-002, FR-009, FR-010).

**Independent Test**: Can be fully tested by executing the data pipeline on a single subject file, verifying the motion parameter output, and confirming the subject is either retained or excluded based on the >3mm threshold.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/data_loader.py` to fetch OpenNeuro dataset ds000030 using `requests` with retry logic (finite retries with exponential backoff); **MUST** execute the following steps in strict order: 1. **Download raw dataset** from `https://openneuro.org/datasets/ds000030/versions/1.0.0/download` (or direct S3 bucket) to `data/raw/ds000030`; 2. **Compute SHA-256 checksum** of the raw file and **update state file immediately** via T007 utility (raise `ERR_DATA_UNAVAILABLE` imported from `src/exceptions.py` if mismatch); 3. **Check dataset metadata or ALL subjects** for presence of "Inclusion" and "Exclusion" trial types (raise `ERR_DATA_UNAVAILABLE` imported from `src/exceptions.py` if missing); **MUST** raise `ERR_DATA_UNAVAILABLE` if fetch fails, checksum mismatch, or markers missing; error message format: "Data unavailable: {reason}"; **DO NOT** implement fallback to alternative datasets; **DO NOT** implement fallback to synthetic data. **Prerequisites**: T006 (exceptions) and T007 (checksum utility) must be implemented first. **Output**: `data/raw/ds000030`.
- [X] T013 [US1] Implement `src/qc.py` to calculate head motion displacement (Framewise Displacement) for every subject from motion parameters; **Input**: `data/raw/ds000030`; **depends on T012, T006**
- [X] T016 [US1] Implement `src/qc.py` to verify each subject has valid time-series data for BOTH Inclusion and Exclusion conditions; **MUST** output a list of subjects with schema `{subject_id, motion_metric, condition_status, retained}` where `condition_status` is "valid" if both conditions exist, "invalid" otherwise; **Input**: `data/raw/ds000030`; **depends on T013**
- [ ] T014 [US1] Implement `src/qc.py` to Filter and return a list of ALL subjects (retained and excluded) with schema `{subject_id: string, motion_metric: float, condition_status: enum[valid, invalid], retained: boolean}`; output `data/processed/subject_qc_list.json`; **MUST** call the checksum utility (from T007) to compute SHA-256 of the output JSON and update `state/projects/PROJ-474-neural-correlates-social-ex.yaml` immediately; **MUST** filter based on the `condition_status` verified in T016 (do not re-verify conditions); **MUST also generate and output `data/processed/subjects_metadata.json`** (the definitive list of retained subjects) for downstream phases; **depends on T016, T007**
- [X] T015 [US1] Implement `src/qc.py` to check the count of filtered subjects (retained); if < 10, raise `ERR_N_INSUFFICIENT` (imported from `src/exceptions.py`); error message format: "Insufficient subjects (N={count}) for valid permutation test."; **depends on T014**; **Note**: This task halts the *final* pipeline exit, but T036 (Sensitivity) runs before this halt is triggered for the final exit.
- [ ] T017 [US1] Implement `src/main.py` orchestrator to integrate download (T012), run QC (T013-T016), handle exceptions (specifically `ERR_DATA_UNAVAILABLE` and `ERR_N_INSUFFICIENT` to **halt pipeline immediately** before proceeding to US2), and **consume** `data/processed/subjects_metadata.json` (produced by T014) to list retained subjects; **MUST** invoke T015, **catch** the raised exception, and **return error code ERR_N_INSUFFICIENT** as the script exit code if raised; **MUST** filter retained subjects from the QC list before invoking downstream tasks (T023, T024); **depends on T012, T013, T014, T015, T016, T007**

### Tests for User Story 1
> Note: Tasks T009-T011 are implemented as failing stubs first. They will intentionally fail until the corresponding implementation tasks (T012-T018) are completed, adhering to the "tests first" methodology. These tests are now independent of the implementation tasks to avoid circular dependencies. They define the expected interfaces and will be updated to assert behavior once the code exists.

- [X] T009 [US1] Unit test stub for `test_motion_calculation` in `tests/unit/test_qc.py`; define function signature `calculate_motion(subject_id)` in a stub file (independent of `src/qc.py` existence); assert `NotImplementedError`; verify eventual behavior: assert that motion > 3mm triggers exclusion flag;
- [X] T010 [US1] Unit test stub for `test_motion_hard_stop` in `tests/unit/test_qc.py`; define function signature `check_subject_count(subject_list)` in a stub file; assert `NotImplementedError`; verify eventual behavior: assert that N < 10 raises `ERR_N_INSUFFICIENT`;
- [X] T011 [US1] Unit test stub for `test_condition_completeness` in `tests/unit/test_qc.py`; define function signature `verify_conditions(subject_id)` in a stub file; assert `NotImplementedError`; verify eventual behavior: assert that missing Inclusion or Exclusion condition triggers exclusion;

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Connectivity Metric Computation (Priority: P2)

**Goal**: Extract ROI time-series, compute correlation matrices, and derive connectivity strength metrics (FR-003, FR-004, FR-005).

**Independent Test**: Can be tested by running the calculation on a synthetic time-series dataset with known correlations and verifying the output matches the expected mean absolute correlation value.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `src/preprocessing.py` to perform nuisance regression (6 motion params + derivatives, WM, CSF) using memory-mapped NIfTI loading; **MUST use `mmap=True`** to stay under 7GB RAM; **MUST** use standard MNI masks for WM/CSF extraction via `nilearn.masking.apply_mask`; **DO NOT** include global signal regression. Output derived data to `data/processed/preprocessed_{subject_id}.nii.gz` (using specific subject ID, not wildcard) to ensure traceability (Constitution Principle III); **Input**: Raw NIfTI from T012; **depends on T005, T006** (Note: T017 provides the list of subjects to process, but T023 implementation depends only on config/utils; T017 will call T023 sequentially).
- [X] T024 [US2] Implement `src/extraction.py` to extract BOLD time-series from PCC, mPFC, and angular gyrus using an anatomical atlas (FR-003); **MUST consume output from T023** (`data/processed/preprocessed_{subject_id}.nii.gz`); **MUST use `mmap=True`** when loading preprocessed files to ensure memory usage < 7GB by processing subject-by-subject; **MUST** use exact ROI labels: 'PCC', 'mPFC', 'Angular Gyrus'; **depends on T023**
- [X] T025 [US2] Implement `src/connectivity.py` to segment time-series by Inclusion/Exclusion event markers (Consumes output from T024); **depends on T024**
- [X] T026 [US2] Implement `src/connectivity.py` to compute Pearson correlation matrices per condition from segmented data (FR-004)
- [X] T027 [US2] Implement `src/connectivity.py` to calculate Mean Absolute Correlation (MAC) as the primary metric per FR-005; store global mean metric in `data/processed/connectivity_metrics.json`
- [ ] T028 [US2] Implement `src/main.py` logic to save `data/processed/connectivity_metrics.json` (subject-level MAC); **MUST** call checksum utility (T007) to update state file; **depends on T027, T007**

### Tests for User Story 2

- [X] T020 [P] [US2] Unit test for preprocessing logic in `tests/unit/test_preprocessing.py` (verify nuisance regression)
- [X] T021 [P] [US2] Unit test for ROI extraction logic in `tests/unit/test_extraction.py` (verify signal extraction from PCC, mPFC, Angular)
- [X] T022 [P] [US2] Unit test for correlation calculation in `tests/unit/test_connectivity.py` (verify Pearson correlation and MAC math)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Hypothesis Testing (Priority: P3)

**Goal**: Execute permutation tests, apply FDR correction, generate sensitivity curves, and frame results correctly (FR-006, FR-007, FR-008, FR-011, SC-005).

**Independent Test**: Can be tested by running the permutation test on a dataset where the null hypothesis is known to be true (random noise) and verifying the p-value distribution is uniform.

### Implementation for User Story 3

- [X] T033 [US3] Implement `src/stats.py` with non-parametric paired permutation test (adaptive iterations, subject-level) for MAC; ensure function is parameterized to allow re-execution with different motion thresholds (FR-006)
- [X] T034 [US3] Implement `src/stats.py` for edge-wise statistical testing with FDR correction (q ≤ 0.05) applied to the **family of edge-wise tests** (PCC-mPFC, PCC-Ang, mPFC-Ang) to detect opposing effects and control family-wise error rate (FR-011, FR-008); the global mean metric is calculated and reported separately and is **NOT** included in this FDR family.
- [X] T035 [US3] Implement `src/stats.py` to calculate the standard deviation of the permutation null distribution; store **both** the raw `std_dev_null` (as primary evidence for SC-002) and the calculated stability ratio `|mean_MAC - mean_null| / std_dev_null` (z-score) in `data/results/stability_metric.json` (SC-002)
- [ ] T036 [US3] Implement `src/stats.py` to generate a sensitivity curve: **re-executes the connectivity calculation logic** (T023-T027) for motion thresholds in range [2.0, 4.0] with **0.2mm steps** (generating sufficient points for a curve) **using the FIXED set of subjects retained at the primary threshold**; **MUST** read the fixed set of `subject_ids` from `data/processed/subject_qc_list.json` where `retained=true`; **MUST** handle case where file is missing or empty (halt or skip); **DO NOT** re-run QC logic internally to include subjects previously excluded by the 3mm rule; **Execute before T015 triggers final halt**; save results to `data/results/sensitivity_curve.csv` (threshold, p_value, effect_size) and **generate the visual plot `data/results/sensitivity_curve.png` as a PRIMARY deliverable** to satisfy SC-005; **depends on T027 (logic), T033 (logic), T014**
- [X] T037 [US3] Implement `src/stats.py` logic to check `randomization_verified` flag in dataset metadata; if false or missing, the output report MUST explicitly contain the literal string "associational" (FR-007); **depends on T017, T033** (logic providers)
- [X] T038 [US3] Implement `src/visualization.py` to generate bar plots with confidence intervals and null distribution histograms
- [ ] T039 [US3] Implement `src/main.py` to orchestrate statistical testing, save `data/results/statistical_report.json`, and generate final PDF/HTML report; **MUST** include edge-wise FDR-corrected p-values (from T034) in `statistical_report.json` and the final report (FR-008); **MUST** aggregate and include edge-wise results alongside global metric in the final output; **MUST** inject the literal string "associational" into the final report if T037 flag is set (FR-007); **MUST** explicitly verify that the final report contains the string "associational" (if required) and that both global and edge-wise results are present before completing; **depends on T033, T034, T035, T036, T037, T038**
- [X] T040 [US3] Implement `src/verification.py` to verify the final report (`data/results/statistical_report.json` or PDF/HTML) explicitly contains the literal string "associational" if `randomization_verified` is false; **MUST** raise an error if the string is missing; **depends on T039**

### Tests for User Story 3

- [X] T029 [P] [US3] Unit test for `test_permutation_logic` in `tests/unit/test_stats.py` (verify shift detection in synthetic data)
- [X] T030 [P] [US3] Unit test for `test_edge_wise_fdr` in `tests/unit/test_stats.py` (verify FDR correction application)
- [X] T031 [P] [US3] Unit test for `test_sensitivity_curve` in `tests/unit/test_stats.py` (verify generation of curve across thresholds)
- [X] T032 [P] [US3] Unit test for stability metric calculation in `tests/unit/test_stats.py` (verify null distribution std dev calculation)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Create `quickstart.md` in `specs/001-neural-correlates-social-exclusion/`
- [X] T042 [P] Create `data-model.md` in `specs/001-neural-correlates-social-exclusion/`
- [ ] T043 Code cleanup and refactoring of `src/main.py` orchestrator
- [X] T044 Performance optimization: Ensure memory usage stays within 7GB limit during permutation tests [UNRESOLVED-CLAIM: c_857ed2e2 — status=not_enough_info] (chunking if necessary)
- [X] T045 [P] Additional unit tests for edge cases (missing files, malformed JSON) in `tests/unit/`
- [X] T046 Run `quickstart.md` validation to ensure end-to-end pipeline execution on CPU-only runner

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
- **Real Data Only**: T012 must fetch real data from OpenNeuro ds000030. Simulation is only for unit tests, not the main pipeline.
- **CPU Constraints**: All tasks must be feasible on Multiple CPU cores, sufficient RAM, no GPU.
- **Sensitivity Curve Logic**: T036 re-calculates metrics for different thresholds on the **fixed set of retained subjects** to ensure valid sensitivity analysis, avoiding the logical trap of re-including subjects excluded by the core 3mm rule. T036 executes before the T015 hard halt for the final pipeline exit.
- **Memory Management**: T023 and T024 must strictly adhere to memory-mapped loading (`mmap=True`) to prevent OOM errors on the 7GB runner.
- **Error Handling**: All data loading tasks must fail loudly (raise exceptions) rather than falling back to synthetic data, per the "Real Data Only" constitution rule.
- **Exception Definitions**: `ERR_DATA_UNAVAILABLE` and `ERR_N_INSUFFICIENT` are defined in `src/exceptions.py` (T006) and must be imported explicitly in T012, T015, and T017.
- **Checksum Flow**: T007 implements the utility; T012, T014, T028 must call this utility to update the state file immediately upon artifact creation.
- **Verification**: T040 ensures the final report meets the "associational" framing requirement (FR-007).
