# Tasks: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Input**: Design documents from `/specs/001-narrative-archaeology/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on previous task output)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

## Phase 1: Setup & Infrastructure

**Purpose**: Project initialization and environment configuration

- [ ] T001-SETUP [P] **CRITICAL**: Initialize project directory structure (`code/`, `tests/`, `data/`, `results/`) and generate configuration files. **Output**: `projects/PROJ-588-narrative-archaeology-reverse-engineerin/` directory tree, `requirements.txt`, `pyproject.toml` (with black/flake8 config), and `.flake8` files.
- [ ] T002-CONFIG [P] Implement `code/config.py` with pinned random seeds, CPU-only constraints, motion thresholds, and path definitions. **Output**: `code/config.py`.
- [ ] T003-PERM [P] Create `code/utils/stats.py` function `run_permutation_test` for permutation testing (a fixed number of iterations, pinned seed). **Output**: `code/utils/stats.py`.
- [ ] T003-FDR [P] Create `code/utils/stats.py` function `apply_fdr_correction` for FDR correction (q < 0.05). **Output**: `code/utils/stats.py`.
- [ ] T003-FISHER [P] Create `code/utils/stats.py` function `fisher_z_aggregate` for Fisher's Z aggregation logic. **Output**: `code/utils/stats.py`.
- [ ] T004-UTILS-VIZ [P] Create `code/utils/viz.py` for plotting RSA matrices and decoding accuracy with specific schema outputs. **Output**: `code/utils/viz.py`.
- [ ] T005-UTILS-LOGGING [P] Implement `code/utils/logging.py` for error handling: detect motion artifacts, skip subjects, and write JSON entries to `data/errors.log` with fields: `{timestamp, subject_id, error_code, motion_mm}`. **Output**: `code/utils/logging.py`.
- [ ] T005b-TEST-LOGGING [P] [US1] Unit test for error log schema in `tests/unit/test_logging.py::test_error_log_schema`. **Dependency**: Requires T005. **Output**: `tests/unit/test_logging.py`.
- [ ] T006-UTILS-HYGIENE [P] Implement `code/utils/hygiene.py` for PII scanning and checksum verification. **Output**: `code/utils/hygiene.py`.
- [ ] T008a-SEMANTIC-IMPL [P] [US2/US3] Implement `code/models/semantic.py` to extract semantic features using pre-trained **BERT-base-uncased** (CPU-only, inference only). **Constraint**: Must use **streaming** for text processing. **Output**: `code/models/semantic.py` (Function definition).

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, preprocess, and segment the Natural Stories fMRI dataset into event-aligned timecourses.

**Independent Test**: Verify that a small subject subset produces preprocessed NIfTI files, a valid event CSV with timestamps, and correctly aligned ROI masks within the CI limit.

### Implementation for User Story 1

