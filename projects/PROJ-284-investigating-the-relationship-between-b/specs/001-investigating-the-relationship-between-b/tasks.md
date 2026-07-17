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

**Goal**: Download and preprocess HCP data (prioritizing ICA-FIX derived data) to generate clean time-series. **Must include full raw pipeline execution on CI for validation (FR-007) using preprocessed ICA-FIX data for the analysis path; raw preprocessing is local-only.**

**Independent Test**: The pipeline can be fully tested by executing the download and preprocessing scripts on a small subset of HCP data and verifying that output NIfTI files exist with the expected dimensions and that no preprocessing errors are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T010 is a contract test (mocks). T011 is an integration test (requires implementation).

- [X] T010 [P] [US1] Contract test in `tests/unit/test_download.py::test_fetch_returns_nifti_on_success` (mocks HCP API, verifies NIfTI return)
- [X] T011 [US1] Integration test in `tests/integration/test_preprocessing.py::test_preprocessing_quality_tSNR_motion` (runs T013a-T015 on subset, verifies tSNR >= 50 and motion < 0.5mm). **DEPENDS ON**: T013a, T013b, T013c, T014, T015 implementation.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement HCP data fetcher in `code/data/download.py` (supports ICA-FIX verified URLs and raw API fallback). **DEPENDS ON**: T012a. <!-- ATOMIZE: requested -->
- [X] T012a [US1] Implement Data Availability Switch and CI Validation Logic in `code/data/download.py`. **CRITICAL**: This task must detect ICA-FIX availability. **IF ICA-FIX is available**, use it for the main run and execute the **full downstream analysis pipeline** (metrics, correlation) on a small subset (N=5) on the CI runner to validate end-to-end executability. **IF ICA-FIX is NOT available**, switch to raw. **CI VALIDATION**: Do NOT mock FSL/AFNI. Instead, validate the *logic* of the pipeline using real ICA-FIX data on CI. If the raw fallback path is triggered, the task must fail on CI (as FSL/AFNI are missing) and log that raw preprocessing is 'LOCAL ONLY'. **DEPENDS ON**: T004, T009.
- [X] T013a [US1] Implement Motion Correction in `code/data/preprocess.py` (LOCAL ONLY, fallback-only, subset validation): Use FSL `mcflirt` for motion correction. **LOCAL ONLY**: This task requires FSL installation and Docker or local machine execution; it cannot run on standard `ubuntu-latest` CI. **Output**: `data/processed/sub-XXX_motion_corrected.nii.gz`. **Constraint**: Implement dynamic batch sizing to respect 7GB RAM limit. **DEPENDS ON**: T012a.
- [X] T013b [US1] Implement Slice-Time Correction & Normalization in `code/data/preprocess.py` (LOCAL ONLY, fallback-only, subset validation): Use AFNI `3dTshift` and `3dQwarp` for slice-time correction and normalization to MNI space. **LOCAL ONLY**: Requires AFNI/FSL. **Output**: `data/processed/sub-XXX_normalized.nii.gz`. **Constraint**: Implement dynamic batch sizing to respect 7GB RAM limit. **DEPENDS ON**: T013a.
- [X] T013c [US1] Implement Smoothing in `code/data/preprocess.py` (LOCAL ONLY, fallback-only, subset validation): Use FSL `fslmaths` for smoothing (mm FWHM). **LOCAL ONLY**: Requires FSL. **Output**: `data/processed/sub-XXX_preproc.nii.gz`. **Constraint**: Implement dynamic batch sizing to respect 7GB RAM limit. **DEPENDS ON**: T013b.
- [X] T014 [US1] Implement tSNR calculator in `code/data/preprocess.py` (mean signal / std dev, excluding initial volumes). **DEPENDS ON**: T013a.
- [X] T015 [US1] Implement motion parameter validator in `code/data/preprocess.py` (threshold < 0.5mm). **Output**: Always write `validation_status.json` with status 'passed', 'failed', or 'skipped' (if on CI and raw path not taken). **DEPENDS ON**: T013a.
- [X] T016 [US1] Implement subject exclusion logic for missing behavioral data in `code/data/download.py`. **DEPENDS ON**: T012.
- [X] T017 [US1] Extract time-series using the Schaefer high-resolution parcellation atlas in `code/data/metrics.py` (apply motion regression). **CRITICAL**: Must explicitly aggregate node-level vectors for Participation Coefficient and Within-Module Degree into a **single scalar per subject** (mean across nodes) as required by FR-003. **Output**: Time-series matrix AND aggregated scalar values for Participation Coefficient and Within-Module Degree. **DEPENDS ON**: T013a (cleaned NIfTI) OR T012a (ICA-FIX data) AND T015 (validation_status.json or direct data check).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Network Metric Extraction and Correlation Analysis (Priority: P2)

