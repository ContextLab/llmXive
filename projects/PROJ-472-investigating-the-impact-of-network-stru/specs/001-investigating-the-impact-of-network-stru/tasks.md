# Tasks: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Input**: Design documents from `/specs/001-network-structure-avalanche-dynamics/`
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

- [ ] T001 Create project directory structure: Create directories `projects/PROJ-472-investigating-the-impact-of-network-stru/`, `code/`, `data/raw/`, `data/processed/`, `tests/`, `tests/unit/`, `tests/integration/`.
- [ ] T002 Initialize Python 3.11 project: Create file `requirements.txt` containing pinned versions for `mne`, `nibabel`, `networkx`, `powerlaw`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `dask`, `openneuro-py`, `pytest`, `pytest-cov`.
- [ ] T003 [P] Configure environment configuration management for OpenNeuro credentials (if required)
- [ ] T004 [P] Configure linting and formatting tools
  - [ ] T004a [P] Create `pyproject.toml` configuration for ruff: Write the `[tool.ruff]` section to `pyproject.toml` with linting rules.
  - [ ] T004b [P] Create `pyproject.toml` configuration for black: Write the `[tool.black]` section to `pyproject.toml` with formatting rules.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup `data/raw` and `data/processed` directory structures with `.gitignore` rules
- [ ] T006 [P] Implement `code/config.py` with paths, random seeds (`np.random.seed`, `random.seed`), and hyperparameters
- [ ] T007 [P] Implement `code/utils/io.py` for SHA256 checksumming and logging infrastructure
- [ ] T008a [P] [Foundational] Implement `Participant` data class in `code/utils/models.py`
- [ ] T008b [P] [Foundational] Implement `StructuralConnectome` data class in `code/utils/models.py`
- [ ] T008c [P] [Foundational] Implement `AvalancheRecord` data class in `code/utils/models.py`
- [ ] T008d [P] [Foundational] Implement `CorrelationResult` data class in `code/utils/models.py`
- [ ] T009 Implement `code/main.py` orchestrator script structure
- [ ] T010 [P] [Foundational] Implement logic to run Reference-Validator Agent on dataset citations (if treated as citations) to satisfy Constitution Principle II

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Integration (Priority: P1) 🎯 MVP

**Goal**: Acquire and preprocess diffusion‑MRI structural connectomes and resting‑state EEG recordings from OpenNeuro HCP-Aging dataset (ds004230/31) into a unified participant‑indexed format.

**Independent Test**: Successfully download, preprocess, and store a subset of dMRI and EEG data for the available number of participants (even if < 50) with matching subject identifiers, and correctly generate a report of reduced statistical power if N < 50.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for OpenNeuro API connection and dataset listing in `tests/unit/test_download.py`
- [ ] T012 [P] [US1] Integration test for end-to-end data fetch and checksum verification in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T013a [P] [US1] Implement `code/data/download.py` function to fetch dMRI data from OpenNeuro ds004230
- [ ] T013b [P] [US1] Implement `code/data/download.py` function to fetch EEG data from OpenNeuro ds004231
- [ ] T014 [P] [US1] Implement `code/data/preprocess_dMRI.py` wrapper for MRtrix to generate multi-parcel structural connectivity matrices
- [ ] T015 [P] [US1] Implement `code/data/preprocess_EEG.py` using MNE-Python: band-pass filter low-frequency to a cutoff within the standard range for neural signal preservation, down-sample to a frequency within the standard range for neural signal preservation, ICA artifact removal
- [ ] T016 [US1] Implement `code/data/fuse_data.py` to match subjects between modalities and save unified participant-indexed CSV/Parquet (DEPENDS ON T013a, T013b, T014, T015)
- [ ] T017 [US1] Implement data quality filtering logic: exclude participants with >30% EEG channels removed OR disconnected structural graphs, and generate `data/processed/exclusion_report.txt` listing excluded participants and reasons (DEPENDS ON T016)
- [ ] T018 [US1] Implement power analysis logic: query the final matched sample size (N) from filtered data (output of T017), calculate statistical power, and generate `data/processed/power_analysis_report.json` explicitly reporting reduced power if N < 50 (DEPENDS ON T017)
- [ ] T019 [US1] Add logging for data pipeline operations and participant exclusion reasons

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Network and Avalanche Metric Computation (Priority: P2)

