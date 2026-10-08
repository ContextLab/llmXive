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

- [ ] T001 [US0] Initialize project directories and verification artifact: Create root directories `src/`, `tests/`, `data/`, `reports/`, `docs/`, `scripts/`, `state/`. **Action**: Execute a Python script `scripts/init_dirs.py` that creates these directories if missing and writes a JSON file `data/directories_verified.json` containing a timestamp and a list of created paths. **Validation Rule**: CI must verify `data/directories_verified.json` exists and contains the expected keys. **Note**: This task blocks all user stories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T003 [P] [US0] Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, nibabel, pyentropy, statsmodels, nilearn, scikit-learn, tqdm, linearmodels).
- [X] T004 [P] [US0] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining specific rules (e.g., line-length=88, target-version=py311).
- [ ] T005 [P] [US0] Setup `data/` directory structure and `data/checksums.txt` logging mechanism. **Depends on T001**.
- [ ] T006 [US0] Implement robust environment variable management in `src/config/env_manager.py`: Check for `HCP_TOKEN` env var. **Validation Rule**: Raise `ValueError` if token is missing OR if `len(token) < 20` or `not token.startswith("hcp_")`. **Note**: This task must complete before T012 (HCP S3 Downloader) can proceed. **Execution Order**: Sequential dependency on T012.
- [ ] T007 [P] [US0] Setup logging infrastructure in `src/utils/logging_config.py`: Define log format as `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and configure output to `logs/pipeline.log` and console. **Note**: Validates logging configuration for the entire pipeline.
- [ ] T008 [P] [US0] Create base data entities in `src/entities/models.py`: Define `Subject` class (attributes: subject_id, dsrt_score, age, sex, mean_fd) and `Parcel` class (attributes: parcel_id, time_series).
- [ ] T009 [US0] Configure deterministic random seed handling: Create `src/utils/seed_manager.py` to set `numpy.random.seed(42)`, `random.seed(42)`, and environment variable `PYTHONHASHSEED=42`. **Note**: This module MUST be imported and called in all stochastic tasks (T012, T020, T029) BEFORE any random operations occur. **Execution Order**: Sequential dependency on T012, T020, T029. **Constraint**: Do NOT mark as [P] as it must run before dependent tasks.

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

- [ ] T012 [US1] Implement HCP S3 downloader in `src/data/download_hcp.py` to fetch **minimally preprocessed 4mm parcellated time series** and behavioral data for N=200 subjects, selecting subjects deterministically using a fixed random seed. **Note**: Data is already 4mm; no resampling required. **Depends on T006, T009**.
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

- [ ] T020 [US2] Implement multiscale sample entropy function in `src/analysis/entropy.py` to compute entropy for **scales 1 through 5**, using **embedding dimension m=2** and tolerance **r=0.15** (baseline configuration). **Note**: Explicitly distinguishes embedding dimension (m=2) from scale range (1-5). **Scope**: This task implements the **baseline** configuration only. The sensitivity analysis (T033) will sweep r and scale parameters.
- [ ] T021 [US2] Implement parcel-wise processing loop in `src/analysis/compute_entropy.py` to handle parcels in batches of **50 parcels per batch** to ensure peak RAM usage does not exceed **4GB**. **Note**: This task supports parallel processing of batches if memory allows. Implement chunking logic to process N parcels per batch.
- [ ] T022 [US2] Implement logic to flag and handle parcels with insufficient timepoints (invalid flagging): Append invalid parcel IDs to `data/derived/invalid_parcels.csv`.
- [ ] T023 [US2] Generate averaged entropy metric by **explicitly averaging across scales 1-5** per parcel per subject and save to `data/derived/entropy_matrix.csv` (subjects × parcels). **Note**: This task replaces T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling & Reporting (Priority: P3)

**Goal**: Fit mass-univariate linear models per parcel, perform permutation-based FWE correction, and generate the final report with power analysis, robustness checks, and sensitivity checks.

**Independent Test**: Run the statistical model on the computed entropy data and verify the output includes a PDF report, a NIfTI map of significant parcels, and a power analysis section.

**⚠️ CONTRADICTION ALERT**: The `plan.md` Summary and Phase 3 description incorrectly specify "Ordinary Least Squares (OLS)" regression. **Spec FR-004 MANDATES** a "Linear Mixed Effects (MixedLM)" model with a random effect `(1|Subject)`. The tasks below implement **MixedLM** to satisfy the Spec. The Plan.md must be flagged for correction in the next review cycle.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for Mixed Effects model fitting and VIF calculation in `tests/unit/test_stats.py`
- [ ] T026 [P] [US3] Unit test for max-t permutation logic in `tests/unit/test_permutations.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement Variance Inflation Factor (VIF) calculation for covariates (Age, Sex, Mean FD) in `src/stats/collinearity.py` using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Note**: (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) (SC-005).
- [ ] T028 [US3] Implement mass-univariate **Linear Mixed Effects (MixedLM)** model per parcel (`DSRT ~ Entropy + Age + Sex + MeanFD + (1|Subject)`) in `src/stats/model_fitting.py`. **Note**: **SPEC FR-004 MANDATES MixedLM with Subject random effect. This overrides the contradictory OLS instruction in Plan.md Summary and Phase 3.** Use `statsmodels` MixedLM. **Note**: Plan.md flagged for correction (Plan-Root-Cause).
- [ ] T029 [US3] Implement adaptive Freedman-Lane permutation test in `src/stats/permutation_test.py`. **Logic**: Start with pilot N=500 iterations. Check p-value stability (convergence of max-t statistic). If unstable, increase iterations by 500 up to a hard cap of N=10,000. Output `data/results/max_t_distribution.npy` and `data/results/corrected_pvalues.csv`. **Note**: Ensures 'statistically significant' requirement is met dynamically by adapting to data complexity. **Depends on T028**.
- [ ] T030 [US3] Implement FWE correction logic to threshold p-values at < 0.05 using the distribution from `data/results/max_t_distribution.npy` (produced by T029) and generate `data/results/corrected_pvalues.csv` containing FWE-adjusted p-values. **Note**: Must strictly follow T029. **Depends on T029**.
- [ ] T031 [US3] Implement post-hoc power analysis (F-test) in `src/stats/power_analysis.py` to calculate power for effect size d=0.3. Save raw metrics to `data/results/power_metrics.json` and explicitly flag the study as 'Underpowered' in the JSON if Power < 0.80.
- [ ] T032 [US3] Generate parcel-wise NIfTI map of significant clusters in `data/results/significant_map.nii.gz`
- [ ] T033 [US3] **Sensitivity Analysis Driver**: Create a wrapper script in `src/stats/sensitivity_driver.py` that orchestrates the full pipeline. **Grid**: Sweep **scale parameter τ ∈ {1, 2, 3, 4, 5}** (discrete magnitudes matching m=1–5) and **tolerance r ∈ {0.1, 0.15, 0.2}**. **Constraint**: Keep **embedding dimension m=2** fixed. **Logic**: For each grid point (τ, r), re-compute entropy from raw time series (T020 function) and run statistical model (T028-T030). **Output**: Aggregate results into `data/results/sensitivity_grid.csv` with columns: [scale_tau, tolerance_r, num_significant_parcels, max_beta, mean_p_value]. **Note**: Uses N=1000 pilot permutations per grid point. **Depends on T020, T023** (raw data and entropy matrix), NOT T023 alone. **Note**: Removed [P] tag; strictly sequential after US2.
- [ ] T034 [US3] **Primary Analysis Execution**: Execute the full statistical pipeline (T028-T032) on the `data/cleaned/low_motion_subset.parquet` dataset to generate the **primary** results. **Output**: Generate `reports/analysis_report.pdf` using filtered data. **Note**: Uses low-motion subset to satisfy FR-002. **Note**: Spec FR-004 (MixedLM) overrides Plan.md (OLS). **This is the main scientific deliverable.**
- [ ] T035 [US3] **Comparative Robustness Check**: Execute a *separate* statistical pipeline execution on the `data/cleaned/full_clean.parquet` dataset (all valid DSRT). **Logic**: Use a distinct function `fit_model_unfiltered()` to avoid ambiguity with T028's filtered context. **Constraint**: This is strictly a comparative sensitivity check. **MOTION FILTERING**: This task MUST **STILL APPLY** the mean FD < 0.2mm filter to the `full_clean` dataset to ensure consistency with FR-002; it compares "Low Motion Subset" vs "All Valid Subjects (with motion filter)" rather than "Filtered vs Unfiltered". Justified by Constitution Principle VI (Neuroimaging Motion Control) to compare low-motion vs full-clean results. **Note**: Does not re-run T012-T014; consumes existing artifacts from T014. **Note**: This task intentionally relaxes the "subset size" constraint but NOT the "motion filter" constraint.
- [ ] T036 [US3] Generate final PDF report in `reports/analysis_report.pdf` including associational framing, power analysis, sensitivity tables, and robustness check results. **Explicit Instruction**: Read `data/results/power_metrics.json`. If the 'underpowered' flag is present, **MUST INJECT** the string 'UNDERPOWERED' into the report text (e.g., in the Results or Discussion section) to satisfy SC-006. **Note**: Ensures the flag is visible in the final deliverable.
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

