# Tasks: Linking Resting‑State fMRI Entropy to Creative Problem Solving

**Input**: Design documents from `/specs/001-linking-resting-state-fmri-entropy/`
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

- [X] T001a Create directory: `code/`
- [X] T001b Create directory: `data/raw`
- [X] T001c Create directory: `data/processed`
- [X] T001d Create directory: `data/logs`
- [X] T001e Create directory: `tests/`
- [X] T001f Create directory: `docs/`
- [X] T002a Initialize `requirements.txt` file in repository root with empty content or header comment.
- [X] T002b Pin dependencies in `requirements.txt` with exact versions: `numpy==1.26.4`, `scipy==1.13.1`, `pandas==2.2.2`, `statsmodels==0.14.2`, `nibabel==5.2.1`, `scikit-learn==1.5.0`, `tqdm==4.66.4`, `requests==2.32.3`, `pytest==8.2.2`, `psutil==6.0.0`.

---

## Phase 2: Data Acquisition & Validation (Critical Path)

**Purpose**: Download and validate real data BEFORE any processing begins. This phase MUST precede all preprocessing and modeling.

**⚠️ CRITICAL**: No preprocessing or modeling can begin until data is acquired and validated.

- [X] T039 [US1] Implement `code/data_loader.py` function to download pre-processed HCP multi-dimensional volumes from OpenNeuro S3 bucket (ds000030) using `awscli` or `requests` with checksum verification
- [X] T040 [US1] Implement `code/data_loader.py` function to download `Creative_Problem_Solving.csv` phenotype file from verified HCP release source
- [X] T041 [US1] Add pre-computation validation step in `code/main.py` to verify downloaded data integrity and existence before running entropy calculations

---

## Phase 3: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to manage paths (`PHENOTYPE_PATH`, `RAW_DATA_DIR`), entropy parameters (`m=2`, `r=0.2*SD`), and motion thresholds (`FD > 0.2mm`)
- [X] T005 Implement `code/utils.py` for logging infrastructure, file I/O helpers, and VIF (Variance Inflation Factor) calculation logic
- [X] T006 [US1] Implement `code/data_loader.py` with functions to:
 1. **Validate existence** of `Creative_Problem_Solving.csv` and **halt execution** if missing (per FR-008)
 2. Load NIfTI volumes using `nibabel`
- [~] T007 [US1] Implement motion scrubbing in `code/data_loader.py` to filter time series based on FD, **exclude subjects with <100 remaining frames** (logging to `data/logs/missing_data.log`), and log FD-based exclusions to `data/logs/motion_exclusions.log` per FR-006. **Additionally, initiate the [deferred] invalid parcels check** by counting NaNs per subject during loading and logging counts to `data/logs/parcel_quality.log` (detailed flagging logic in T015b).
 - *Note: This task is sequential relative to T006. Internal loops over subjects may be parallelized, but the task produces a global list required by downstream tasks.*
