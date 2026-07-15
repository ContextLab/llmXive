# Tasks: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Input**: Design documents from `/specs/001-linking-resting-state-fmri-entropy-to-re/`
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

- [ ] T001 Create project structure per implementation plan <!-- FAILED: unspecified -->
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, nibabel, pyentropy, statsmodels, nilearn, scikit-learn, tqdm)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [ ] T004 Setup `data/` directory structure and `data/checksums.txt` logging mechanism <!-- SKIPPED: non-mapping output -->
- [ ] T005 [P] Implement robust environment variable management (HCP_TOKEN) with graceful failure on missing credentials
- [ ] T006 [P] Setup logging infrastructure to record subject exclusions and processing steps
- [ ] T007 Create base data entities (Subject, Parcel) in `src/entities/`
- [ ] T008 Configure deterministic random seed handling for all stochastic processes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition & Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HCP resting-state fMRI parcellated time series and DSRT scores for a subset of subjects., filter high-motion subjects (FD ≥ 0.2mm), and ensure data quality.

**Independent Test**: Verify the download of a a subset of subjects and confirm the exclusion of subjects with mean framewise displacement (FD) ≥ 0.2mm.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for HCP credential validation in `tests/unit/test_data_download.py`
- [ ] T011 [P] [US1] Unit test for motion threshold exclusion logic (FD ≥ 0.2mm) in `tests/unit/test_qc.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement HCP S3 downloader in `src/data/download_hcp.py` to fetch Spatially parcellated time series and behavioral data for N=200 subjects, selecting subjects deterministically using random seed 42
- [ ] T013 [US1] Implement data validation script in `src/data/validate_data.py` to check for required columns (subject_id, DSRT, age, sex, mean_fd) and handle missing DSRT
- [ ] T014 [US1] Implement motion quality control filter in `src/data/filter_motion.py` to exclude subjects with mean FD ≥ 0.2mm and log exclusion counts
- [ ] T015 [US1] Create aggregated clean dataset CSV/Parquet in `data/cleaned/subjects_200_filtered.csv`
- [ ] T016 [US1] Generate checksum for all **downloaded** raw artifacts and append to `data/checksums.txt`
- [ ] T017 [US1] Generate checksum for **derived** intermediate file `data/cleaned/subjects_200_filtered.csv` and append to `data/checksums.txt`
- [ ] T018 [US1] Implement resampling pipeline in `src/data/resample_to_4mm.py` to interpolate standard HCP parcellated time series to 4mm resolution, ensuring FR-003 input validity
- [ ] T019 [US1] Implement residual noise variance computation in `src/data/compute_noise_variance.py` to derive the noise-variance covariate required by FR-009, outputting to `data/derived/noise_variance.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiscale Entropy Computation (Priority: P2)

**Goal**: Compute multiscale sample entropy (mSE) for each cortical parcel across the valid subject cohort, averaging across scales m=1–5.

