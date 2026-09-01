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

- [ ] T001 [P] [US0] Create root directories: `src/`, `tests/`, `data/`, `reports/`, `docs/`, `scripts/`, `state/`.
- [ ] T002 [P] [US0] Create source and test subdirectories: `src/data`, `src/analysis`, `src/stats`, `src/config`, `src/utils`, `src/entities`, `tests/unit`, `tests/integration`.
- [X] T003 [P] [US0] Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, nibabel, pyentropy, statsmodels, nilearn, scikit-learn, tqdm, linearmodels).
- [X] T004 [P] [US0] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining specific rules (e.g., line-length=88, target-version=py311).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T005 [P] [US0] Setup `data/` directory structure and `data/checksums.txt` logging mechanism. **Depends on T001, T002**.
- [ ] T006 [P] [US0] Implement robust environment variable management in `src/config/env_manager.py`: Check for `HCP_TOKEN` env var. **Validation Rule**: Raise `ValueError` if token is missing OR if `len(token) < 20` or `not token.startswith("hcp_")`. **Note**: This task must complete before T012 (HCP S3 Downloader) can proceed, despite being marked [P] for parallel implementation.
- [ ] T007 [P] [US0] Setup logging infrastructure in `src/utils/logging_config.py`: Define log format as `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and configure output to `logs/pipeline.log` and console. **Note**: Validates logging configuration for the entire pipeline.
- [ ] T008 [P] [US0] Create base data entities in `src/entities/models.py`: Define `Subject` class (attributes: subject_id, dsrt_score, age, sex, mean_fd) and `Parcel` class (attributes: parcel_id, time_series).
- [ ] T009 [P] [US0] Configure deterministic random seed handling: Create `src/utils/seed_manager.py` to set `numpy.random.seed(42)`, `random.seed(42)`, and environment variable `PYTHONHASHSEED=42`. This module MUST be imported and called in all stochastic tasks (T012, T020, T029) before any random operations.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition & Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HCP resting-state fMRI parcellated time series and DSRT scores for a subset of subjects, filter high-motion subjects (FD ≥ 0.2mm), and ensure data quality.

**Independent Test**: Verify the download of a a subset of subjects and confirm the exclusion of subjects with mean framewise displacement (FD) ≥ 0.2mm.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for HCP credential validation in `tests/unit/test_data_download.py`. **Note**: Validates the specific credential check logic implemented in T012 (checking for `HCP_TOKEN` and raising on missing/invalid).
- [X] T011 [P] [US1] Unit test for motion threshold exclusion logic in `tests/unit/test_qc.py`. **Note**: Validates the specific filtering logic implemented in T014 (exclusion of subjects with mean FD ≥ 0.2mm).

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement HCP S3 downloader in `src/data/download_hcp.py` to fetch **minimally preprocessed 4mm parcellated time series** and behavioral data for N=200 subjects, selecting subjects deterministically using a fixed random seed. **Note**: Data is already 4mm; no resampling required.
- [ ] T013 [US1] Implement data validation script in `src/data/validate_data.py` to check for required columns (subject_id, DSRT, age, sex, mean_fd). **Handling Logic**: If DSRT is missing (NaN/null), **drop rows** and log the exclusion count to `data/validation_report.txt`. If required columns are missing entirely, exit with code 1 and log to `data/validation_report.txt`.
- [ ] T014 [US1] Implement motion quality control filter in `src/data/filter_motion.py` to process downloaded data: 1) Create `data/cleaned/full_clean.parquet` (all subjects with valid DSRT). 2) Create `data/cleaned/low_motion_subset.parquet` (subjects with mean FD < 0.2mm). Log exclusion counts for both outputs.
- [ ] T015 [US1] Create aggregated clean dataset in `data/cleaned/subjects_200_filtered.parquet` with schema: [subject_id, DSRT, age, sex, mean_fd], encoding UTF-8. **Selection Logic**: Select the **first 200 subjects** from the list sorted by `subject_id` (after T012 download) to ensure determinism. **Note**: This is a derived artifact; must be checksummed in `data/checksums.txt` and `state/projects/...yaml`.
- [ ] T016 [US1] Generate checksum for all **downloaded** raw artifacts and append to `data/checksums.txt`
- [ ] T017 [US1] Generate checksum for **derived** intermediate files `data/cleaned/full_clean.parquet` and `data/cleaned/low_motion_subset.parquet` and append to `data/checksums.txt`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiscale Entropy Computation (Priority: P2)

**Goal**: Compute multiscale sample entropy (mSE) for each cortical parcel across the valid subject cohort, averaging across scales m=1–5.

**Independent Test**: Run entropy computation on a small test dataset (a small number of subjects) and verify output shape matches (subjects × parcels).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for mSE calculation on synthetic time series in `tests/unit/test_entropy.py`
- [ ] T019 [P] [US2] Integration test for parcel-wise processing loop in `tests/integration/test_entropy_pipeline.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement multiscale sample entropy function in `src/analysis/entropy.py` to compute entropy for **scales 1 through 5**, using **embedding dimension m=2** and tolerance **r=0.15**. **Note**: Explicitly distinguishes embedding dimension (m=2) from scale range (1-5).
- [ ] T021 [US2] Implement parcel-wise processing loop in `src/analysis/compute_entropy.py` to handle parcels in batches of **50 parcels per batch** to ensure peak RAM usage does not exceed **4GB**. **Note**: This task supports parallel processing of batches if memory allows. Implement chunking logic to process N parcels per batch.
- [ ] T022 [US2] Implement logic to flag and handle parcels with insufficient timepoints (invalid flagging): Append invalid parcel IDs to `data/derived/invalid_parcels.csv`.
- [ ] T023 [US2] Generate averaged entropy metric by **explicitly averaging across scales 1-5** per parcel per subject and save to `data/derived/entropy_matrix.csv` (subjects × parcels). **Note**: This task replaces T024.
- [X] T024 [US2] (Merged into T023) Removed.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling & Reporting (Priority: P3)

