# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Input**: Design documents from `/specs/001-brain-music-emotion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `specs/`)
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (nibabel, nilearn, networkx, bctpy, scikit-learn, pandas, numpy, matplotlib, seaborn, datasets, openneuro-py, pydantic, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/logging.py` for reproducibility logging (seeds, timestamps, versions)
- [ ] T007 [P] Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for validation (MUST precede T005)
- [X] T005 Implement `src/models/schemas.py` with Pydantic models for `Subject`, `ConnectivityMatrix`, `NetworkMetrics`, and `BehavioralScore` (DEPENDS ON T007)
- [X] T008 [P] Implement `tests/contract/test_schemas.py` to validate JSON/YAML outputs against contracts (DEPENDS ON T005, can run parallel to T006)
- [ ] T006 [P] Setup environment configuration management (`.env` handling for API keys, data paths)
- [X] T015 [P] Implement logging enhancements in `src/utils/logging.py` for download integrity and preprocessing steps (MUST precede T011)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Retrieve HCP/OpenNeuro rs-fMRI and BMRQ data, preprocess to extract connectivity matrices.

**Independent Test**: A researcher can run the data pipeline script on a subset of 5 subjects and verify that output files contain valid connectivity matrices (symmetric, elements in range [-1, 1], diagonal = 1.0) and corresponding behavioral scores without errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T010 [P] [US1] Integration test for download pipeline (N=1) in `tests/integration/test_download.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/data/download.py`: Stream OpenNeuro ds metadata, verify BMRQ column existence, and download raw rs-fMRI NIfTI + behavioral CSV with checksum validation. **FAIL LOUDLY** if BMRQ is missing.
- [ ] T011b [US1] Implement logic in `src/data/download.py`: If BMRQ is missing, generate `data/data_gap_report.md` listing missing variables and **exit with code 1**. No synthetic data allowed.
- [ ] T012c [US1] Implement `src/data/preprocess.py`: Wrapper script to execute fMRIPrep (CPU-only mode) for motion correction and **bandpass filtering (0.01-0.1 Hz)**. Calculate Framewise Displacement (FD). **Off-CI execution logic**; CI runs dry-run on N=1. **Output**: `data/preprocessing/run_log.json` (exit code 1 on failure).
- [ ] T012d [US1] Implement validation logic in `src/data/preprocess.py`: Verify that output NIfTI files (motion-corrected, bandpass-filtered) exist, are valid, and meet schema criteria before T013 consumes them.
- [ ] T012e [US1] Implement motion exclusion logic in `src/data/preprocess.py`: Exclude subjects with FD > 0.5 mm. Update `data/preprocessing/run_log.json` with excluded subject IDs.
- [ ] T013 [US1] Implement `src/analysis/connectivity.py`: Load Schaefer atlas, extract time series from preprocessed fMRI (output of T012d), compute Pearson correlation matrices (200x200). Validate symmetry and diagonal.
- [ ] T015b [US1] Add logging for download integrity and preprocessing steps in `src/utils/logging.py` (if not already covered by T015).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (N=1 validation pass).

---

## Phase 4: User Story 2 - Network Metric Calculation and Merging (Priority: P2)

**Goal**: Calculate graph metrics (global/network-specific/edge-level) and merge with BMRQ scores.

**Independent Test**: The system can process a single subject's connectivity matrix and output a JSON object containing the keys `global_efficiency`, `modularity`, `participation_coefficient`, `network_efficiency`, and `edge_strength`, which can be successfully joined with a mock behavioral score.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for network metrics JSON schema in `tests/contract/test_metrics_schema.py`
- [ ] T017 [P] [US2] Integration test for metric calculation in `tests/integration/test_metrics.py`

### Implementation for User Story 2

- [ ] T018a [P] [US2] Implement `src/analysis/graph_metrics.py`: Calculate global efficiency, modularity, participation coefficient using `bctpy`/`networkx`.
- [ ] T018b [P] [US2] Implement `src/analysis/graph_metrics.py`: Calculate network-specific efficiencies (DMN, Salience, Visual) based on Schaefer atlas labels.
- [ ] T018c [P] [US2] Implement `src/analysis/graph_metrics.py`: Extract edge-level connectivity strengths from the full matrix and save as `data/edge_strengths_raw.json`.
- [ ] T020b [US2] Implement `src/analysis/graph_metrics.py`: Compute VIF for multicollinearity check using `edge_strengths_raw.json`. If VIF > 5, apply PCA or **flag removal**. **Output**: `data/vif_report.json` and `data/edge_strengths_corrected.json` (if PCA) OR `data/edge_strengths_filtered.csv` (if removal, listing excluded edges).
- [ ] T021 [US2] Implement data merging logic in `src/analysis/merge.py`: Join connectivity features (including **edge-level strengths** from `data/edge_strengths_corrected.json` or `data/edge_strengths_filtered.csv`) with BMRQ scores, excluding subjects with missing data.
- [ ] T025 [US2] Implement `src/analysis/stats.py`: Power analysis (Task 3.1) to verify N is sufficient for r≥0.20, α=0.05, power≥0.80. **Output**: `data/power_gate_status.json` (schema: `{'status': 'pass' | 'fail', 'achieved_power': float}`). If 'fail', exit script with code 1 and generate `data/power_failure_report.md`.
- [ ] T025b [US2] Implement `src/analysis/stats.py`: Generate `data/power_analysis_final_report.md` explicitly reporting the final achieved power, effect size detected, and sample size N to satisfy **SC-005** verification.
- [ ] T022 [US2] Add summary statistic generation (N, score distribution) in `src/analysis/merge.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.
**Gate to Phase 5**: Phase 5 (US-3) cannot begin until T025 (Power Gate) returns 'pass' in `data/power_gate_status.json`.

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

**Goal**: Perform partial correlation and regularized regression with FDR correction.

**Independent Test**: The analysis script runs on the full dataset, produces a CSV of correlation coefficients with p-values, and generates a scatter plot of predicted vs. actual BMRQ scores with a regression line and R² annotation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Contract test for results CSV schema in `tests/contract/test_results_schema.py`
- [ ] T024 [P] [US3] Integration test for statistical pipeline in `tests/integration/test_stats.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/analysis/stats.py`: Partial correlation analysis controlling for age, sex, and FD. Apply FDR correction (q<0.05).
- [ ] T027 [US3] Implement `src/analysis/stats.py`: Regularized linear regression (Ridge/Lasso/Elastic Net) with **5-fold cross-validation** to predict BMRQ scores. **Output**: `data/regression_cv_results.json` containing R², fold indices, and coefficients.
- [ ] T027b [US3] Implement `src/analysis/stats.py`: Fit and report a **null model (intercept only)** baseline. **Output**: `data/null_model_results.json` containing baseline R² for comparison with SC-002.
- [ ] T028 [US3] Implement visualization generation (scatter plots, network diagrams) in `src/analysis/visualize.py` (DEPENDS ON T026, T027, T027b).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` and `README.md`
- [ ] T031 Code cleanup and refactoring
- [ ] T032 Performance optimization for large matrix operations (streaming/chunking if needed)
- [ ] T033 [P] Additional unit tests in `tests/unit/test_metrics.py`
- [ ] T034 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T007 (Contracts) MUST precede T005 (Models)
 - T005 (Models) MUST precede T008 (Tests)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
 - T012c -> T012d -> T012e -> T013 (Data flow)
 - T018a/b/c -> T020b -> T021 -> T025 (Metric flow)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 merged dataset AND T025 Gate Pass
 - T025 (Power Gate) must return 'pass' before T026/T027 run

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (except T005/T008 which depend on T007/T005)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for download pipeline (N=1) in tests/integration/test_download.py"

# Launch all models for User Story 1 together:
Task: "Create Subject model in src/models/schemas.py"
Task: "Create ConnectivityMatrix model in src/models/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (N=1 validation)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Graph Metrics)
 - Developer C: User Story 3 (Stats)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: fMRIPrep is Off-CI; CI only validates logic with N=1 dry-run.
- **Critical**: No synthetic data. If BMRQ is missing in OpenNeuro ds000233, the pipeline halts with a Data Gap Report (T011b).
- **Critical**: T012c executes fMRIPrep; T012d validates output; T012e excludes motion; T013 consumes valid data.
- **Critical**: T018a/b/c produces metrics; T020b checks VIF; T021 merges edge-level features explicitly.
- **Critical**: T025 (Power Gate) must pass before US-3 begins.
- **Critical**: T027b fits null model for SC-002 comparison.
- **Critical**: T025b generates the final power analysis report for SC-005 verification.