- [ ] T014-RUN [S] [US1] Orchestrate download of a **-subject subset** (first few alphabetically) of ds000234 using `code/data/download.py` (T007) with checksum validation. **Output**: `data/raw/ds000234/`.
- [ ] T017-VERIFY-HYGIENE [S] [US1] Implement data hygiene: Verify checksums in `data/raw/`, ensure no in-place modifications, and enforce PII scanning. **Output**: `data/hygiene.log`. **Hard Stop**: Pipeline halts if PII scan fails. **Dependency**: Requires T006-UTILS-HYGIENE (Implementation) and T014 (Download).
- [ ] T009-IMPL-FMRIPREP [S] [US1] Implement `code/data/preprocess_wrapper.py` wrapper function `fMRIPrepWrapper` for fMRIPrep (**version 23.x**). **Flags**: `--output-spaces MNI`, `--fs-no-reconall`, `--omp-num-threads 2`, `--nthreads 2`. **Constraint**: Must use **Harvard-Oxford atlas** for ROI masks as per **Spec US-1**. **Output**: `code/data/preprocess_wrapper.py` (Class definition).
- [ ] T010-IMPL-MOTION [S] [US1] Implement `code/data/preprocess_motion.py` function `motion_detector()` for motion artifact detection (threshold >3mm). Skip subjects exceeding threshold, log to `data/errors.log` (JSON), proceeding with the remaining subjects. **Output**: `code/data/preprocess_motion.py` (Function definition).
- [ ] T011-IMPL-EXEC [S] [US1] Implement `code/data/preprocess_execution.py` function `run_subjects_sequentially()` to process a subset of subjects on the free-tier runner. **Output**: `code/data/preprocess_execution.py` (Wrapper function). **Constraint**: Must complete within 6 hours. **Implementation Detail**: Must include explicit **timeout enforcement** (subprocess timeout or wall-clock check) and a **fail-fast** strategy to halt execution immediately if the 6-hour limit is exceeded, logging the timeout event. **Dependency**: Requires T014 (Download), T009 (Wrapper impl), and T010 (Motion detector impl).
- [ ] T011b-RUNTIME-MONITOR [S] [US1] Implement `code/utils/runtime_monitor.py` to measure, log, and verify the actual runtime of the preprocessing pipeline against the 6-hour constraint (SC-005). **Output**: `results/runtime_report.json` with fields: `{total_runtime_seconds, status: "pass"|"fail", threshold_seconds: a predefined duration representing a significant time interval}`. **Dependency**: Requires T011.
- [ ] T011b-TEST [S] [US1] Unit test for runtime monitor in `tests/unit/test_runtime_monitor.py::test_runtime_threshold`. **Dependency**: Requires T011b-RUNTIME-MONITOR.
- [ ] T004b-LABEL-DERIVE [S] [US1] Derive 'plot', 'character', 'theme' labels from the official story script using a deterministic rule-based parser (keyword matching) to ensure ground truth independence from BERT features. **Dependency**: Requires T014 (Download). **Output**: `data/processed/annotations_raw.csv`.
- [ ] T004c-LABEL-VERIFY [S] [US1] Validate the rule-based parser output against the official story annotation files provided in the dataset. **Logic**: Compare derived labels with official onset/duration; flag deviations > 1s. **Output**: `data/processed/label_validation_report.json`. **Dependency**: Requires T004b-LABEL-DERIVE.
- [ ] T012-SEGMENT [S] [US1] Implement `code/data/segment.py` to align story events (plot, character, theme) with BOLD signal using HRF convolution (double-gamma). **Output**: `data/processed/events_aligned.csv` with `≤ 5%` missing timepoints. **Dependency**: Requires T011 (Preprocess execution), T004b-LABEL-DERIVE, and T004c-LABEL-VERIFY.
- [ ] T016-VERIFY-SEGMENT [S] [US1] Verify event segmentation output: Assert `missing_timepoints_ratio <= 0.05` in `tests/integration/test_segmentation.py::test_missing_timepoints_ratio`. **Dependency**: Requires T012.
- [ ] T013-ROI-MASKER [S] [US1] Create `code/data/roi_masker.py` to extract timecourses for hippocampus, mPFC, PCC, and lateral temporal cortex. **Logic**: Include "Delayed Task Availability Check" (FR-008) internally: if delayed task data is missing, switch to Early vs. Late encoding logic. Extract timecourses for **both Early and Late event phases separately** (or Delayed if available). **Output**: `data/processed/roi_timecourses.h5`. **Constraint**: Must use **Harvard-Oxford atlas** for ROI masks. **Dependency**: Requires T012 (Segmentation).

**Checkpoint**: User Story 1 is fully functional; clean, event-aligned dataset is ready for analysis.

---

## Phase 2: Foundational (Blocking Prerequisites for Analysis)

**Purpose**: Core infrastructure that MUST be complete before ANY analysis (US2/US3) can run. **Note**: This phase is now structurally empty of data-dependent tasks. All data-dependent foundational tasks (T008) have been moved to Phase 3 to resolve circular dependencies. This phase serves as a placeholder for future non-data dependencies if any arise.

**⚠️ CRITICAL**: Phase 2 contains no active tasks. T008 (Semantic Features) has been moved to Phase 3 to ensure it runs after T012 (Segmentation).

