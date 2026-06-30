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

- [X] T001a Create project structure per implementation plan: `mkdir -p projects/PROJ-195-examining-the-impact-of-auditory-feedbac/{code,data/raw,data/derivatives,data/processed,roi_masks,tests/unit,tests/integration,tests/contract}` (Split from T001 for parallel execution)
- [X] T001b Create data directory structure: `mkdir -p projects/PROJ-195-examining-the-impact-of-auditory-feedbac/data/{raw,derivatives,processed}` (Split from T001 for parallel execution)
- [X] T002 Initialize Python 3.11 project: Create `projects/PROJ-195-examining-the-impact-of-auditory-feedbac/requirements.txt` with pinned versions for: nilearn, pandas, numpy, scipy, matplotlib, seaborn, bids-validator, pytest. (Removed fmriprep as it is a Docker container)
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/download.py` to fetch OpenNeuro `ds000246` subset (handling disk limits) and verify SHA256 checksums. (Corrected dataset source; removed [P] to enforce sequential execution for T012/T013)
- [X] T005 [P] Create `stats_config.yaml` defining GLM parameters, FDR threshold (q<0.05), and ROI definitions
- [X] T006 [P] Create `roi_masks/auditory_cortex.nii.gz` using the Harvard-Oxford Cortical Structural Atlas in standard MNI template space (specific source for determinism).
- [X] T007 Implement `code/utils.py` for BIDS path helpers, QC logging, and motion threshold checks (>2mm exclusion logic) (Prerequisite for T009)
- [ ] T008 Setup Docker configuration for `fmriprep` with appropriate memory and process limits to ensure efficient resource utilization. (Prerequisite for T009)
- [ ] T008b [P] Specify Docker image tag: Create `docker-compose.yml` or script to pull `nipreps/fmriprep` with a version tag corresponding to a stable release. (Specific tag for determinism) (Prerequisite for T009)
- [ ] T009 Implement `code/preprocess.py` orchestration script to run fmriprep sequentially per subject and handle OOM/failure gracefully (Depends on T007, T008, T008b)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Test-First Implementation (US1)

**Purpose**: Write tests for User Story 1 BEFORE implementation to ensure test-driven development.

- [ ] T010 [P] [US1] Unit test for download integrity and checksum validation in `tests/unit/test_download.py` (Must be written before T012/T013)
- [ ] T011 [P] [US1] Integration test for fmriprep execution on a single subject in `tests/integration/test_preprocess.py` (Must be written before T014/T015)

**Checkpoint**: Tests written and failing - ready for implementation

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download `ds000246`, validate event labels (normal, delayed, pitch-shifted), and generate fmriprep derivatives.

**Independent Test**: Run pipeline on a single subject subset; verify BIDS derivatives exist, motion QC log is populated, and no subjects >2mm motion are included in the final list.

### Implementation for User Story 1

- [ ] T012 [US1] Implement dataset filtering logic in `code/download.py` to ensure total size < 14GB (subset if necessary) (Depends on T004; Corrected dataset source ds000246)
- [ ] T013 [US1] Implement event label validation in `code/utils.py` to halt with exit code 1 and log "ERROR: Missing required event labels" if 'normal', 'delayed', or 'pitch-shifted' are missing (Depends on T004, T007; Hard stop constraint)
- [ ] T014 [US1] Implement motion QC extraction in `code/preprocess.py` to parse fmriprep logs and flag subjects >2mm displacement
- [ ] T015 [US1] Implement subject exclusion logic to generate `data/processed/valid_subjects.txt` for downstream steps
- [ ] T016 [US1] Add logging for preprocessing deviations to `preprocessing.log` (Constitution Principle VI)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Group Analysis (Priority: P2)

**Goal**: Fit First-Level GLMs, generate contrast maps (perturbed > normal), and perform Group-Level one-sample t-test with FDR.

**Independent Test**: Run GLM on a single subject's preprocessed data; verify contrast map generation. Run group test on synthetic contrast maps; verify FDR thresholding and output of effect sizes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for contrast definition logic (delayed + pitch-shifted) in `tests/unit/test_glm_first_level.py`
- [ ] T018 [P] [US2] Unit test for FDR correction and one-sample t-test logic in `tests/unit/test_glm_group.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement First-Level GLM in `code/glm_first_level.py` using nilearn, defining 'perturbed' as union of 'delayed' and 'pitch-shifted' (Removed [P] to enforce sequential execution for T020)
- [ ] T020 [US2] Implement contrast map generation and saving for each valid subject to `data/processed/` (Depends on T019)
- [ ] T021 [US2] Implement Group-Level analysis in `code/glm_group.py` performing a **one-sample t-test against zero** (Corrected from spec's paired-sample to scientifically valid method per plan)
- [ ] T022 [US2] Apply Voxel-wise FDR correction (q < 0.05) and extract significant clusters (Depends on T021)
- [ ] T023 [US2] Calculate and save Cohen's d effect sizes and confidence intervals for identified clusters
- [ ] T024 [US2] Handle edge case: if no clusters survive FDR, calculate global t-statistic p-value, save uncorrected map (thresholded at p < 0.001 uncorrected) to `data/processed/uncorrected_map.nii.gz`, and log "NULL RESULT: No clusters survived FDR" (Depends on T022; Includes global p-value logic for SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Brain-Behavior Correlation and Visualization (Priority: P3)

**Goal**: Extract behavioral learning rates, correlate with auditory cortex activation, and generate visualizations.

**Independent Test**: Provide synthetic CSVs of RTs and ROI betas; verify Pearson correlation calculation and scatter plot generation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for learning rate proxy calculation (linear regression slope) in `tests/unit/test_behavior.py`
- [ ] T026 [P] [US3] Unit test for correlation logic and plotting in `tests/unit/test_correlation.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement behavioral metric extraction in `code/behavior.py` (trial-wise RTs or block-level slope if missing) (Depends on T015)
- [ ] T028 [US3] Implement global learning rate proxy calculation (slope of RT over ALL trials) ensuring independence from condition labels
- [ ] T029 [US3] Implement ROI extraction in `code/correlation.py` to get mean beta from `auditory_cortex.nii.gz` for each subject (Depends on T006, T020; Removed [P] to enforce sequential execution for T030)
- [ ] T030 [US3] Calculate Pearson correlation between auditory cortex activation and learning rate proxy; save results to `data/processed/correlation_results.csv` (Depends on T028, T029; Removed [P] to enforce sequential execution for T032)
- [ ] T031 [US3] Implement visualization scripts in `code/viz.py` to generate thresholded statistical maps and scatter plots
- [ ] T032 [US3] Generate final report summary table with cluster coordinates and behavioral correlations to `docs/report_summary.csv` (Depends on T023, T030)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Update `README.md` with project overview and setup instructions
- [ ] T033b [P] Update `docs/api.md` with function signatures and usage examples for `download.py`, `preprocess.py`, `glm_first_level.py`
- [ ] T033c [P] Update `quickstart.md` with end-to-end execution guide
- [ ] T034 Code cleanup and refactoring of utils
- [ ] T035 Performance optimization for sequential fmriprep execution
- [ ] T036 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end flow on a small subset

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on valid subjects from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on contrast maps from US2 and behavioral data from US1/US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T009 which depends on T007/T008/T008b**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) **EXCEPT T029/T030 which depend on US2 completion**
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
Task: "Implement dataset filtering logic in code/download.py"
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

1. Team completes Setup + Foundational together (excluding T009 until T007/T008/T008b done)
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 (Must wait for US2 completion for T029/T030)
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