**Goal**: Fit mass-univariate linear models per parcel, perform permutation-based FWE correction, and generate the final report with power analysis, robustness checks, and sensitivity checks.

**Independent Test**: Run the statistical model on the computed entropy data and verify the output includes a PDF report, a NIfTI map of significant parcels, and a power analysis section.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for Mixed Effects model fitting and VIF calculation in `tests/unit/test_stats.py`
- [ ] T026 [P] [US3] Unit test for max-t permutation logic in `tests/unit/test_permutations.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement Variance Inflation Factor (VIF) calculation for covariates (Age, Sex, Mean FD) in `src/stats/collinearity.py` using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Note**: {{claim:c_3bc8eae0}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) (SC-005).
- [ ] T028 [US3] Implement mass-univariate **Linear Mixed Effects (MixedLM)** model per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD + (1|Subject)`) in `src/stats/model_fitting.py`. **Note**: **SPEC FR-004 MANDATES MixedLM with Subject random effect. This overrides the contradictory OLS instruction in Plan.md Summary and Phase 3.** Use `statsmodels` MixedLM.
- [ ] T029 [US3] Implement Freedman-Lane permutation test (exactly **5,000 iterations**) in `src/stats/permutation_test.py` with a fixed random seed for shuffling. Explicitly construct the max-statistic null distribution across all parcels for FWE correction per FR-005. Include timeout monitoring.
- [ ] T030 [US3] Implement FWE correction logic to threshold p-values at < 0.05 and generate `data/results/corrected_pvalues.csv` containing FWE-adjusted p-values.
- [ ] T031 [US3] Implement post-hoc power analysis (F-test) in `src/stats/power_analysis.py` to calculate power for effect size d=0.3. Save raw metrics to `data/results/power_metrics.json` and explicitly flag the study as 'Underpowered' in the report if Power < 0.80.
- [ ] T032 [US3] Generate parcel-wise NIfTI map of significant clusters in `data/results/significant_map.nii.gz`
- [ ] T033 [US3] **Sensitivity Analysis Driver**: Create a wrapper script in `src/stats/sensitivity_driver.py` that orchestrates the full pipeline. **Grid**: `r ∈ {0.1, 0.15, 0.2}` (Tolerance) and `m ∈ {2, 3, 4}` (Embedding Dimension). **Constraint**: Keep **Scale Range fixed at 1–5** for all grid points (per FR-003). **Logic**: For each grid point (r, m), re-run entropy computation (T020) with `embedding_dim=m` and `tolerance=r`, keeping `scales=range(1, 6)`. **Output**: Aggregate results into `data/results/sensitivity_grid.csv` with columns: [r, m, num_significant_parcels, max_beta, mean_p_value]. **Note**: Uses N=500 permutations per grid point to ensure total runtime stays within CI limit. **Note**: This is a separate analysis branch; outputs do not overwrite the primary entropy matrix.
- [ ] T034 [US3] **Main Pipeline Execution**: Execute the full statistical pipeline (T028-T032) on the `data/cleaned/low_motion_subset.parquet` dataset to generate the primary results. **Note**: Uses low-motion subset to satisfy FR-002. **Note**: Spec FR-004 (MixedLM) overrides Plan.md (OLS).
- [ ] T035 [US3] **Robustness Re-run (Separate Branch)**: Execute the full statistical pipeline (T028-T032) on the `data/cleaned/full_clean.parquet` dataset (all valid DSRT, **unfiltered by motion**). **Instruction**: **Skip the motion filtering step (FD < 0.2mm)** and use all subjects with valid DSRT. Generate a comparative report in `reports/robustness_check.pdf`. **Constraint**: This is strictly a robustness comparison; do not merge these results with the primary analysis (T034/T036). Justified by Constitution Principle VI (Neuroimaging Motion Control) to compare low-motion vs full-clean results.
- [ ] T036 [US3] Generate final PDF report in `reports/analysis_report.pdf` including associational framing, power analysis (with underpowered flag if applicable), sensitivity tables (comparing baseline vs. grid), and robustness check results.
- [ ] T037 [US3] Update `state/projects/PROJ-754-...yaml` with SHA-256 hashes of all final artifacts

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] [US0] Documentation updates: Create `docs/entropy_method.md` with sections: 'Parameters', 'Dependencies', 'Algorithm', 'Reproducibility'.
- [ ] T039 [US0] Refactoring: Extract data loading logic into `src/data/loader.py` to improve modularity.
- [ ] T040 [P] [US0] Performance optimization for the permutation loop using joblib with n_jobs=2 (or optimized serial if 2 cores unavailable)
- [ ] T041 [P] [US0] Additional unit tests for edge cases in `tests/unit/test_edge_cases.py`: Include `test_empty_dataset`, `test_timeout_trigger`, `test_missing_column`.
- [ ] T042 [US0] Execute `scripts/validate_quickstart.sh` and ensure exit code 0.

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
- **Critical Constraint**: All tasks must run on CPU-only CI (A minimal virtual environment configured with a small number of CPU cores, a moderate amount of RAM, and limited disk space.). No GPU, no 8-bit quantization, no large model loading.
- **Data Integrity**: All analysis tasks must use real HCP data downloaded via T012. No synthetic data fabrication.
- **Sensitivity Analysis**: Task T033 is a driver that re-runs the pipeline with reduced permutations for grid points to fit within 6 hours. **Logic corrected to test discrete scale points m=3, 5, 7** -> **Corrected to test embedding dimension m ∈ {2, 3, 4} with fixed scale range 1-5**.
- **Model Architecture**: Task T028 implements Mass-Univariate MixedLM per parcel to satisfy Spec FR-004. **Overrides Plan.md OLS instruction**. **Plan.md flagged for correction**.
- **Power Analysis**: Task T031 includes explicit logic to flag the study as underpowered if Power < 0.80.
- **Robustness**: T035 runs on `full_clean` (unfiltered) while T034 runs on `low_motion_subset` (filtered), enabling valid comparison and satisfying FR-002 for the primary analysis.
- **Plan Correction**: The `plan.md` summary and Phase 3 description incorrectly specify OLS. The implementation MUST follow Spec FR-004 (MixedLM). This task list reflects the Spec requirement.