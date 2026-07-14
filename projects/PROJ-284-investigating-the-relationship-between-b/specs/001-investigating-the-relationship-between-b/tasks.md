# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

**Input**: Design documents from `/specs/001-brain-proprioception-correlation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code/data code/analysis code/viz code/report code/tests data/raw data/processed data/analysis logs docs`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing: `nibabel==5.2.0`, `numpy==1.26.0`, `pandas==2.2.0`, `scikit-learn==1.4.0`, `networkx==3.2.1`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `nilearn==0.10.2`, `requests==2.31.0`, `pytest==7.4.0`, `statsmodels==0.14.1`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management (`code/config.py`) with keys: `HCP_CREDENTIALS`, `BATCH_SIZE`, `MEMORY_LIMIT` (7GB), `HCP_API_VERSION`, `SCHAEFER_ATLAS_URL`
- [X] T005 [P] Implement memory profiling and dynamic batch sizing utility (`code/utils/memory_monitor.py`)
- [X] T006 [P] Setup logging infrastructure with structured logging to `logs/pipeline.log`
- [X] T007 Create base data models (`code/models.py`) with attributes: `Subject` (id, age, sex, motor_score, fd), `ConnectivityMatrix` (data: 400x400 array, atlas_id), `NetworkMetric` (name, value, subject_id), `CorrelationResult` (metric_name, r, p, q, significant, covariate_controlled)
- [X] T008 Setup data directory structure (`data/raw`, `data/processed`, `data/analysis`) with `.gitignore` rules
- [X] T009 Configure retry logic with exponential backoff for HCP API requests

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess HCP data (prioritizing ICA-FIX derived data) to generate clean time-series. **Must include full raw pipeline execution on CI for validation (FR-007).**

**Independent Test**: The pipeline can be fully tested by executing the download and preprocessing scripts on a small subset of HCP data and verifying that output NIfTI files exist with the expected dimensions and that no preprocessing errors are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T010 is a contract test (mocks). T011 is an integration test (requires implementation).

- [X] T010 [P] [US1] Contract test in `tests/unit/test_download.py::test_fetch_returns_nifti_on_success` (mocks HCP API, verifies NIfTI return)
- [X] T011 [US1] Integration test in `tests/integration/test_preprocessing.py::test_preprocessing_quality_tSNR_motion` (runs T013-T015 on subset, verifies tSNR >= 50 and motion < 0.5mm). **DEPENDS ON**: T013, T014, T015 implementation. <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement HCP data fetcher in `code/data/download.py` (supports ICA-FIX verified URLs and raw API fallback). **DEPENDS ON**: T012a.
- [X] T012a [US1] Implement Data Availability Switch logic in `code/data/download.py` to detect ICA-FIX availability. **CRITICAL**: Must include a validation step that executes the FULL raw preprocessing pipeline logic (T013-T015) on a subset of subjects on the CI runner to satisfy FR-007's requirement that the entire pipeline is executable. **IF ICA-FIX is available**, use it for the main run. **IF ICA-FIX is NOT available**, switch to raw. **CI VALIDATION**: Since standard `ubuntu-latest` runners lack FSL/AFNI, this task MUST validate the pipeline logic using **synthetic NIfTI data** and mock tool invocations on CI. If the fallback path is triggered on CI, it must run the synthetic validation, not the actual FSL/AFNI binaries. **DEPENDS ON**: T004, T009.
- [X] T013a [US1] Implement Motion Correction in `code/data/preprocess.py` (fallback-only, subset validation): Use FSL `mcflirt` for motion correction. **LOCAL ONLY**: This task requires FSL installation and Docker or local machine execution; it cannot run on standard `ubuntu-latest` CI. **Output**: `data/processed/sub-XXX_motion_corrected.nii.gz`. **Constraint**: Implement dynamic batch sizing to respect 7GB RAM limit. **DEPENDS ON**: T012a.
- [X] T013b [US1] Implement Slice-Time Correction & Normalization in `code/data/preprocess.py` (fallback-only, subset validation): Use AFNI `3dTshift` and `3dQwarp` for slice-time correction and normalization to MNI space. **LOCAL ONLY**: Requires AFNI/FSL. **Output**: `data/processed/sub-XXX_normalized.nii.gz`. **Constraint**: Implement dynamic batch sizing to respect 7GB RAM limit. **DEPENDS ON**: T013a.
- [X] T013c [US1] Implement Smoothing in `code/data/preprocess.py` (fallback-only, subset validation): Use FSL `fslmaths` for smoothing (mm FWHM). **LOCAL ONLY**: Requires FSL. **Output**: `data/processed/sub-XXX_preproc.nii.gz`. **Constraint**: Implement dynamic batch sizing to respect 7GB RAM limit. **DEPENDS ON**: T013b.
- [X] T014 [US1] Implement tSNR calculator in `code/data/preprocess.py` (mean signal / std dev, excluding initial volumes). **DEPENDS ON**: T013a.
- [X] T015 [US1] Implement motion parameter validator in `code/data/preprocess.py` (threshold < 0.5mm). **DEPENDS ON**: T013a.
- [X] T016 [US1] Implement subject exclusion logic for missing behavioral data in `code/data/download.py`. **DEPENDS ON**: T012.
- [ ] T017 [US1] Extract time-series using the Schaefer high-resolution parcellation atlas in `code/data/metrics.py` (apply motion regression). **CRITICAL**: Must explicitly aggregate node-level vectors for Participation Coefficient and Within-Module Degree into a **single scalar per subject** (mean across nodes) as required by FR-003. **Output**: Time-series matrix AND aggregated scalar values for Participation Coefficient and Within-Module Degree. **DEPENDS ON**: T013a (cleaned NIfTI) AND T015 (motion validation).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Network Metric Extraction and Correlation Analysis (Priority: P2)