**Goal**: Compute graph metrics, perform multivariate analysis, and run correlations with covariates.

**Independent Test**: The analysis can be tested by running the metric extraction and correlation code on a synthetic dataset with known correlations and verifying that the output statistics match the ground truth within an acceptable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test in `tests/unit/test_metrics.py::test_graph_metrics_match_synthetic_ground_truth`. **Logic**: Generate synthetic 400x400 correlation matrices with `seed=42`, `noise_level=0.1`, and known ground truth modularity/efficiency. Verify calculated metrics match ground truth within 5% tolerance. **DEPENDS ON**: T021.
- [X] T019 [P] [US2] Integration test in `tests/integration/test_correlations.py::test_correlation_with_synthetic_data`. **Logic**: Generate synthetic behavioral scores with `correlation=0.5` against synthetic metrics. Verify output r, p, q values match expected ground truth within 5% tolerance. **DEPENDS ON**: T024.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement functional connectivity matrix builder (400x400 Pearson) in `code/data/metrics.py`
- [X] T021 [US2] Implement graph metric extractor (Modularity, Global Efficiency, Participation Coeff, Within-Module Degree) in `code/data/metrics.py`
- [X] T022 [US2] Implement aggregation logic for node-level metrics (mean across nodes) in `code/data/metrics.py`. **Output**: `data/analysis/aggregated_metrics.csv` (columns: subject_id, modularity, global_efficiency, participation_coef, within_module_degree).
- [X] T023a [US2] Implement PCA on network metrics in `code/analysis/correlations.py`. **Input**: `data/analysis/aggregated_metrics.csv` (columns: modularity, global_efficiency, participation_coef, within_module_degree). **Output**: `data/analysis/pca_loadings.csv` (columns: component_1, component_2) AND `data/analysis/factor_scores.csv` (columns: subject_id, pca_factor_1). **DEPENDS ON**: T021, T022.
- [X] T023b [US2] Implement File Output & Metric Preservation in `code/analysis/correlations.py`. **Logic**: Merge individual metric columns (from T022 `aggregated_metrics.csv`) with PCA factor scores (from T023a `factor_scores.csv`) into a single output DataFrame. **Output**: `data/analysis/full_metrics.csv` containing all raw metrics AND PCA factors to ensure FR-005 (FDR on individual metrics) and FR-004 (report generation) have access to all data. **DEPENDS ON**: T023a, T021, T022.
- [X] T024 [US2] Implement Spearman/Pearson correlation with Framewise Displacement (FD) covariate in `code/analysis/correlations.py`. **CRITICAL**: Apply to **individual metrics** (from T022) for FDR correction as required by FR-005. PCA factors are for exploratory multivariate analysis only. **DEPENDS ON**: T021, T022, T023b.
- [X] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis/correlations.py`. **DEPENDS ON**: T024.
- [X] T025a [US2] Implement Benjamini-Hochberg FDR correction specifically for **individual network metrics** in `code/analysis/correlations.py`. **Logic**: Take p-values for modularity, global efficiency, participation coefficient, and within-module degree from T024. Apply FDR correction (q < 0.05). Output `data/analysis/fdr_corrected_individual.csv` with columns: metric_name, r, p, q, significant. **DEPENDS ON**: T024.
- [X] T026 [US2] Implement post-hoc power analysis in `code/analysis/power.py`. **Logic**: Calculate the detectable effect size (r) for the achieved sample size (N) at 80% power (α=0.05, FDR corrected). **Output**: `data/analysis/power_analysis.csv` with columns: sample_size, power, detectable_effect_size_r, alpha. **DEPENDS ON**: T024.
- [X] T027 [US2] Implement correlation threshold logging (r > 0.3) in `code/analysis/correlations.py`. **CRITICAL**: Log the threshold **after** applying multiple-comparison correction (FDR). **Output**: Log entry "Threshold r > 0.3 applied to FDR-corrected results" and flag metrics meeting both criteria. **DEPENDS ON**: T025a.
- [X] T028 [US2] Implement dynamic batch sizing for matrix computation to respect memory capacity constraints. in `code/analysis/correlations.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting Generation (Priority: P3)

**Goal**: Generate publication-quality plots and a comprehensive Markdown/PDF report.

**Independent Test**: The visualization module can be tested by running the plotting code on a dummy correlation result and verifying that the output image files (PNG/PDF) are generated, labeled correctly with axis titles and p-values, and saved to the designated output directory.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test in `tests/unit/test_viz.py::test_scatter_plot_generates_png_with_annotations` (dummy data, verifies file output and labels)
- [X] T030 [P] [US3] Integration test in `tests/integration/test_report.py::test_report_generates_markdown_with_all_sections` (dummy results, verifies template injection)

