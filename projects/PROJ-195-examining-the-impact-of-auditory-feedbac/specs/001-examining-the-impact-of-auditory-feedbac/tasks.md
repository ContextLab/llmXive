# Tasks: Examining the Impact of Auditory Feedback on Motor Sequence Learning

**Input**: Design documents from `/specs/001-examining-the-impact-of-auditory-feedback-motor-learning/`
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

- [X] T001 Create project structure per implementation plan: `mkdir -p projects/PROJ-195-examining-the-impact-of-auditory-feedbac/{code,data/raw,data/derivatives,data/processed,roi_masks,tests/unit,tests/integration,tests/contract}` and `data/{raw,derivatives,processed}`.
- [X] T002 Initialize Python project: Create `projects/PROJ-195-examining-the-impact-of-auditory-feedbac/requirements.txt` with pinned versions for: nilearn, pandas, numpy, scipy, matplotlib, seaborn, bids-validator, pytest. (Removed fmriprep as it is a Docker container)
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Spec Amendments)

**Purpose**: Core infrastructure, Spec Amendments, and validation that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All Spec Amendment tasks (T004a, T021a, T024a, T028a) are placed here to ensure the spec is corrected before implementation.

- [ ] T004 [P] Create `stats_config.yaml` defining GLM parameters, FDR threshold (q<0.05), and ROI definitions
- [ ] T005 [P] Create `roi_masks/auditory_cortex.nii.gz` using the Harvard-Oxford Cortical Structural Atlas. **Exact Command**: Use `nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr0-1mm')` and extract the 'Auditory Cortex' label mask. Ensure deterministic output by setting the random seed if any sampling is involved (though maxprob is deterministic). (Depends on T001)
- [X] T006 [P] Implement `code/utils.py` for BIDS path helpers, QC logging, and motion threshold checks (>2mm exclusion logic) (Prerequisite for T009)
- [X] T007 Setup Docker configuration for `fmriprep` by creating `docker-compose.yml`. **Exact Syntax**: Use a configured memory limit in the service definition., mount `./data/raw:/data:ro` and `./data/derivatives:/out`, and set entrypoint arguments for `fmriprep` including `--output-spaces MNI152NLin2009cAsym --fs-no-reconall`. (Depends on T001, T006; Hard prerequisite for T009)
- [ ] T008 [P] Specify Docker image tag: Create a script or configuration to Pull `nipreps/fmriprep` with a specific stable version tag for determinism. (Depends on T001; Prerequisite for T009)
- [ ] T009 [SPEC-AMEND] Update `spec.md` FR-001 to reference `ds000246` instead of `ds000115`. **Exact Text Replacement**: Replace "ds000115" with "ds000246" in FR-001, User Story 1, and Assumptions sections of `spec.md`. (Depends on T001, T002; **Must complete before T012**)
- [ ] T010 [SPEC-AMEND] Update `spec.md` FR-004 to change "paired-sample t-test" to "one-sample t-test against zero". **Exact Text Replacement**: Replace "paired-sample t-test" with "one-sample t-test against zero" in FR-004 of `spec.md`. (Depends on T001; **Must complete before T021**)
- [ ] T011 [SPEC-AMEND] Update `spec.md` FR-005 to allow "global learning rate slope" independent of condition. **Exact Text Replacement**: Replace "per condition" with "global (independent of condition)" in FR-005 of `spec.md`. (Depends on T001; **Must complete before T028**)
- [ ] T012 [SPEC-AMEND] Update `spec.md` SC-002 to allow "global t-statistic p < 0.10" for pilot adjustments. **Exact Text Replacement**: Replace "p < 0.05" with "p < 0.10" in SC-002 of `spec.md`. (Depends on T001; **Must complete before T024**)

**Checkpoint**: Foundation and Spec Amendments ready - user story implementation can now begin in parallel

---

## Phase 2.5: Test-First Implementation (US1)

**Purpose**: Write tests for User Story 1 BEFORE implementation to ensure test-driven development.

- [X] T013 [P] [US1] Unit test for download integrity and checksum validation in `tests/unit/test_download.py` (Must be written before T014/T015)
- [X] T014 [P] [US1] Integration test for fmriprep execution on a single subject in `tests/integration/test_preprocess.py` (Must be written before T016/T017)

**Checkpoint**: Tests written and failing - ready for implementation

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download `ds000246`, validate event labels (normal, delayed, pitch-shifted), and generate fmriprep derivatives.

**Independent Test**: Run pipeline on a single subject subset; verify BIDS derivatives exist, motion QC log is populated, and no subjects >2mm motion are included in the final list.

### Implementation for User Story 1

- [X] T015 [US1] Implement dataset filtering logic in `code/download.py` to ensure total size < 14GB. **Exact Strategy**: Select the initial subjects from the dataset and maintain their alphabetical ordering.