---

## Phase 3 (Continued): Semantic Feature Extraction (Blocking Prerequisite for US2/US3)

**Purpose**: Extract semantic features required for US2 and US3. This task is placed here to ensure it runs after T012 (Segmentation) which produces the event text.

- [ ] T008b-SEMANTIC-RUN [S] [US2/US3] Execute semantic feature extraction on the small text corpus from the 5-subject subset events. **Constraint**: Limit to the **small text corpus** to fit within 6-hour CI limit. **Dependency**: Requires T012 (Segmentation) for event text. **Output**: `data/features/bert_embeddings.npy`. **Usage**: Features used for RSA (T021) or as covariates.

---

## Phase 4: User Story 2 - Early vs. Late Event Pattern Comparison (Priority: P2)

**Goal**: Compare neural patterns between Early and Late events (Adapted from Encoding vs. Recognition) using RSA to identify reconfiguration in hippocampus and mPFC.

**Independent Test**: Compute RSA matrices and verify that Early-Late dissimilarity is significantly higher than Early-Early (p < 0.05).

### Implementation for User Story 2

- [ ] T021-RSA-COMPUTE [S] [US2] Implement `code/models/rsa.py` to compute dissimilarity matrices for **Early Event vs. Late Event** phases. **Rationale**: Implements **Semantic Drift** fallback (Early vs. Late) as per FR-008 due to missing delayed task data. **Formula**: `RDM[i,j] = 1 - corr(timecourse_i, timecourse_j)`. **Output**: `results/rsa_matrices.json` (schema: `{roi: {early_late: float, early_early: float}}`). **Dependency**: Requires T013 (ROI timecourses) and T008b (Semantic features for covariates). **Verification**: Assert results/rsa_matrices.json contains keys "early_late" and "early_early" with float values.
- [ ] T021-TEST [P] [US2] Unit test for RSA dissimilarity matrix calculation and output schema verification in `tests/unit/test_rsa.py::test_rsa_schema`. **Dependency**: Requires T021-RSA-COMPUTE.
- [X] T022 [P] [US2] Implement permutation testing logic in `code/utils/stats.py` with **Fixed a sufficient number of iterations to ensure convergence.** (per FR-004 and SC-001) and FDR correction (q < 0.05). **Seed**: Must pin random seed for the permutation loop to ensure determinism. **Output**: `results/permutation_pvalues.json`. **Dependency**: Requires T021-RSA-COMPUTE (Implementation) and T021-RSA-COMPUTE (Output File).
- [X] T023 [P] [US2] Implement Fisher's Z aggregation across subjects: `Z = 0.5 * ln((1+r)/(1-r))`. **Output**: `results/group_rsa_stats.json`. **Dependency**: Requires T021-RSA-COMPUTE (Implementation) and T021-RSA-COMPUTE (Output File).
- [ ] T024-VIZ [P] [US2] Visualize top differing ROIs (mPFC, hippocampus) in `code/utils/viz.py`. **Output**: `results/rsa_heatmaps.png`. **Dependency**: Requires T021-RSA-COMPUTE (Implementation).
- [ ] T024-TEST [P] [US2] Unit test for RSA heatmap generation in `tests/unit/test_viz.py::test_rsa_heatmap_exists`. **Dependency**: Requires T024-VIZ.
- [ ] T025-IMPLEMENT [S] [US2] Implement "Early vs. Late Event Stability" RSA analysis. **Metric**: `Stability = 1 - (Dissimilarity_Late - Dissimilarity_Early)`. **Output**: `results/stability_metrics.json` (schema: `{stability_score: float, early_dissimilarity: float, late_dissimilarity: float}`). **Dependency**: Requires T021-RSA-COMPUTE.
- [ ] T025-DOC-GENERAL [P] [US2] Update `docs/methodology.md` to reflect the "Early vs. Late" adaptation as the primary analysis strategy and document the "Stability" metric formula: `Stability = 1 - (Dissimilarity_Late - Dissimilarity_Early)`. **Verification**: Verify the section exists via a grep check or specific string assertion in `tests/docs/test_methodology.py`. **Dependency**: Requires T025-IMPLEMENT.

