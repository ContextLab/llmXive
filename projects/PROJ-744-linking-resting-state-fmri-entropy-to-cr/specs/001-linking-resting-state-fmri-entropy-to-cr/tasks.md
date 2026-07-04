# Tasks: Linking Resting‑State fMRI Entropy to Creative Problem Solving

**Input**: Design documents from `/specs/001-linking-resting-state-fmri-entropy-to-cr/`
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

- [ ] T001a [P] Create project directory structure: `code/`, `tests/`, `data/`, `results/`, `docs/`, `specs/`
- [ ] T001b [P] Create sub-directories: `code/ingestion`, `code/entropy`, `code/modeling`, `code/utils`, `code/benchmark`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scikit-learn, statsmodels, nibabel, requests, tqdm, h5py, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Setup data directory structure (`data/raw`, `data/processed`, `results/`) and `.gitignore` for large files
- [ ] T005 [P] Implement robust logging infrastructure in `code/utils/logging.py` (JSON formatted, file + console handlers)
- [ ] T006 [P] Create base configuration manager for parameters (m, r, scales) in `code/utils/config.py`
- [ ] T007 [P] Implement checksum verification utility in `code/utils/checksum.py` for FR-001
- [ ] T008 [P] Setup environment variable management for S3 credentials in `code/utils/env_loader.py`
- [ ] T009 [P] Create base schema definitions in `specs/contracts/` (dataset, entropy, association result)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download pre-processed HCP fMRI data and phenotypes, apply atlas, and extract clean time series.

**Independent Test**: The system can be tested by verifying that the script successfully retrieves a sample of subjects, extracts parcel time series per subject, and outputs a clean CSV containing the global mean entropy and all covariates, without requiring any downstream statistical modeling.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for S3 download retry logic with exponential backoff (max 3 retries) in `tests/unit/test_download_hcp.py`
- [ ] T011 [P] [US1] Integration test for parcellation dimensionality check in `tests/integration/test_parcellate.py`
- [ ] T012 [P] [US1] Test for motion flagging logic (FD > 0.2mm) in `tests/unit/test_motion_check.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/ingestion/download_hcp.py` to fetch 4-D volumes and phenotypes from OpenNeuro S3 with SHA-256 checksum verification (via manifest) and exponential backoff retry logic (max 3 times) per Edge Cases. Tested by T010.
- [ ] T014 [US1] Implement `code/ingestion/parcellate.py` to apply HCP 360-parcel atlas using `nibabel` (FR-002)
- [ ] T015 [US1] Implement `code/utils/motion_check.py` to calculate Framewise Displacement and flag subjects with threshold > 0.2 mm (Edge Case)
- [ ] T016 [US1] Implement data cleaning pipeline in `code/ingestion/clean.py` to consume the output of T013 (phenotypes) and T014 (time series), excluding rows with missing NIH Toolbox scores or incomplete fMRI scans (Edge Case), and logging excluded subjects to a separate report.
- [ ] T017 [US1] Create output CSV generator for `data/processed/subject_timeseries.csv` with columns: subject_id, age, sex, FD, nih_score, and flattened parcel values

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entropy Computation and Aggregation (Priority: P2)

**Goal**: Compute Multiscale Sample Entropy (MSE) for each parcel and derive global/network metrics.

**Independent Test**: The system can be tested by running the entropy calculation on a fixed subset of subjects with known parameters, verifying that the computed MSE values match a pre-calculated reference file within an appropriate tolerance, and that network aggregation correctly averages the parcel values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for MSE vectorized algorithm against **pre-calculated reference file** within **tolerance 1e-6** in `tests/unit/test_mse.py`
- [ ] T019 [P] [US2] Test for network aggregation logic (DMN mean of 60 parcels) in `tests/unit/test_aggregation.py`
- [ ] T020 [P] [US2] Test for NaN handling (median replacement) in `tests/unit/test_entropy_cleaning.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/entropy/mse.py` with vectorized Sample Entropy algorithm (m=2, r=0.2, scales 1-20) optimized for CPU (FR-003). Must generate and use a pre-calculated reference file for verification.
- [ ] T022 [US2] Implement `code/entropy/aggregate.py` to compute global mean and network-specific averages (DMN, FPN, etc.) (FR-004)
- [ ] T023 [US2] Implement Coefficient of Variation (CV) calculation per subject for SC-006 in `code/entropy/aggregate.py`
- [ ] T024 [US2] Implement robust NaN handling: replace flat-time-series NaNs with parcel median across subjects
- [ ] T025 [US2] Generate `data/processed/entropy_metrics.csv` with columns: subject_id, global_entropy, network_entropy_*

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Inference (Priority: P3)