**Independent Test**: Run entropy computation on a small test dataset (a small number of subjects) and verify output shape matches (subjects × parcels).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for mSE calculation on synthetic time series in `tests/unit/test_entropy.py`
- [ ] T019 [P] [US2] Integration test for parcel-wise processing loop in `tests/integration/test_entropy_pipeline.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement multiscale sample entropy function (scales 1–5) using `pyentropy` in `src/analysis/entropy.py` with default parameters: embedding dimension m=2, tolerance r=0.15
- [ ] T021 [US2] Implement parcel-wise processing loop in `src/analysis/compute_entropy.py` to handle one parcel at a time, ensuring peak RAM usage does not exceed a defined threshold. This task is NOT parallel-safe and must run serially.
- [ ] T022 [US2] Implement logic to flag and handle parcels with insufficient timepoints (invalid flagging)
- [ ] T023 [US2] Generate averaged entropy metric by **explicitly averaging across scales** per parcel per subject
- [ ] T024 [US2] Save final entropy matrix to `data/derived/entropy_matrix.csv` (subjects × parcels)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling & Reporting (Priority: P3)

**Goal**: Fit mass-univariate Mixed-Effects Models per parcel, perform permutation-based FWE correction, and generate the final report with power analysis, robustness checks, and sensitivity checks.

**Independent Test**: Run the statistical model on the computed entropy data and verify the output includes a PDF report, a NIfTI map of significant parcels, and a power analysis section.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for MixedLM model fitting and VIF calculation in `tests/unit/test_stats.py`
- [ ] T026 [P] [US3] Unit test for max-t permutation logic in `tests/unit/test_permutations.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement Variance Inflation Factor (VIF) calculation for covariates and {{claim:c_ca86a376}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) in `src/stats/collinearity.py`
- [ ] T028 [US3] Implement mass-univariate **Mixed-Effects Model (MixedLM)** fitting (`DSRT ~ Entropy + Age + Sex + MeanFD + NoiseVariance + (1|Subject)`) in `src/stats/model_fitting.py`. Subject ID is used as a random effect (1|Subject) per Spec FR-004.
- [ ] T029 [US3] Implement Freedman-Lane permutation test (A sufficient number of iterations, max-t statistic) in `src/stats/permutation_test.py` with random seed 42 for shuffling. Explicitly construct the max-statistic null distribution across all parcels for FWE correction per FR-005 and Constitution VII. Include timeout monitoring.
- [ ] T030 [US3] Implement FWE correction logic to threshold p-values at < 0.05
- [ ] T031 [US3] Implement post-hoc power analysis (F-test) in `src/stats/power_analysis.py` to calculate power for effect size d=0.3. Explicitly flag the study as 'Underpowered' in the report if Power < 0.80.
- [ ] T032 [US3] Generate parcel-wise NIfTI map of significant clusters in `data/results/significant_map.nii.gz`
- [ ] T033a [US3] **Define Baseline**: Create a configuration script in `src/stats/sensitivity_baseline.py` that explicitly defines the primary baseline parameters: r=0.15, m=1-5 (averaged), A large number of permutations.
- [ ] T033b [US3] **Implement Sensitivity Driver**: Create a wrapper script in `src/stats/sensitivity_driver.py` that orchestrates re-runs of T028-T032 for the full x grid of parameters: `r ∈ {0.1, 0.15, 0.2}` AND `m ∈ {3, 5, 7}`. Implement logic to monitor total runtime; if the grid exceeds 5 hours, dynamically reduce the number of permutations to a lower magnitude for subsequent runs and log the reduction.
- [ ] T034 [US3] Implement robustness check: Re-run the full statistical pipeline (T028-T032) on the **low-motion subset (FD < 0.2mm)** and generate a comparative report in `reports/robustness_check.pdf`. Justified by Constitution Principle VI (Neuroimaging Motion Control).
- [ ] T035 [US3] Generate final PDF report in `reports/analysis_report.pdf` including associational framing, power analysis (with underpowered flag if applicable), sensitivity tables, and robustness check results.
- [ ] T036 [US3] Update `state/projects/PROJ-754-...yaml` with SHA-256 hashes of all final artifacts

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` explaining the entropy calculation and permutation method
- [ ] T038 Code cleanup and refactoring of data loading utilities
- [ ] T039 Performance optimization for the permutation loop using joblib with n_jobs=2 (or optimized serial if 2 cores unavailable)
- [ ] T040 [P] Additional unit tests for edge cases (empty datasets, timeout triggers) in `tests/unit/`
- [ ] T041 Run quickstart.md validation to ensure full pipeline execution fits within 6 hours

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (clean data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (entropy matrix)

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
Task: "Unit test for HCP credential validation in tests/unit/test_data_download.py"
Task: "Unit test for motion threshold exclusion logic in tests/unit/test_qc.py"

# Launch all models for User Story 1 together:
Task: "Create base data entities in src/entities/"
Task: "Setup environment variable management in src/config/"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Entropy)
 - Developer C: User Story 3 (Stats)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (A minimal virtual environment configured with a small number of CPU cores, a moderate amount of RAM, and 14GB disk.). No GPU, no 8-bit quantization, no large model loading.
- **Data Integrity**: All analysis tasks must use real HCP data downloaded via T012. No synthetic data fabrication.
- **Sensitivity Analysis**: Task T033b is a driver that re-runs the pipeline 9 times; ensure CI resources are allocated accordingly. If runtime exceeds 5 hours, permutations are reduced to a documented fallback threshold.
- **Model Architecture**: Task T028 implements Mixed-Effects Model (MixedLM) with (1|Subject) random effect as explicitly mandated by Spec FR-004.
- **Noise Covariate**: Task T019 computes residual noise variance, which is included as a covariate in T028 to satisfy FR-009.
- **Resampling**: Task T018 ensures 4mm parcellated time series are generated from standard HCP data to satisfy FR-003.
- **Power Analysis**: Task T031 includes explicit logic to flag the study as underpowered if Power < 0.80.