### Implementation for User Story 3

- [X] T031 [US3] Implement scatter plot generator (metric vs. score, regression line, annotated r/q) in `code/viz/scatter.py`. **Logic**: For each significant correlation (q < 0.05), generate a plot with x=metric, y=score, regression line, and annotation "r=X.XX, q=X.XX". **Output**: `data/analysis/plots/scatter_metric_name.png`. **DEPENDS ON**: T024, T025a.
- [X] T032 [US3] Implement network diagram generator (module coloring, significant edges) in `code/viz/network.py`. **Logic**: Visualize a medium-scale network. Color nodes by module. Highlight edges with significant correlations (q < 0.05). **Output**: `data/analysis/plots/network_significance.png`. **DEPENDS ON**: T024, T025a.
- [X] T033 [US3] Implement report generator in `code/report/generate.py` (Markdown/PDF assembly). **Template**: `templates/report_template.md`. **Variables**: `{{correlation_table}}`, `{{power_analysis}}`, `{{plots}}`, `{{limitations}}`. **Sections**: Must include explicit "Limitation Statement" text: "Motor Task Performance is a proxy for proprioceptive accuracy." Must include "Associational Relationship" phrase: "associational relationship" OR "correlational evidence" in conclusion. **CRITICAL**: Ensure correlation results (from T024/T025a) trigger the "associational relationship" phrasing in the conclusion. **DEPENDS ON**: T031, T032, T026, T025a.

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

## Revision: Resolving Analysis Findings

**Purpose**: Address specific concerns raised by the `/speckit.analyze` pass regarding unspecified test failures and data flow gaps.

### Implementation for Revision

- [ ] T043 [US2] Refactor `tests/unit/test_metrics.py::test_graph_metrics_match_synthetic_ground_truth` to explicitly define synthetic matrix generation parameters (seed=42, noise=0.1) and expected tolerance thresholds (5%) to resolve "unspecified" failure. **DEPENDS ON**: T021.
- [ ] T044 [US2] Refactor `tests/integration/test_correlations.py::test_correlation_with_synthetic_data` to explicitly define synthetic behavioral data generation (correlation=0.5) and expected r/p/q values to resolve "unspecified" failure. **DEPENDS ON**: T024.
- [ ] T045 [US2] Refactor `code/analysis/correlations.py::test_PCA_implementation` (new unit test) to verify PCA output dimensions and loadings against a known small dataset to resolve "unspecified" failure in T023a. **DEPENDS ON**: T023a.
- [ ] T046 [US2] Refactor `code/analysis/correlations.py::test_file_output_preservation` (new unit test) to verify `full_metrics.csv` contains all required columns (raw + PCA) to resolve "unspecified" failure in T023b. **DEPENDS ON**: T023b.
- [ ] T047 [US2] Refactor `code/analysis/correlations.py::test_correlation_with_covariate` (new unit test) to verify FD covariate adjustment logic and output statistics to resolve "unspecified" failure in T024. **DEPENDS ON**: T024.
- [ ] T048 [US2] Refactor `code/analysis/correlations.py::test_threshold_logging` (new unit test) to verify r > 0.3 logging format and content (post-FDR) to resolve "unspecified" failure in T027. **DEPENDS ON**: T027.
- [ ] T049 [US3] Refactor `code/viz/scatter.py::test_scatter_annotations` (new unit test) to verify exact string formatting of r, q, and p-values in plot annotations to resolve "unspecified" failure in T031. **DEPENDS ON**: T031.
- [ ] T050 [US3] Refactor `code/viz/network.py::test_network_significance_filtering` (new unit test) to verify edge filtering logic based on q < 0.05 to resolve "unspecified" failure in T032. **DEPENDS ON**: T032.
- [ ] T051 [US3] Refactor `code/report/generate.py::test_limitation_statement_inclusion` (new unit test) to verify the exact presence of "Motor Task Performance is a proxy..." and "associational relationship" strings in the generated report to resolve "unspecified" failure in T033. **DEPENDS ON**: T033.
- [ ] T052 [US1] Add explicit error handling in `code/data/download.py` to raise a `DataFetchError` if the HCP API returns a 403 or rate-limit after retries, preventing silent fallback to synthetic data. **DEPENDS ON**: T012.
- [ ] T053 [US1] Add explicit logging in `code/data/download.py` to record the count of excluded subjects due to missing behavioral data, ensuring the final N is reported as per Edge Case requirements. **DEPENDS ON**: T016.
- [ ] T054 [US2] Add explicit dynamic batch size reduction logic in `code/analysis/correlations.py` to handle memory overflow during matrix computation, reducing batch size from default to a smaller value if OOM detected, ensuring completion on modest RAM. **DEPENDS ON**: T028.