### Tests for User Story 2

- [X] T019 [P] [US2] Unit test for RSA dissimilarity matrix calculation in `tests/unit/test_rsa.py`.
- [X] T020 [P] [US2] Integration test for permutation test convergence and FDR correction in `tests/integration/test_stats.py`.

**Checkpoint**: Pattern reconfiguration analysis is complete; statistical significance established.

---

## Phase 5: User Story 3 - Narrative Element Reconstruction (Priority: P3)

**Goal**: Train linear classifiers to predict narrative elements (plot points, characters, themes) from encoding patterns and evaluate accuracy against chance.

**Independent Test**: Verify that decoder accuracy exceeds chance (/N) for at least one category and significantly outperforms a null shuffled-label model (p < 0.01).

### Implementation for User Story 3

- [ ] T030-PRIMARY [S] [US3] Implement `code/models/decoder.py` with Ridge Regression. **Logic**:
 1. **Aggregation**: If a category has <5 samples, aggregate into "Miscellaneous".
 2. **Validation (FR-011)**: Implement validation against a **held-out text set** (not the training set) to prevent circularity using a **Pearson correlation test** (null hypothesis r=0). **Action**: If validation fails (p < 0.01), **Log a warning** with `validation_p_value` and `validation_accuracy` to `results/validation_log.json`, but **PROCEED** with the pipeline. The pipeline **must NOT halt** on validation failure to ensure SC-003's validity and avoid unauthorized brittle failure modes.
 3. **Metric**: Calculate chance baseline as the reciprocal of the number of unique labels after aggregation.
 4. **Output**: `results/decoder_metrics.json` with schema: `{'actual_N': int, 'adjusted_chance': float, 'original_N': int, 'accuracy': float, 'deviation_log': str, 'validation_p_value': float, 'validation_accuracy': float}`.
- [ ] T031-CV-IMPL [S] [US3] Implement K-fold cross-validation (K=5) and accuracy reporting against chance baseline. **Output**: `results/cv_fold_accuracies.csv` (schema: `subject_id, fold, accuracy`). **Dependency**: Requires T030-PRIMARY.
- [ ] T031-TEST [P] [US3] Unit test for K=5 CV implementation and output schema in `tests/unit/test_decoder.py::test_cv_schema`. **Dependency**: Requires T031-CV-IMPL.
- [ ] T032-FDR-IMPL [S] [US3] Implement FDR correction across narrative categories and ROIs. **Logic**: Apply Benjamini-Hochberg procedure to p-values from T030/T031. **Output**: `results/fdr_corrected_pvalues.json` (schema: `{category_roi: {p_raw: float, p_fdr: float}}`). **Dependency**: Requires T030-PRIMARY and T031-CV-IMPL.
- [ ] T032-TEST [P] [US3] Unit test for FDR correction logic and output schema in `tests/unit/test_stats.py::test_fdr_schema`. **Dependency**: Requires T032-FDR-IMPL.
- [ ] T033-LIM [P] [US3] **Document Limitation**: Explicitly record the absence of "told vs. experienced" control condition; describe "label shuffling" as the simulation method. **Output**: `docs/limitations.md`.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for semantic feature extraction (BERT CPU inference) in `tests/unit/test_semantic.py`.
- [X] T027 [P] [US3] Unit test for Ridge Regression/SVM training and K-fold cross-validation in `tests/unit/test_decoder.py`.
- [X] T028 [P] [US3] Integration test for null model comparison (shuffled labels) and FR-011 validation logging in `tests/integration/test_decoder.py`.

**Checkpoint**: Narrative element reconstruction is complete; accuracy and statistical validity confirmed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Data Ingestion (Phase 3)**: Can start immediately after Setup (T014).
- **Semantic Features (Phase 3 Continued)**: **Cannot start until T012 (Segmentation)** in Phase 3 completes.
- **User Stories (Phase 4/5)**:
 - **US2/US3**: Can start **after T008b (Semantic Features) and T013 (ROI Timecourses)** complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories
