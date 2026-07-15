# Tasks: The Impact of Simulated Social Exclusion on Neural Responses to Reward

**Input**: Design documents from `/specs/001-social-exclusion-reward-neural/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001a [P] Create `projects/PROJ-392-the-impact-of-simulated-social-exclusion/` root directory and `code/`, `data/`, `tests/` subdirectories. <!-- FAILED: unspecified -->
- [X] T001b [P] Create `data/raw-fmri`, `data/processed-fmri`, `data/behavioral`, `data/results` subdirectories.
- [X] T001c [P] Create `code/data_download`, `code/manipulation`, `code/preprocess`, `code/analysis`, `code/visualization`, `code/utils`, `code/pipeline` subdirectories.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (nibabel, numpy, pandas, scikit-learn, scipy, matplotlib, nilearn, nipype, pybids, pyyaml, statsmodels). **Note**: Do NOT include `fmriprep` in this list; create a `docker-compose.yml` or wrapper script in T012 to invoke the Docker image.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup directory structure: `data/raw-fmri`, `data/processed-fmri`, `data/behavioral`, `data/results`, `code/manipulation`, `code/utils`
- [X] T005 Implement `code/utils/checksums.py` for data integrity verification
- [X] T006 Implement `code/utils/provenance.py` for machine-readable YAML sidecar generation
- [X] T007 Create base configuration loader for dataset IDs (ds000246, ds004738) and ROI coordinates (AAL, Harvard-Oxford)
- [X] T008 Setup `code/pipeline/run_pipeline.py` orchestration skeleton with error handling and logging
- [X] T009 Implement `code/utils/framing_validator.py` to scan reports for causal verbs (satisfying FR-009)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download publicly available fMRI datasets containing social exclusion and reward tasks, and preprocess them using CPU-tractable methods. **Critical**: Since no single dataset contains both tasks, this phase implements a 'Merged Dataset Strategy' to harmonize separate datasets.

**Independent Test**: Can be fully tested by downloading the individual datasets (ds000246, ds004738), running the harmonization logic, preprocessing on CPU, and verifying output BOLD images and first-level GLM estimates are generated without GPU resources.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `code/data_download/download_openneuro.py` to fetch ds000246 (Exclusion) and ds004738 (Reward) separately with BIDS validation. **Do not** attempt to merge here.
- [ ] T010b [US1] Implement `code/data_download/harmonize_datasets.py` to execute the 'Merged Dataset Strategy': map participant IDs across datasets, align condition labels, and apply confound controls (e.g., adding 'Dataset ID' as a covariate tag) to prepare for analysis. (Addresses FR-001 and Plan's Critical Design Pivot).
- [ ] T011 [P] [US1] Implement `code/manipulation/generate_condition_labels.py` to extract exclusion/inclusion labels from `participants.tsv` or task JSON for each dataset.
- [X] T012 [US1] Implement `code/preprocess/cpu_fmriprep_wrapper.py` invoking fMRIPrep (docker: `nipreps/fmriprep:latest`) with a configurable thread count suitable for CPU-only execution. **Note**: This task creates the wrapper script; `fmriprep` is not installed via pip.
- [X] T013 [US1] Implement `code/preprocess/run_preprocessing.py` to handle chunked processing (batches of subjects) and generate preprocessed NIfTI images (slice-timing corrected, realigned, normalized to MNI, smoothed with an appropriate spatial kernel) with failure logging.
- [~] T014 [US1] Implement logic to harmonize and label data from merged exclusion and reward datasets: create a unified metadata file linking participants to their exclusion/inclusion group and task run type (BLOCKING DEPENDENCY FOR T018).
- [~] T015 [US1] Implement provenance generation: create YAML sidecars for every preprocessed file recording pipeline version and parameters (satisfying Constitution Principle VI).
- [X] T016 [US1] Implement metrics collection: calculate 'Preprocessing Completion Rate', log to `data/results/preprocessing_metrics.json` (target ≥90%), and include logic to flag 'exploratory' status and recommend future studies if N < 20 per group (satisfying FR-010).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Data downloaded, harmonized, preprocessed, and labeled). **T014 must be complete before T018 can execute.**

---

## Phase 4: User Story 2 - ROI-Based Statistical Analysis (Priority: P1)

**Goal**: Extract beta estimates from predefined ROIs and perform second-level mixed-effects analysis comparing excluded vs. included groups.

**Independent Test**: Can be fully tested by running the ROI extraction and t-test on preprocessed data from ≥20 participants per group, producing statistically valid group-level effect estimates.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/analysis/roi_extraction.py` to load Ventral Striatum (AAL atlas) and OFC (Harvard-Oxford, thresholded at an appropriate level) masks in MNI space (DEPENDS ON T013/T014).
- [~] T018 [US2] Implement first-level GLM execution using Nilearn with autoregressive pre-whitening for temporal autocorrelation (DEPENDS ON T013/T014).
- [~] T019 [US2] Implement extraction of beta estimates for 'reward anticipation' and 'reward receipt' events per participant.
- [~] T020 [US2] Store extracted betas in structured format: `data/results/beta_estimates.csv` (columns: participant_id, group, roi, event_type, beta_value).
- [X] T021 [US2] Implement `code/analysis/group_analysis.py` to perform two-sample t-test between excluded vs. included groups (PRIMARY METHOD per FR-005).
- [~] T022 [US2] Implement Bonferroni correction logic for 4 hypothesis tests (2 ROIs × 2 events) at α=0.05.
- [X] T023a [US2] Implement the primary two-sample t-test logic in `code/analysis/group_analysis.py` to compare groups, satisfying FR-005 and SC-001.
- [~] T023b [US2] Implement a secondary MixedLM model (using `statsmodels`) including 'Dataset ID' as a random effect to assess robustness of the merged dataset approach (Plan's design pivot), distinct from the primary t-test.
- [~] T024 [US2] Generate summary statistics: mean activation, SD, t-statistic, Cohen's d, and Bonferroni-corrected p-values for each ROI/Event combination (from T023a).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Data processed and statistical results generated).

---

## Phase 5: User Story 3 - Result Visualization and Reporting (Priority: P2)

**Goal**: Generate interpretable visualizations and a summary report framing results as associational.

**Independent Test**: Can be fully tested by generating figures from completed analysis outputs and verifying they display group differences with appropriate statistical annotations.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/visualization/plot_results.py` to generate ROI bar plots with mean ± SEM error bars and p-value annotations (*p<0.05, **p<0.01) (DEPENDS ON T021/T024).
- [~] T026 [US3] Implement SPM overlay generation: overlay significant clusters on MNI template brain with coordinates (x,y,z) and peak t-values (DEPENDS ON T021/T024).
- [ ] T027 [US3] Implement report compilation: generate `data/results/summary_report.md` including sample size, ROI means, t-stats, effect sizes, and corrected p-values.
- [X] T028 [US3] Integrate `code/utils/framing_validator.py` to scan the summary report for causal verbs (lexicon: 'causes', 'leads to', 'results in', 'induces', 'forces') and enforce associational language (e.g., "association between" vs "causes").
- [~] T029 [US3] Implement power limitation check: if N < 20 per group, flag as exploratory and append recommendation for future studies (≥30 participants) to the report.

**Checkpoint**: All user stories should now be independently functional (Analysis complete, visualized, and reported).

---

## Phase 6: User Story 4 - Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis sweeping key decision thresholds to demonstrate robustness.

**Independent Test**: Can be fully tested by re-running analysis with alternative thresholds (smoothing ∈ {4mm, 6mm, 8mm}) and comparing resulting mean beta estimates.

### Implementation for User Story 4

- [ ] T030 [P] [US4] Implement `code/analysis/sensitivity_analysis.py` to iterate over smoothing kernels across a range of FWHM values.
- [ ] T030b [P] [US4] Implement logic to iterate over ROI mask probability thresholds [low, high] and generate corresponding masks for sensitivity analysis. (Satisfies FR-008 with concrete values).
- [ ] T031 [US4] Re-run ROI extraction and group analysis via a parameterized analysis wrapper function for each smoothing kernel and mask probability combination (DEPENDS ON Phase 4 completion).
- [ ] T032 [US4] Generate a consistency table in `data/results/sensitivity_analysis.csv` showing beta values and t-statistics across threshold combinations.
- [ ] T033 [US4] Calculate consistency rate: verify if primary finding (reduced VS activation) holds in ≥4 of 6 threshold combinations (3 kernels × 2 masks) (≥67% threshold).
- [ ] T034 [US4] Append sensitivity analysis results and consistency conclusion to `data/results/summary_report.md`.

**Checkpoint**: Sensitivity analysis complete and reported.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T036a [P] Refactor `code/analysis/group_analysis.py` to ensure cyclomatic complexity < 10 and improve modularity.
- [ ] T036b [P] Run static analysis (flake8/mypy) on all `code/` files and fix reported issues.
- [ ] T037 [P] Run `pytest` unit tests: `tests/unit/test_roi_extraction.py`, `tests/unit/test_group_analysis.py` in `tests/unit/`.
- [ ] T038 [P] Run integration test `tests/integration/test_pipeline.py` on a small subset of data to verify end-to-end flow.
- [ ] T039 Run quickstart.md validation to ensure reproducibility on a fresh runner.

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 output (preprocessed data)
- **User Story 3 (P2)**: Can start after US2 completion - Depends on US2 output (beta estimates/stats)
- **User Story 4 (P3)**: Can start after US2 completion - Depends on US2 logic for re-runs

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
 - Developer A: User Story 1 (Data/Preprocess)
 - Developer B: User Story 2 (Analysis)
 - Developer C: User Story 3 (Visualization/Reporting)
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
- **Critical**: All preprocessing tasks MUST respect a constrained CPU, RAM, and time budget (no GPU, no 8-bit models).
- **Critical**: No synthetic data is used for primary analysis; only real OpenNeuro datasets.
- **Critical**: T014 (harmonization) is a blocking dependency for T018 (GLM).
- **Critical**: T031 uses a parameterized wrapper, not static task re-execution.
- **Critical**: T033 validates against 6 combinations (3 kernels × 2 masks) with ≥4/6 threshold.
- **Critical**: T023a implements the Spec-mandated t-test; T023b implements the Plan's MixedLM as a robustness check.
- **Critical**: T030b uses concrete values [[deferred], [deferred]] for mask probability thresholds.