- [ ] T007b [US1] Implement logic to **persist the list of valid subject IDs** to `data/processed/valid_subjects.csv` (CSV) so downstream tasks (T013, T022) can consume it. This file MUST be generated immediately after T007 completes.
- [ ] T008 Setup `tests/` directory structure and `conftest.py` for shared fixtures (sample data paths, mock entropy vectors)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 4: User Story 1 - Compute Global and Network-Specific Entropy Metrics (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed HCP fMRI data and compute Multiscale Sample Entropy (MSE) for whole brain and canonical networks (DMN, FPN, CON).

**Independent Test**: Run entropy module on a subset of subjects; verify output CSV contains non-null MSE values for all parcels and correct aggregation; verify motion-excluded subjects are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for vectorized Sample Entropy calculation in `tests/test_entropy.py` (verify against known small matrix)
- [X] T011 [P] [US1] Integration test for motion exclusion logic in `tests/test_data_loader.py` (verify subjects with FD > 0.2mm and <100 frames are skipped)
- [X] T012 [P] [US1] Integration test for AUC aggregation in `tests/test_entropy.py` (verify Area Under Curve calculation across scales)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement vectorized `compute_sample_entropy` function in `code/entropy.py` (CPU-optimized, no GPU dependencies, default precision)
- [X] T014 [P] [US1] Implement `compute_multiscale_entropy` in `code/entropy.py` to calculate entropy across multiple scales (1-20) and aggregate the result as the **Area Under the Curve (AUC) of the entropy-vs-scale profile** per FR-009
- [X] T015 [US1] Implement parcel-level processing loop in `code/entropy.py` to iterate over HCP 360-parcel atlas using **scrubbed time series from T007/valid_subjects.csv**, handling NaNs per FR-001.
 - **Input**: HCP Atlas definition file (external input).
 - **Output**: Per-parcel entropy values.
- [~] T015b [US1] Implement logic in `code/entropy.py` to **flag subjects for manual review if >10% of parcels are invalid** (NaN) and log to `data/logs/invalid_parcels.log` per Edge Cases. This task consumes the parcel counts logged in T007.
- [X] T016 [P] [US1] Implement `aggregate_networks` function in `code/aggregation.py` to map parcels to DMN, FPN, CON, and other networks using HCP atlas definitions
- [~] T017 [US1] Implement main entropy orchestration in `code/entropy.py` to process all valid subjects, handle chunking for memory constraints (<7GB RAM), and output `data/processed/entropy_metrics.csv`
- [~] T017b [US1] Implement instrumentation in `code/entropy.py` to **log peak RAM usage using `psutil`** for the full entropy computation run to `data/logs/ram_usage.log` per SC-003

**Surrogate Validation Sub-Phase (Required for Scientific Soundness per Plan.md Complexity Tracking)**
*Note: These tasks are part of US1 and must be completed for the entropy metric to be considered valid. They depend on raw data and entropy logic (T013-T017), not on US2/US3 results.*

- [ ] T042 [US1] Implement `code/sensitivity.py` function to generate phase-randomized surrogates of fMRI time series for a subset of subjects.
- [ ] T043 [US1] Implement entropy and model computation on surrogate data to validate non-linear structure, outputting `data/processed/surrogate_results.csv`.
- [ ] T044 [US1] Implement validation comparison logic in `code/sensitivity.py` to compare surrogate results against real data results. **Output**: `data/processed/surrogate_validation_report.csv` containing columns: `entropy_real`, `entropy_surrogate`, `difference`, `pass_flag` (PASS if difference > 10%). Log validation status per FR-010 (Scientific Soundness).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Fit Linear Regression Models with Covariates (Priority: P2)

**Goal**: Fit OLS models with robust standard errors to test entropy vs. creativity associations, controlling for age, sex, and motion.

**Independent Test**: Run modeling script on synthetic data with known coefficients; verify recovery of coefficients and p-values; verify sample size check (N < 30) halts execution.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for OLS coefficient recovery in `tests/test_modeling.py` (synthetic data with known slope)
- [ ] T020 [P] [US2] Unit test for robust standard error calculation (HC1) in `tests/test_modeling.py`
- [ ] T021 [P] [US2] Integration test for sample size guard in `tests/test_modeling.py` (verify N < 30 raises critical warning)

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `load_merged_data` in `code/modeling.py` to join `entropy_metrics.csv` with `Creative_Problem_Solving.csv` on subject ID, **filtering using `data/processed/valid_subjects.csv` generated by T007b**.
- [ ] T023 [US2] Implement VIF check in `code/modeling.py` to detect collinearity (VIF > 5) among predictors (age, sex, motion, entropy)
- [ ] T024 [US2] Implement OLS model fitting with `statsmodels` using `HC1` robust standard errors in `code/modeling.py`
- [ ] T025 [US2] Implement sample size validation logic to **HALT primary analysis** and log critical warning to `data/logs/safety_checks.log` if N < 30 per Edge Cases (preventing misleading p-values)
- [ ] T026 [US2] Implement result extraction to generate `data/processed/model_results_raw.csv` containing coefficients, SEs, t-stats, and **raw p-values only**. **Note**: This is a temporary file; final FDR-adjusted values are added in T029.
- [ ] T026b [US2] Implement instrumentation in `code/modeling.py` to **log peak RAM usage using `psutil`** for the full modeling run to `data/logs/ram_usage.log` per SC-003

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Apply Multiple-Comparison Correction and Sensitivity Analysis (Priority: P3)

**Goal**: Apply Benjamini-Hochberg FDR correction and perform sensitivity analysis on entropy tolerance parameter `r`.

**Independent Test**: Verify FDR adjusted p-values match manual calculation; verify sensitivity sweep output includes results for r values within a low-to-moderate range of SD.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Benjamini-Hochberg FDR implementation in `tests/test_modeling.py`
- [ ] T028 [P] [US3] Unit test for sensitivity sweep logic in `tests/test_modeling.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `apply_fdr_correction` in `code/modeling.py` using Benjamini-Hochberg procedure on network-specific p-values per FR-004. **Action**: Read `data/processed/model_results_raw.csv`, compute FDR-adjusted p-values, and write the final `data/processed/model_results.csv` containing **both** unadjusted and FDR-adjusted p-values per FR-007.
- [ ] T030a [US3] **Sensitivity Re-computation**: Re-execute **ONLY** the entropy computation logic (T013-T016) on **pre-scrubbed time series** (from T007) for each `r` value in {0.15*SD, 0.20*SD, 0.25*SD}.
 - **⚠️ DEPENDENCY**: Must wait for Phase 4 (entropy logic implementation) to be complete.
 - **Constraint**: Re-compute the **FULL Multiscale Sample Entropy profile (scales 1-20)** and aggregate via **AUC** for each `r` value. Do NOT re-run motion scrubbing (T007) or data loading (T006).
 - **Inputs**: `data/processed/valid_subjects.csv`, raw NIfTI files, entropy module code.
 - **Outputs**: `data/processed/entropy_metrics_r015.csv`, `entropy_metrics_r020.csv`, `entropy_metrics_r025.csv`.
- [ ] T030b [US3] Implement sensitivity modeling in `code/modeling.py` to re-fit OLS models using the sensitivity entropy artifacts from T030a and store results
- [ ] T031 [US3] Implement stability analysis logic to compare p-values across `r` sweeps and flag non-robust findings per FR-005
- [ ] T032 [US3] Generate final results table in `data/processed/final_results.csv` containing both unadjusted and FDR-adjusted p-values, and sensitivity metrics per FR-007
- [ ] T033 [US3] Implement instrumentation in `code/modeling.py` to **log peak RAM usage using `psutil`** for each sensitivity sweep iteration to `data/logs/sensitivity_ram.log` per SC-003. **Action**: Aggregate peak RAM across all sensitivity iterations (r=0.15, 0.20, 0.25) into a single summary metric in `data/logs/ram_usage_summary.log`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T034 [P] Documentation updates in `docs/` (README, usage examples)
- [ ] T035 Code cleanup and refactoring for memory efficiency (ensure no peak RAM > 6GB)
- [ ] T036 Performance optimization: profile entropy calculation and optimize vectorization if needed
- [ ] T037 [P] Additional unit tests for edge cases (NaN handling, empty datasets) in `tests/`
- [ ] T038 Run `quickstart.md` validation to ensure full pipeline execution on CPU-only runner

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Data Acquisition (Phase 2)**: No dependencies - MUST complete before Phase 3
- **Foundational (Phase 3)**: Depends on Phase 2 - BLOCKS all user stories
- **User Stories (Phase 4+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 3) and Data Acquisition (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 3) - Depends on US1 output (entropy metrics)
- **User Story 3 (P3)**: Can start after Foundational (Phase 3) - Depends on US2 output (model results) and US1 output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 3)
- Data Acquisition tasks can run in parallel with Setup if network bandwidth allows
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for vectorized Sample Entropy calculation in tests/test_entropy.py"
Task: "Integration test for motion exclusion logic in tests/test_data_loader.py"

# Launch all models for User Story 1 together:
Task: "Implement vectorized compute_sample_entropy function in code/entropy.py"
Task: "Implement parcel-level processing loop in code/entropy.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Data Acquisition
3. Complete Phase 3: Foundational
4. Complete Phase 4: User Story 1 (including Surrogate Validation T042-T044)
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Data Acquisition + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Data Acquisition + Foundational together
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
- **Compute Constraint**: All entropy tasks must run on CPU-only (cores, sufficient RAM); no GPU, no 8-bit quantization, no large model loading.
- **Data Constraint**: All data must be real (HCP/OpenNeuro); no synthetic/fake data generation for final results.
- **Validation Constraint**: Sensitivity analysis must sweep `r` while keeping scale range FIXED (1-20) but re-computing the FULL AUC profile.
- **Sensitivity Constraint**: Full multiscale re-computation is required for each `r` value in sensitivity analysis (T030a), but ONLY on pre-scrubbed data (no re-scrubbing).
- **RAM Constraint**: Peak RAM must be logged using `psutil` for all major phases (T017b, T026b, T033) and aggregated for sensitivity sweeps.