- All Setup tasks marked [P] can run in parallel (except T001 which is sequential)
- All Foundational tasks marked [P] can run in parallel (within Phase 2) (except T006/T009 which have sequential dependencies)
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

- [P] tasks = different files, no dependencies (except where explicitly noted for sequential steps like T001)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (A minimal virtual environment configured with a small number of CPU cores, a moderate amount of RAM, and limited disk space.). No GPU, no 8-bit quantization, no large model loading.
- **Data Integrity**: All analysis tasks must use real HCP data downloaded via T012. No synthetic data fabrication.
- **Sensitivity Analysis**: Task T033 is a driver that re-runs the pipeline with reduced permutations for grid points to fit within 6 hours. **Logic corrected to test scale parameter τ ∈ {1, 2, 3, 4, 5} and tolerance r ∈ {0.1, 0.15, 0.2}**.
- **Model Architecture**: Task T028 implements Mass-Univariate MixedLM per parcel to satisfy Spec FR-004. **Overrides Plan.md OLS instruction**. **Plan.md flagged for correction**.
- **Power Analysis**: Task T031 includes explicit logic to flag the study as underpowered if Power < 0.80. Task T036 ensures this flag is injected into the PDF.
- **Robustness**: T035 runs on `full_clean` (with motion filter applied) while T034 runs on `low_motion_subset` (filtered), enabling valid comparison and satisfying FR-002 for the primary analysis. **T035 is a comparative check, not a primary analysis**.
- **Plan Correction**: The `plan.md` summary and Phase 3 description incorrectly specify OLS. The implementation MUST follow Spec FR-004 (MixedLM). This task list reflects the Spec requirement.
- **Permutation Logic**: Task T029 uses an adaptive loop (pilot 500 -> expand to 10k) to ensure statistical significance, replacing hardcoded 5000.
- **Directory Verification**: T001 now produces `data/directories_verified.json` as an explicit, machine-readable artifact.
- **Seed Manager**: T009 is sequential and must run before stochastic tasks; [P] tag removed.