- **User Story 2 (P2)**: Can start after T008b (Semantic Features) and T013 (ROI Timecourses) - **Requires T008b and T013**.
- **User Story 3 (P3)**: Can start after T008b (Semantic Features) and T013 (ROI Timecourses) - **Requires T008b and T013**.

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks for that story to validate them.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (none active).
- Once T008b and T013 complete, US2 and US3 can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **ONLY AFTER T008b and T013 complete**.

---

## Parallel Example: User Story 1

```bash
# Launch implementation for User Story 1 (Sequential):
Task: "Orchestrate download of 5-subject subset of ds000234 using code/data/download.py" (T014-RUN)
Task: "Configure and run preprocessing pipeline for 5-subject subset using code/data/preprocess.py" (T011-IMPL-EXEC) -> MUST wait for T014

# Launch tests for User Story 1 (Parallel after implementation):
Task: "Unit test for OpenNeuro downloader in tests/unit/test_download.py"
Task: "Integration test for preprocessing pipeline on 5 subjects in tests/integration/test_preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (5 subjects) - *Note: T008 depends on T012, so T012 must run first*
3. Complete Phase 3 (Continued): T008b (Semantic Features) - *After T012 completes*
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + User Story 1 (T014-T013) → Foundation ready
2. Complete Semantic Features (T008b) → Semantic features ready
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Finalize Documentation (T025-DOC-GENERAL, T033-LIM)
6. No Phase 6 (Reviewer Response) - Removed as out of scope.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Developer A: User Story 1 (T014-T013)
3. Once T012 (Segmentation) completes:
 - Developer B: T008b (Semantic Features)
 - Developer C: T013 (ROI Masker)
4. Once T008b and T013 complete:
 - Developer D: User Story 2
 - Developer E: User Story 3
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Sequential (must wait for previous output)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Implementation first, then Tests)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on GitHub Actions free-tier (limited vCPU and RAM, no GPU) for a small subject subset. The spec (FR-001, SC-005) requires this. If the small-subject analysis exceeds the time limit, the spec/plan must be revised (plan kickback).
- **Data Integrity**: No synthetic data or hard-coded placeholders allowed.
- **Adaptation Note**: The "Encoding vs. Recognition" comparison (FR-004) is implemented as "Early vs. Late Event Stability" per the fallback authorization in FR-003 and FR-004.
- **Metric Definition**: SC-003 (1/N) is implemented using `N_actual` (observed unique labels after aggregation) to ensure calculability. The report documents the aggregation logic.
- **Semantic Features**: Task T008b uses BERT-base-uncased ONLY for RSA (T021) or as covariates. The decoder (T030) uses Neural Patterns -> Labels, avoiding circularity as per Plan methodology.
- **Validation Logic**: T030-PRIMARY now correctly implements FR-011 (held-out text set validation) by **Logging a warning** (not halting) if validation fails, ensuring strict adherence to the spec's "prevent circularity" requirement without introducing unauthorized brittle failure modes.
- **Removed Scope**: Phase 6 (T040-T049) has been **permanently removed** as it contained unapproved scope creep (simulated reviewer feedback) and violated the "Verified Accuracy" principle by implementing features not in the ratified spec.
- **Atlas Constraint**: T009 and Phase 3 notes explicitly mandate **Harvard-Oxford atlas** as per spec US-1, overriding the discrepancy in plan.md Constitution Check table (AAL3). T009 is the single source of truth for execution.
- **Fallback Logic**: T021 and T013 explicitly document the "Early vs. Late" fallback due to missing delayed task data.
- **Timeout Enforcement**: T011 and T011b include explicit timeout enforcement and monitoring logic to meet SC-005.
- **Label Validation**: T004c ensures ground truth integrity by validating the parser against official annotations.
- **Runtime Threshold**: T011b uses a concrete s (6h) threshold as per SC-005, with no fabricated citations.