The research question, method, and references remain unchanged as no specific citations or experimental procedures were included in the original passage to preserve. (Depends on T009; Corrected dataset source ds000246; Explicitly depends on T009's core fetch logic)
- [X] T016 [US1] Implement event label validation in `code/utils.py` to halt with exit code 1 and log "ERROR: Missing required event labels" if 'normal', 'delayed', or 'pitch-shifted' are missing (Depends on T009, T006; Hard stop constraint)
- [X] T017 [US1] Implement motion QC extraction in `code/preprocess.py` to parse fmriprep logs and flag subjects >2mm displacement. (Depends on T009)
- [X] T018 [US1] Implement subject exclusion logic to generate `data/processed/valid_subjects.txt` for downstream steps
- [ ] T019 [US1] Add logging for ALL pipeline deviations (slice-time, motion, normalization, smoothing) to `data/processed/preprocessing.log` in JSON format for every subject with motion >2mm or fmriprep failure, adhering to Constitution Principle VI. (Depends on T009)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Group Analysis (Priority: P2)

**Goal**: Fit First-Level GLMs, generate contrast maps (perturbed > normal), and perform Group-Level one-sample t-test with FDR.

**Independent Test**: Run GLM on a single subject's preprocessed data; verify contrast map generation. Run group test on synthetic contrast maps; verify FDR thresholding and output of effect sizes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for contrast definition logic (delayed + pitch-shifted) in `tests/unit/test_glm_first_level.py`
- [X] T021 [P] [US2] Unit test for FDR correction and one-sample t-test logic in `tests/unit/test_glm_group.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement First-Level GLM in `code/glm_first_level.py` using nilearn, defining 'perturbed' as union of 'delayed' and 'pitch-shifted'. (Depends on T018)
- [X] T023 [US2] Implement contrast map generation and saving for each valid subject to `data/processed/` (Depends on T022)
- [X] T024 [US2] Implement Group-Level analysis in `code/glm_group.py` performing a **one-sample t-test against zero**. (Depends on T023; Corrected from spec's paired-sample to scientifically valid method per plan; **Depends on T010**)
- [ ] T025 [US2] Apply Voxel-wise FDR correction (q < 0.05) and extract significant clusters. (Depends on T024)
- [X] T026 [US2] Calculate and save Cohen's d effect sizes and confidence intervals for identified clusters (Depends on T025)
- [X] T027 [US2] Handle edge case: if no clusters survive FDR, calculate global t-statistic p-value, save uncorrected map (thresholded at p < 0.001 uncorrected) to `data/processed/uncorrected_map.nii.gz`, and log "NULL RESULT: No clusters survived FDR". (Depends on T025; Includes global p-value logic for SC-002; **Depends on T012**)
- [X] T028 [US2] Extract mean beta values from `auditory_cortex.nii.gz` for each subject and save to `data/processed/roi_betas.csv`. (Depends on T005, T023; **Moved from Phase 5 to Phase 4 to resolve ordering dependency**)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. **US3 cannot start until T028 is complete.**

---

## Phase 5: User Story 3 - Brain-Behavior Correlation and Visualization (Priority: P3)

**Goal**: Extract behavioral learning rates, correlate with auditory cortex activation, and generate visualizations.

**Independent Test**: Provide synthetic CSVs of RTs and ROI betas; verify Pearson correlation calculation and scatter plot generation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for learning rate proxy calculation (linear regression slope) in `tests/unit/test_behavior.py`. **Specific Test**: `tests/unit/test_behavior.py::test_learning_rate_slope_independence` verifies that the slope is calculated over ALL trials and is independent of condition labels.
- [X] T030 [P] [US3] Unit test for correlation logic and plotting in `tests/unit/test_correlation.py`. **Specific Test**: `tests/unit/test_correlation.py::test_pearson_correlation_and_plot_generation` verifies Pearson's r calculation and that a PNG/PDF plot is generated.

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement behavioral metric extraction in `code/behavior.py` (trial-wise RTs or block-level slope if missing) (Depends on T018)
- [ ] T032 [US3] Implement global learning rate proxy calculation using Ordinary Least Squares (OLS) regression of mean RT (ms) against trial index to derive the slope. (Depends on T031; **Depends on T011**)
- [ ] T033 [US3] Calculate Pearson correlation between auditory cortex activation (from T028) and learning rate proxy. (Depends on T032, T028; **Must wait for T028 completion**)
- [X] T034 [US3] Implement visualization scripts in `code/viz.py` to generate thresholded statistical maps and scatter plots. (Depends on T033)
- [ ] T035 [US3] Generate final report summary table with cluster coordinates and behavioral correlations to `docs/report_summary.csv`. **Exact Schema**: Columns must be `cluster_id, x, y, z, t, p_val_fdr, r_corr, p_val_beh, description`. (Depends on T026, T033)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update `README.md` with project overview and setup instructions
- [ ] T036b [P] Update `docs/api.md` with function signatures and usage examples for `download.py`, `preprocess.py`, `glm_first_level.py`
- [ ] T036c [P] Update `quickstart.md` with end-to-end execution guide
- [ ] T037 Code cleanup and refactoring of utils
- [ ] T038 Performance optimization for sequential fmriprep execution
- [ ] T039 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end flow on a small subset

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes all Spec Amendments**.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
 - **US3 (Phase 5) specifically depends on T028 (US2) completion.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on valid subjects from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **MUST WAIT** for T028 (US2) completion for ROI extraction. T031/T032 can start earlier if data exists, but T033/T034/T035 require T028.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T009/T010/T011/T012 which must complete before their respective implementation tasks**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) **EXCEPT T033/T034/T035 which depend on T028 completion**.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for download integrity and checksum validation in tests/unit/test_download.py"
Task: "Integration test for fmriprep execution on a single subject in tests/integration/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset filtering logic in code/download.py (Keep sub-01 to sub-10)"
Task: "Implement event label validation in code/utils.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Test-First Implementation
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (excluding T009/T010/T011/T012 until validated)
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 (Must wait for US2 completion for T028/T033)
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
- **Critical Constraint**: All tasks must run on free-tier CPU (limited cores, constrained RAM). No GPU, no 8-bit models.
- **Data Source**: Ensure all tasks reference `ds000246` (corrected from spec's ds000115).
- **Statistical Method**: Ensure all tasks implement 'one-sample t-test' (corrected from spec's paired-sample).
- **Spec Amendments**: Tasks T009, T010, T011, T012 are explicitly designated to update spec.md to match the plan's corrections. These MUST be completed before their corresponding implementation tasks.
- **Ordering Fix**: T028 (ROI extraction) moved to Phase 4 to ensure US3 (Phase 5) does not start until ROI data is available.