**Goal**: Compute graph metrics, perform multivariate analysis, and run correlations with covariates.

**Independent Test**: The analysis can be tested by running the metric extraction and correlation code on a synthetic dataset with known correlations and verifying that the output statistics match the ground truth within an acceptable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test in `tests/unit/test_metrics.py::test_graph_metrics_match_synthetic_ground_truth` (synthetic matrices, verifies modularity/efficiency)
- [ ] T019 [P] [US2] Integration test in `tests/integration/test_correlations.py::test_correlation_with_synthetic_data` (synthetic data, verifies r, p, q values)

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement functional connectivity matrix builder (400x400 Pearson) in `code/data/metrics.py`
- [ ] T021 [US2] Implement graph metric extractor (Modularity, Global Efficiency, Participation Coeff, Within-Module Degree) in `code/data/metrics.py`
- [ ] T022 [US2] Implement aggregation logic for node-level metrics (mean across nodes) in `code/data/metrics.py`
- [~] T023a [US2] Implement PCA on network metrics in `code/analysis/correlations.py`. **Input**: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree]. **Output**: `data/analysis/pca_loadings.csv` (columns: component_1, component_2) AND `data/analysis/factor_scores.csv` (columns: subject_id, pca_factor_1). **DEPENDS ON**: T021, T022. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [~] T023b [US2] Implement File Output & Metric Preservation in `code/analysis/correlations.py`. **Logic**: Merge individual metric columns (from T021/T022) with PCA factor scores into a single output DataFrame. **Output**: `data/analysis/full_metrics.csv` containing all raw metrics AND PCA factors to ensure FR-005 (FDR on individual metrics) and FR-004 (report generation) have access to all data. **DEPENDS ON**: T023a, T021, T022. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [~] T024 [US2] Implement Spearman/Pearson correlation with Framewise Displacement (FD) covariate in `code/analysis/correlations.py`. **CRITICAL**: Apply to **individual metrics** (from T021/T022) for FDR correction as required by FR-005. PCA factors are for exploratory multivariate analysis only. **DEPENDS ON**: T021, T022, T023b. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [~] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis/correlations.py`. **DEPENDS ON**: T024. <!-- FAILED: unspecified -->
- [X] T026 [US2] Implement % Confidence Interval calculation in `code/analysis/power.py` to calculate detectable effect size (r) for achieved N at 80% power (α=0.05, FDR corrected). **NOTE**: This replaces the Spec's FR-008 "post-hoc power analysis" per the Implementation Plan's approved technical strategy. **DEPENDS ON**: T024.
- [ ] T027 [US2] Implement correlation threshold logging (r > 0.3) in `code/analysis/correlations.py` <!-- FAILED: unspecified -->
- [ ] T028 [US2] Implement dynamic batch sizing for matrix computation to respect memory capacity constraints. in `code/analysis/correlations.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting Generation (Priority: P3)

**Goal**: Generate publication-quality plots and a comprehensive Markdown/PDF report.

**Independent Test**: The visualization module can be tested by running the plotting code on a dummy correlation result and verifying that the output image files (PNG/PDF) are generated, labeled correctly with axis titles and p-values, and saved to the designated output directory.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test in `tests/unit/test_viz.py::test_scatter_plot_generates_png_with_annotations` (dummy data, verifies file output and labels)
- [X] T030 [P] [US3] Integration test in `tests/integration/test_report.py::test_report_generates_markdown_with_all_sections` (dummy results, verifies template injection)

### Implementation for User Story 3

- [X] T031 [US3] Implement scatter plot generator (metric vs. score, regression line, annotated r/q) in `code/viz/scatter.py`. **DEPENDS ON**: T024, T025.
- [X] T032 [US3] Implement network diagram generator (module coloring, significant edges) in `code/viz/network.py`. **DEPENDS ON**: T024, T025.
- [X] T033 [US3] Implement report generator in `code/report/generate.py` (Markdown/PDF assembly). **Template**: `templates/report_template.md`. **Variables**: `{{correlation_table}}`, `{{power_analysis}}`, `{{plots}}`, `{{limitations}}`. **Sections**: Must include explicit "Limitation Statement" text: "Motor Task Performance is a proxy for proprioceptive accuracy." Must include "Associational Relationship" phrase: "associational relationship" OR "correlational evidence" in conclusion. **CRITICAL**: Ensure correlation results (from T024) trigger the "associational relationship" phrasing in the conclusion. **DEPENDS ON**: T031, T032, T026, T025.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/` and `README.md`
- [X] T038 Code cleanup and refactoring
- [X] T039 Performance optimization (batching logic verification)
- [X] T040 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T041 Security hardening (API credential handling)
- [X] T042 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output

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
Task: "Contract test for HCP data fetch in tests/unit/test_download.py::test_fetch_returns_nifti_on_success"

# Launch all models for User Story 1 together:
Task: "Create base data models in code/models.py"
Task: "Implement HCP data fetcher in code/data/download.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T012a validation)
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