**Goal**: Fit robust linear regression models, apply FDR correction, and perform sensitivity/reverse checks.

**Independent Test**: The system can be tested by running the modeling pipeline on a synthetic dataset where the relationship between entropy and creativity is known, and verifying that the model recovers a statistically significant positive coefficient with the correct p-value range.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for RLM HC3 standard errors against statsmodels reference in `tests/unit/test_robust_regression.py`
- [ ] T027 [P] [US3] Test for Benjamini-Hochberg FDR correction logic in `tests/unit/test_fdr_correction.py`
- [ ] T028 [P] [US3] Test for reverse-causality check (non-significant result) in `tests/unit/test_reverse_causality.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/modeling/robust_regression.py` using `statsmodels` RLM with HC3 SE (FR-005). **Staged Deviation**: Replaces Constitution Principle VII (LMM) with RLM as documented in plan.md; pending formal amendment ratification.
- [ ] T030 [US3] Implement `code/modeling/fdr_correction.py` for Benjamini-Hochberg correction on network p-values. **Replaces FR-006**: This task implements BH-FDR instead of the Spec's 'permutation-based cluster correction' as documented in plan.md (Constitution Check) due to methodological invalidity for N=6. **Staged Deviation** from Spec FR-006.
- [ ] T031 [US3] Implement `code/modeling/sensitivity.py` to sweep r parameter {0.15, 0.20, 0.25} and compute stability scores (FR-007)
- [ ] T032 [US3] Implement reverse-causality check in `code/modeling/reverse_check.py` (swap X/Y) (FR-009). **Note**: This tests correlation symmetry, not causality. The Spec's 'confirm directionality' is interpretive; output must report p-values to show symmetry, not causal proof.
- [ ] T033 [US3] Generate final `results/association_results.csv` with coefficient, SE, p-value, adjusted p-value, and stability metrics
- [ ] T034 [US3] Generate `results/data_completeness_report.json` confirming ≥95% valid parcels (SC-005). Must exit with code 1 if threshold < 95%.
- [ ] T035 [US3] Implement `code/modeling/enforce_completeness.py` to trigger exclusion logic and halt pipeline if `data_completeness_report.json` indicates <95% validity (SC-005 enforcement).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish, Benchmarking & Reporting

**Purpose**: Performance verification, documentation, and final artifact generation

- [ ] T036 [P] Implement `code/benchmark/benchmark.sh` to measure wall-clock time and memory for N=1000 subjects (FR-008)
- [ ] T037 [P] Run full pipeline on N=1000 subset in CI and verify ≤45 min runtime (SC-004). Note: This depends on completion of all prior phases.
- [ ] T038 [P] Update `specs/contracts/` schemas with final output fields from `association_results.csv`
- [ ] T039 [P] Generate `docs/quickstart.md` with step-by-step execution guide
- [ ] T040 [P] Update `docs/research.md` with empirical findings and limitations
- [ ] T041 [P] Write final `README.md` section for this feature branch

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (time series)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (entropy metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
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
Task: "Unit test for S3 download retry logic in tests/unit/test_download_hcp.py"
Task: "Integration test for parcellation dimensionality check in tests/integration/test_parcellate.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion/download_hcp.py"
Task: "Implement code/ingestion/parcellate.py"
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
- **CRITICAL**: All entropy calculations must use CPU-only, vectorized implementations to meet FR-008 (45 min limit). No GPU/CUDA allowed.
- **CRITICAL**: Ensure data flow: Download (US1) → Parcellation (US1) → Entropy (US2) → Modeling (US3). Do not reorder.
- **Staged Deviations**: Tasks T029, T030, and T032 contain explicit notes where the Plan deviates from the Spec or Constitution. These deviations are documented as necessary scientific corrections and are pending formal amendment ratification.