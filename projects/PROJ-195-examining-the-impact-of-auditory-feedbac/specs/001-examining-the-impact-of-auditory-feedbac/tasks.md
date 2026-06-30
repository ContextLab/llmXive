# Tasks: Examining the Impact of Auditory Feedback on Motor Sequence Learning

**Input**: Design documents from `/specs/001-examining-the-impact-of-auditory-feedback/`
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

- [ ] T001 [US1] Initialize project directory structure at `projects/PROJ-195-examining-the-impact-of-auditory-feedbac/`. Create subdirectories `code/`, `data/raw/`, `data/processed/`, `data/interim/`, `contracts/`, `tests/`, `code/utils/`, `code/outputs/`, and `logs/`. Ensure all directories exist unconditionally. (Replaces T001a-d)
- [ ] T002 [US1] Initialize Python 3.10 project with pinned dependencies in `code/requirements.txt` (nilearn>=0.10.0, nibabel, scikit-learn, pandas, matplotlib, pyyaml, openneuro-py, statsmodels). Verify installation via `pip install -r code/requirements.txt` in a clean virtualenv and ensure exit code 0. (Replaces T002)
- [ ] T003 [P] [US1] Configure linting and formatting tools (black, flake8) in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [US1] Setup data directory structure (`data/raw/`, `data/processed/`, `data/interim/`) and `.gitignore` (ensure large files ignored).
- [ ] T005 [P] [US2] Implement ROI mask loading utility in `code/utils/rois.py` (auditory cortex, SMA, cerebellum).
- [ ] T006 [P] [US2] Setup statistical utility functions in `code/utils/stats.py` (Cohen's d, CI calculation).
- [ ] T007 [US1] Create base schema definitions in `contracts/` (dataset.schema.yaml, output.schema.yaml).
- [ ] T008 [US1] Configure Docker environment variables for `fmriprep` execution. Create `.env` file in `code/` with variables: `FMRIPREP_VERSION=23.1.3`, `BIDS_DIR=/data/raw/ds000115`, `OUTPUT_DIR=/data/processed`. (Replaces T008)
- [ ] T009 [US1] Setup logging infrastructure to capture pipeline stages and errors.
- [ ] T009.5 [P] [US2] Serialize static statistical parameters into `data/processed/stats_config.yaml` BEFORE any GLM fitting. **Schema**: Validate against `contracts/stats_schema.yaml`. **Required Keys**: `threshold_voxel`, `fdr_method`, `roi_definitions`, `smoothing_mm`. **Note**: This config defines static parameters for the entire pipeline, not data-derived values. (Moved from Phase 4, Replaces T020.5)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download `ds000115`, verify conditions, select pilot subset (N≈10), and run `fmriprep` to generate preprocessed data.

**Independent Test**: The pipeline is tested by verifying that the `fmriprep` output directory contains valid NIfTI files for the "normal", "delayed", and "pitch-shifted" conditions for at least 10 subjects, and that the event files correctly label trial types.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data download integrity in `tests/test_download.py`.
- [ ] T011 [P] [US1] Integration test for fmriprep output validation in `tests/test_preprocess.py`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `download_data.py` to fetch `ds000115` via OpenNeuro API with checksum verification. **Output**: `data/raw/ds000115/`, checksums in `data/raw/ds000115/.checksums.txt`. **Note**: Select a limited number of valid subjects (N≈10) during download to respect CI limits per **Plan Summary: Pilot subset N≈10**. (FR-001, Plan Task 0.1, 0.6)
- [ ] T013 [P] [US1] Implement `verify_conditions.py` to check event files for "normal", "delayed", "pitch-shifted" labels; HALT if missing (Plan Task 0.5).
- [ ] T015 [US1] Create `run_fmriprep.sh` wrapper to execute `fmriprep:23.1.3` Docker container. **Args**: `--output-spaces MNI --smooth 6 --nthreads 2 --omp-nthreads 2`. **Constraint**: Process a small cohort of subjects (N≈). **Verification**: Verify logs for slice-time, motion correction, MNI normalization; halt on missing files. **Deviation Log**: If N < 30, log deviation to `logs/deviation.log` referencing Plan Summary. (FR-002, Plan Task 1.1)
- [ ] T016 [US1] Implement motion artifact exclusion logic: **Threshold**: mean frame-wise displacement > 0.5mm. **Output**: Log excluded subjects to `data/processed/excluded_subjects.csv`. **Verification**: Verify that excluded subjects are removed from the input list for T020. (Replaces T016)
- [ ] T017 [US1] Add logging for US1 operations and calculate retention rate for the N≈10 subset. **Metric**: Target: [deferred] of N selected subjects valid (Plan Success Criteria Mapping). (Replaces T017)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Voxel-wise GLM and Group Statistical Analysis (Priority: P2)

**Goal**: Fit subject-level GLMs, perform group-level t-test with FDR correction, and compute effect sizes.

**Independent Test**: The analysis is tested by generating a null dataset (shuffling condition labels) and verifying that the permutation test yields no significant clusters (or a false-positive rate ≤ 0.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for GLM contrast generation in `tests/test_glms.py`.
- [ ] T019 [P] [US2] Integration test for null-dataset permutation test in `tests/test_null_test.py`.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `preprocess_glms.py` to fit first-level GLM for each subject using `nilearn` with regressors for conditions and motion parameters. **Output**: `data/processed/subject_{id}_contrast.nii.gz`. **Config**: Read parameters from `data/processed/stats_config.yaml`. (FR-003)
- [ ] T021 [US2] Generate contrast maps ("perturbed > normal") for each subject and save to `data/processed/`.
- [ ] T022 [US2] Implement `group_analysis.py` to perform paired-sample t-test across subjects with **Voxel-wise FDR** correction (p < 0.05) and voxel-wise threshold (p < 0.005). **Output**: `data/processed/group_stats_fdr.nii.gz`, `data/processed/group_summary.csv`. **Deviation Log**: Log deviation from Spec FR-004 (cluster-wise) to `logs/deviation.log` referencing Plan Override. (FR-004, Plan Phase 3.1)
- [ ] T023 [US2] Implement `null_test.py` to shuffle condition labels, rerun group analysis, and estimate false-positive rate (Plan Task 3.5).
- [ ] T024 [US2] Implement extraction of peak coordinates and mapping to anatomical regions (auditory cortex, STG, cerebellum) using MNI atlas.
- [ ] T025 [US2] Implement calculation of Cohen's d and confidence intervals for significant clusters (FR-007, SC-004).
- [ ] T026 [US2] Add logic to flag power limitation warning if N < 10. **Output**: Append warning to `code/outputs/power_report.md`. **Trigger**: N < 10. (Replaces T026)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Brain-Behavior Correlation and Visualization (Priority: P3)

**Goal**: Correlate ROI activation with behavioral metrics and generate publication-quality visualizations.

**Independent Test**: The feature is tested by generating a scatter plot and verifying that the system correctly computes and reports the Pearson correlation coefficient (r) and p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for correlation calculation in `tests/test_stats.py`.
- [ ] T028 [P] [US3] Integration test for visualization generation in `tests/test_visualization.py`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `extract_behavior.py` to extract mean reaction times and accuracy per subject/condition from event files. **Input**: `data/raw/ds000115`. **Output**: `data/interim/behavioral_metrics.csv`. **Dependency**: Requires T012 (download) to be complete. (FR-005)
- [ ] T030 [US3] Implement Pearson correlation calculation between ROI contrast values and behavioral metrics (FR-005, SC-003).
- [ ] T031 [US3] Generate scatter plots with regression lines and confidence intervals. **Output**: `code/outputs/brain_behavior_scatter.pdf` (800x600, annotated with r-value and p-value). (FR-006)
- [ ] T032 [US3] Generate thresholded 3D statistical maps (NIfTI) showing FDR-corrected clusters (FR-006).
- [ ] T034a [US3] Implement "Observed Power Limitation Report" generation in `code/outputs/power_report.md`. **Content**: A priori power estimation, observed power, limitations. **Note**: Implements Plan Phase 4.3 (Observed Power Report) superseding Spec FR-008 'post-hoc power analysis' per Plan Notes on Spec Conflicts. (FR-008, Plan Phase 4.3)
- [ ] T034b [US3] Implement 'post-hoc power analysis' calculation using observed effect sizes (from T025) and alpha=0.05 via `statsmodels.stats.power`. **Output**: Append results to `code/outputs/power_report.md` with header 'Statistically Criticized / Not Recommended (Spec FR-008 Requirement)'. **Note**: Explicitly performs Spec FR-008 requirement while noting statistical criticism per Plan. (FR-008, Spec Requirement)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] [US1] Update `README.md` with pipeline overview and setup instructions.
- [ ] T035b [P] [US1] Update `docs/api.md` with function signatures and usage examples.
- [ ] T036 [P] Code cleanup and refactoring.
- [ ] T037 [P] Profile pipeline execution time and implement caching/parallelization strategies to meet the 6-hour limit. **Verification**: Run full pipeline on CI and record duration < 6h. (Replaces T037)
- [ ] T038 [P] [US1] Additional unit tests for edge cases in `tests/unit/`.
- [ ] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (contrast maps)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (ROI values) and US1 (behavioral data)

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
Task: "Contract test for data download integrity in tests/test_download.py"
Task: "Integration test for fmriprep output validation in tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement download_data.py to fetch ds000115..."
Task: "Implement verify_conditions.py to check event files..."
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
- **Critical Constraint**: All tasks must run on GitHub Actions free-tier (limited CPU, ~7GB RAM, no GPU) within 6 hours. No 8-bit models or large LLMs.
- **Data Constraint**: Use only `ds000115` from OpenNeuro. If conditions are missing, the pipeline must halt gracefully.
- **Spec/Plan Conflict**: The Plan overrides Spec FR-004 (cluster-wise FDR) with Voxel-wise FDR for N=10. The Plan overrides Spec FR-008 (post-hoc power) with Observed Power Report. Tasks reflect Plan but explicitly log deviations.