**Goal**: Compute canonical structural network metrics and neural avalanche statistics for all valid participants.

**Independent Test**: Compute metrics for a subset of participants and verify output values are within expected ranges for human brain networks and neural avalanches.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for graph metric calculations (degree, clustering) in `tests/unit/test_network.py`
- [ ] T021 [P] [US2] Unit test for avalanche detection and power-law fitting in `tests/unit/test_avalanche.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/metrics/network.py`: compute node-wise degree, mean clustering coefficient, and rich-club coefficient using NetworkX
- [ ] T023 [P] [US2] Implement `code/metrics/avalanche.py`: detect avalanches using 75th percentile threshold (per-channel), fixed time bin Δt = 4 ms
- [ ] T024a [US2] Implement power-law fitting function in `code/metrics/avalanche.py` using `powerlaw` package (DEPENDS ON T023)
- [ ] T024b [US2] Implement KS test validation logic in `code/metrics/avalanche.py` to validate fit against log-normal/exponential alternatives and explicitly save KS statistics/p-values to `data/processed/fit_validation.json` (DEPENDS ON T024a)
- [ ] T025 [US2] Implement export logic to save participant-level metrics (structural + avalanche) to `data/processed/metrics.csv` (DEPENDS ON T022, T023, T024a, T024b)
- [ ] T026 [US2] Add error handling for power-law convergence failures (exclude participant from downstream analysis)
- [ ] T027 [US2] Add logging for metric computation status and exclusion counts

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Association and Robustness Testing (Priority: P3)

**Goal**: Test for statistically robust associations between structural metrics and avalanche exponents with correction and sensitivity analysis.

**Independent Test**: Run association analysis on a subset and verify correlation coefficients, p-values, and sensitivity results are reproducible.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for Spearman correlation and bootstrap CI in `tests/unit/test_correlation.py`
- [ ] T029 [P] [US3] Integration test for permutation test and sensitivity sweep in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analysis/correlation.py`: Compute Spearman rank correlations between structural metrics and avalanche exponents, then immediately consume these coefficients as input to a non-parametric permutation test (a sufficient number of shuffles of raw subject labels) to generate a null distribution of Spearman coefficients and derive corrected p-values. Save results (coefficients, corrected p-values) to `data/processed/correlation_results.json` (DEPENDS ON Phase 4 outputs)
- [ ] T031 [P] [US3] Implement `code/analysis/robustness.py`: Sensitivity sweep logic for thresholds across a representative range of values.
- [ ] T032 [US3] Implement sensitivity analysis in `code/analysis/robustness.py`: run correlation for each threshold and report stability (DEPENDS ON T030, T031)
- [ ] T033 [US3] Implement `code/analysis/diagnostics.py`: Variance Inflation Factor (VIF) calculation for degree and clustering coefficient
- [ ] T034 [US3] Implement additional uncertainty-aware correlation analysis using Bootstrap uncertainty propagation (as per FR-006) to complement the primary Spearman/Permutation test (DEPENDS ON Phase 4 outputs)
- [ ] T035 [US3] Generate final results report framing findings as associational (not causal) per FR-010, including a verification step to ensure absence of causal language
- [ ] T035b [US3] Implement code-level enforcement of associational framing in output headers, log messages, and result object metadata
- [ ] T036 [US3] Add logging for statistical test parameters and result summary

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T038 Code cleanup and refactoring for memory efficiency (dask usage verification)
- [ ] T039 [US3] Implement runtime profiling logic in `code/main.py` to track execution time per phase
- [ ] T040 Verify total runtime ≤ 6 hours on GitHub Actions free-tier (2 CPU, 7 GB RAM) for N=50 subjects
- [ ] T041 [P] Additional unit tests for edge cases (empty datasets, fit failures)
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metric output

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
Task: "Unit test for [function] in tests/unit/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"

# NOTE: T016 (fuse_data) is NOT parallel with T013-T015; it must run AFTER them.
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
- **Compute Constraint**: All tasks must be executable on CPU-only free-tier runners (2 cores, ~7 GB RAM). No GPU/CUDA tasks allowed.
- **Data Integrity**: No synthetic data generation. All analysis must use real OpenNeuro ds004230/31 data.