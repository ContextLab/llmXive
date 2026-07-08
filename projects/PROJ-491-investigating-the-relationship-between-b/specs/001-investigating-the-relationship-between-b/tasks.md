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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `state/` (Note: `specs/001-gene-regulation/` is a source artifact, not created here)
- [ ] T001b [P] Create `.gitignore` excluding `data/raw/*.nii*`, `data/processed/*.csv`, `__pycache__`, `*.pyc`, `env/`
- [ ] T001c [P] Create `README.md` skeleton with project title and empty installation/usage sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scikit-learn, nibabel, scipy, matplotlib, requests, tqdm, bids)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools
- [X] T004 Create `code/config.py` defining paths, seeds (), and parameters (window sizes:, 30, 40 TRs)
- [~] T005 [P] Implement `code/state_manager.py` to compute content hashes for artifacts and update `state/` YAML
- [~] T006 [P] Setup `code/__init__.py` and basic logging infrastructure
- [~] T007a [P] Define and write `data/contracts/atlas_power264.json` containing Power node coordinates in MNI space
- [~] T007b [P] Define and write `data/contracts/roi_ventral_striatum.json` containing Ventral Striatum ROI MNI coordinates
- [ ] T007c [P] Implement logic to identify and write `data/contracts/Power264_excl_vs_nodes.json` listing Power 264 nodes overlapping with VS ROI to prevent double-dipping
- [ ] T008 [P] Implement memory-efficient streaming utilities for large NIfTI files to ensure <7GB RAM usage
- [ ] T009 Setup environment configuration management for OpenNeuro credentials

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and prepare a subsample of 50 HCP subjects (resting-state and task-fMRI) ensuring memory constraints and data validity.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script and verifying the output directory contains exactly 50 subject folders (or fewer if skipped), with both resting-state and task-fMRI NIfTI files, and that total disk usage is ≤ 14 GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for session ID validation logic in `tests/unit/test_data_ingestion.py`
- [ ] T011 [P] [US1] Integration test for data download and checksum verification in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_ingestion.py` to download HCP data from OpenNeuro for 50 subjects (FR-001)
- [ ] T013 [US1] Implement session ID distinctness validation logic in `code/data_ingestion.py` (FR-008), explicitly excluding subjects with matching session IDs from the downstream pipeline
- [ ] T013b [US1] Implement logic to calculate the pass-rate percentage of subjects with distinct session IDs and write this metric to `data/processed/session_validation_metrics.json` (SC-005)
- [ ] T013c [US1] Implement logic to write the list of excluded subject IDs (due to session ID mismatch) to `data/processed/excluded_session_ids.csv`
- [ ] T014 [US1] Implement logic to skip corrupted/missing subjects and log warnings to `data/processed/ingestion_warnings.log` (Edge Case)
- [ ] T015 [US1] Implement logic to fail fast with non-zero exit code and error message "Error: Insufficient valid subjects (<50)" if <50 valid subjects found, logging to `data/processed/ingestion_errors.log` (FR-010)
- [ ] T016 [US1] Implement `code/preprocessing.py` to extract BOLD time series using Power 264 atlas, explicitly excluding nodes listed in `data/contracts/Power264_excl_vs_nodes.json` to prevent double-dipping (FR-002)
- [ ] T016c [US1] Implement `code/preprocessing.py` to explicitly extract the Ventral Striatum (VS) ROI time series from task-fMRI NIfTI files for all valid subjects (FR-002)
- [ ] T016b [US1] Implement aggregation of task-fMRI BOLD time series (from T016c) to calculate mean ventral striatum activation magnitude per subject, writing to `data/processed/ventral_striatum_activation.csv` (FR-002)
- [ ] T017 [US1] Verify TR of downloaded data matches expected values for window calculations; fail with non-zero exit code and "Error: TR mismatch" if invalid (Assumption)
- [ ] T018 [US1] Ensure memory footprint of loaded data never exceeds 7 GB during processing (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (valid CSV time series generated for 50 subjects)

---

## Phase 4: User Story 2 - Dynamic Connectivity and Flexibility Calculation (Priority: P2)

**Goal**: Compute dynamic functional connectivity (dFC) metrics and derive a "flexibility" score for each subject using sliding window K-means.

**Independent Test**: The calculation can be tested independently by running the dFC module on a small synthetic dataset with known switching patterns and verifying the flexibility score correlates with ground truth and produces identical results on repeated runs (seed=42).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for K-means clustering determinism (seed=42) in `tests/unit/test_connectivity.py`
- [ ] T020 [P] [US2] Unit test for flexibility score calculation against known ground truth in `tests/unit/test_connectivity.py`

### Implementation for User Story 2

- [ ] T020b [US2] Generate synthetic ground truth dataset with known switching patterns to validate the flexibility calculation logic (Independent Test requirement)
- [ ] T021 [US2] Implement sliding window functional connectivity calculation (window=30 TR, step=1 TR) in `code/connectivity.py` (FR-003)
- [ ] T022 [US2] Implement K-means clustering (K=4, K-means++, seed=42) to define state space in `code/connectivity.py` (FR-003a)
- [ ] T023 [US2] Implement flexibility score calculation (state switching frequency) normalized for scan length in `code/connectivity.py` (FR-004)
- [ ] T025 [US2] Handle edge case: flag and exclude subjects with zero variance flexibility scores, writing excluded subject IDs to `data/processed/excluded_subjects_log.csv` (Edge Case)
- [ ] T025b [US2] Filter the `data/processed/ventral_striatum_activation.csv` (from T016b) to match the remaining subject list after zero-variance exclusions, ensuring data alignment for correlation analysis
- [ ] T026 [US2] Ensure output files are CSVs containing time-series state sequences and scalar flexibility scores

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (flexibility scores generated for 50 subjects)

---

## Phase 5: User Story 3 - Correlation Analysis and Significance Testing (Priority: P3)

**Goal**: Correlate flexibility scores with ventral striatum activation and perform permutation testing to establish significance.

**Independent Test**: The analysis can be tested independently by providing a mock dataset with a known correlation coefficient and verifying the Pearson correlation calculation and permutation p-value match expected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Pearson correlation and p-value calculation in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for permutation test logic (A sufficient number of iterations will be performed to ensure convergence.) in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement Pearson correlation analysis between flexibility scores and ventral striatum activation in `code/analysis.py` (FR-005)
- [ ] T029b [US3] Implement sensitivity analysis loop for window sizes {20, 30, 40} TRs; calculate correlation and p-value for each; write results to `data/processed/sensitivity_analysis.csv` with columns: window_size, correlation_coefficient, p_value (FR-009)
- [ ] T030 [US3] Implement permutation test (A sufficient number of iterations will be performed to ensure convergence.) to calculate empirical p-value in `code/analysis.py` (FR-006)
- [ ] T031 [US3] Handle edge case: report p < 1/1001 if permutation p-value is exactly 0 (Edge Case)
- [ ] T032 [US3] Generate scatter plot with regression line for the correlation result
- [ ] T033 [US3] Implement `code/reporting.py` to generate final markdown report containing "associational relationship" and excluding "causal" (FR-007)
- [ ] T034 [US3] Include sensitivity analysis results (window sizes 20, 30, 40) from `data/processed/sensitivity_analysis.csv` in the final report (FR-009)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Update `README.md` with installation instructions and CLI usage examples
- [ ] T035b [P] Update `specs/001-gene-regulation/` documentation with final data flow diagrams
- [ ] T036a Code cleanup: fix linting errors in `code/`
- [ ] T036b Code cleanup: remove dead code and unused imports in `code/`
- [ ] T037c [P] Benchmark pipeline runtime on a small subset (e.g., 5 subjects) to establish a baseline and verify the time constraint before full execution (FR-009/Assumptions)
- [ ] T037b [P] Performance optimization: ensure total runtime stays <6h for 50 subjects based on T037c results (FR-009/Assumptions)
- [ ] T037a Performance optimization: ensure peak RAM usage stays <6GB during processing
- [ ] T038 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation
- [ ] T040 Verify `state/` YAML contains hashes for all artifacts in `data/processed/` and `paper/` (Constitution V)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
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