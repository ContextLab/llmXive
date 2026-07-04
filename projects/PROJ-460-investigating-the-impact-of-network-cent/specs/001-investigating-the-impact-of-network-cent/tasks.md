# Tasks: Investigating Network Centrality in ASD Resting-State fMRI

**Input**: Design documents from `/specs/001-investigating-the-impact-of-network-centrality/`
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

- [ ] T001 [P] Create project structure per implementation plan by executing: `mkdir -p projects/${PROJECT_ID}/{data/{raw,processed,derived},code,tests/{unit,integration,contract}}` and creating `.gitkeep` files in each data subdirectory.
- [ ] T002 [P] Install `bids-validator` via curl binary in `projects/PROJ-460-investigating-the-impact-of-network-cent/`. Note: `bids-validator` is NOT a Python package; do not include in requirements.txt.
- [ ] T003 [P] Initialize Python 3.11 project with dependencies: `nibabel==5.2.1`, `nilearn==0.10.4`, `networkx==3.2.1`, `scikit-learn==1.5.0`, `pandas==2.2.0`, `numpy==1.26.4`, `scipy==1.13.0`, `pyyaml==6.0.1`, `tqdm==4.66.2`, `statsmodels==0.14.1` in `projects/PROJ-460-investigating-the-impact-of-network-cent/requirements.txt`. **Note**: fMRIPrep is a Docker container dependency, not a Python package; do not include it in requirements.txt. Ensure Docker is installed and accessible in the runner environment.
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-460-investigating-the-impact-of-network-cent/pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement data directory structure: `data/raw`, `data/processed`, `data/derived` with `.gitkeep` files.
- [ ] T006 [P] Create `code/__init__.py` and define module interfaces for `download`, `preprocess`, `atlas`, `graph_analysis`, `statistics`, `classification`, `viz`.
- [ ] T007 [P] Setup logging infrastructure in `code/utils/logging_config.py` that configures a FileHandler writing to `logs/pipeline.log` with JSON format, INFO level, and capturing participant exclusion reasons and preprocessing stats.
- [ ] T008 [P] Implement `code/config.py` to manage environment variables (e.g., `OPENNEURO_BASE_URL`, `RANDOM_SEED`, `PROJECT_ID`, `MAX_MEMORY_GB`).
- [ ] T009 [P] Create `code/state_manager.py` to track artifact hashes in `state/projects/PROJ-460-...yaml` per Constitution Principle V (Versioning Discipline). Specifically: track `data/raw` for raw scans using glob `sub-*_desc-bold.nii.gz` (raw BIDS pattern), and `data/processed` for pre-processed derivatives using glob `*`. Update the `updated_at` timestamp on every change. **Note**: Per Constitution VI, `data/raw` is reserved for raw scans; derivatives are stored in `data/processed`.
- [ ] T010 [P] [US2] Download and validate the Schaefer atlas (multiple parcels) from the official source (https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal). **Requirement**: Must specify a specific version tag or commit hash (e.g., `v1.0.0` or a specific SHA) and verify the downloaded artifact's checksum against a known-good hash to ensure reproducibility (Constitution Principle III). Save to `data/derived/atlas/`. **Must be available before T018**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw ABIDE data, preprocess it using fMRIPrep Docker container, validate outputs, and extract cleaned time-series data for each participant.

**Independent Test**: Run on a sample of 5 participants; verify output files exist in `data/processed` with expected dimensions (timepoints × ROIs) and valid BIDS sidecars. The system MUST retrieve raw data from a verified ABIDE source.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [US1] Contract test for time-series output schema in `tests/contract/test_time_series_schema.py`.
- [ ] T012 [US1] Integration test for download pipeline on 2 participants in `tests/integration/test_download_pipeline.py`.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download.py` to fetch **raw** BIDS fMRI data (NIfTI + JSON) from a verified ABIDE source. **CRITICAL PRE-REQUISITE**: Before executing any download, the script MUST verify that `plan.md` contains a valid, reachable URL in the `# Verified datasets` block. If the block is missing or the URL is invalid, the script MUST abort with a clear error message and log the blocker status. If valid, fetch data (e.g., from the verified ABIDE source), using `bids-validator` to verify integrity. The task MUST filter/select participants to ensure a minimum of ≥100 ASD and ≥100 control participants are downloaded. Read diagnosis labels from `phenotypic.tsv`, column `Diagnosis` (1=ASD, 0=Control). Save raw files to `data/raw`.
- [ ] T014 [US1] Implement `code/preprocess.py` to execute the **fMRIPrep Docker container** (CPU mode, `--omp-nthreads 2`) for motion correction, normalization, and nuisance regression on raw data in `data/raw`. Output pre-processed derivatives to `data/processed`. Record exact fMRIPrep version and parameters in `data/derived/preprocessing_log.yaml` (Constitution VI).
- [ ] T015 [US1] Implement motion exclusion logic in `code/feature_extraction.py`: flag participants with >3mm translation (extracted from fMRIPrep motion parameters in BIDS sidecar JSON) and log the exclusion count and reason to `data/derived/preprocessing_log.yaml`.
- [ ] T016 [US1] Implement missing data handling in `code/feature_extraction.py`: exclude participants with missing diagnosis/age/sex and report counts.
- [ ] T017 [US1] Implement `code/feature_extraction.py` to **generate `valid_participants.csv`** listing all participants that passed exclusion criteria (T015, T016). This artifact is required for downstream tasks (T035). **Depends on T015 and T016 completion**.
- [ ] T018 [US1] Implement `code/feature_extraction.py` to **extract time-series from pre-processed NIfTI files** (output of T014, located in `data/processed`) using the Schaefer atlas (T010). Input must be from `data/processed`. Output to `data/processed/timeseries`. **Depends on T014, T015, T016, T010 completion**.
- [ ] T019 [US1] Validate output against `contracts/participant.schema.yaml` and `contracts/centrality_completeness_report.schema.yaml`.
- [ ] T020 [US1] Calculate preprocessing success rate (valid outputs / total attempts) and explicitly compare it against the SC-001 threshold (≥90%). Log pass/fail status to `data/derived/preprocessing_success_report.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Metric Computation and Group Comparison (Priority: P2)

**Goal**: Compute degree, betweenness, and eigenvector centrality for a set of ROIs, perform FDR-corrected group comparisons, and conduct threshold sensitivity analysis.

**Independent Test**: Run on a subset of participants; Verify centrality values exist for all ROIs with expected ranges and FDR-corrected q-values are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for centrality metrics output in `tests/contract/test_centrality_output_schema.py`.
- [ ] T022 [P] [US2] Integration test for group comparison logic in `tests/integration/test_group_comparison.py`.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/graph_analysis.py` to compute Pearson correlation matrices from time-series files in `data/processed`. Implement **proportional thresholding** logic with a configurable percentage parameter. **Sensitivity Sweep Range**: Explicitly sweep thresholds over the set **{0.10, 0.15, 0.20}** as required by SC-004. **Logic**: If the correlation threshold creates a disconnected graph, adjust threshold to the top percentile and log a warning.
- [ ] T024 [US2] Implement `code/graph_analysis.py` to compute degree, betweenness, and eigenvector centrality using `networkx` for all nodes in the network.
- [ ] T025 [P] [US2] Implement `code/graph_analysis.py` to handle disconnected graphs: adjust threshold to the top percentile and log warning if still disconnected. (Logic also embedded in T023).
- [ ] T026 [US2] Implement `code/statistics.py` to calculate centrality completeness (percentage of participants with valid values for all ROIs) and compare against the SC-002 threshold (≥95%). Log pass/fail status to `data/derived/centrality_completeness_report.yaml`.
- [ ] T027 [US2] Implement `code/statistics.py` to perform **two-sample t-tests** (ASD vs Control) for each centrality metric and ROI as required by FR-005.
- [ ] T028 [US2] Implement `code/statistics.py` to apply FDR correction (q < 0.05) to p-values and output `data/derived/group_comparison_results.csv`.
- [ ] T029 [US2] Implement `code/statistics.py` to perform sensitivity analysis: sweep thresholds over the set **{0.10, 0.15, 0.20}**. Reuse graph construction and centrality logic from T023/T024 for each threshold. Count nodes significant at all thresholds and calculate Jaccard similarity of significant node sets. Save results to `data/derived/sensitivity_analysis.csv`. This task depends on the completion of T023 and T024.
- [ ] T030 [US2] Implement `code/statistics.py` to compute and save collinearity diagnostics (VIF/correlation matrix) for the three centrality metrics in `data/derived/collinearity_diagnostics.yaml`.
- [ ] T031 [US2] Implement `code/statistics.py` to generate descriptive narrative text framing joint relationships descriptively (avoiding causal claims) based on collinearity diagnostics, and save to `data/derived/collinearity_narrative.txt` as required by FR-010.
- [ ] T032 [US2] Validate output against `contracts/centrality_output.schema.yaml`, `contracts/sensitivity_analysis.schema.yaml`, and `contracts/collinearity_diagnostics.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Diagnostic Classification and Visualization (Priority: P3)

**Goal**: Train a logistic regression classifier on centrality features with 5-fold CV and generate brain surface visualizations of significant differences.

**Independent Test**: Run on held-out test set; verify accuracy, AUC, and confusion matrix are reported with confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Contract test for classification results in `tests/contract/test_classification_results_schema.py`.
- [ ] T034 [P] [US3] Integration test for visualization generation in `tests/integration/test_viz_generation.py`.

### Implementation for User Story 3

- [ ] T035 [US3] Implement `code/classification.py` to prepare feature matrix (centrality metrics from T024) and labels (ASD/Control) with stratified splitting. **Depends on T024 and T017 (valid_participants.csv) completion**.
- [ ] T036 [US3] Implement `code/classification.py` to train logistic regression with k-fold cross-validation, reporting accuracy, AUC, and confusion matrix. **Must calculate and save baseline accuracy. If class imbalance ratio > 1.5, report ratio as baseline; otherwise report accuracy.** Calculate and save confidence intervals via bootstrapping in `data/derived/classification_results.yaml`. **Explicitly compare** final metrics against the baseline defined in SC-005 and report the delta.
- [ ] T037 [US3] Implement `code/viz.py` to load significant ROIs from `data/derived/group_comparison_results.csv` (output of T028).
- [ ] T038 [US3] Implement `code/viz.py` to generate brain surface visualizations using `nilearn` showing color-coded effect sizes for significant regions.
- [ ] T039 [US3] Save visualizations to `data/derived/figures/` and validate against `contracts/classification_results.schema.yaml`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Update `README.md` with instructions for running the full pipeline and CI subset. Explicitly document that memory limits are controlled by the `MAX_MEMORY_GB` environment variable defined in `code/config.py` rather than a hardcoded value.
- [ ] T041 Code cleanup: ensure all scripts handle edge cases (missing data, disconnected graphs) gracefully.
- [ ] T042 Add memory profiling to `code/graph_analysis.py` using `tracemalloc` and create `tests/integration/test_memory.py` to assert peak usage **does not exceed the value of `MAX_MEMORY_GB` environment variable defined in `code/config.py`**.

---

## Phase N+1: Power Analysis & Statistical Rigor (Priority: P2)

**Goal**: Ensure statistical validity and report power limitations as required by FR-009 and plan constraints.

**Independent Test**: Verify that power analysis results are generated and included in the final report, and that sample size limitations are explicitly documented.

### Implementation for Power Analysis

- [ ] T043 [US2] Implement `code/statistics.py` to perform a formal power analysis using `statsmodels` (function `TTestIndPower`) before group comparison. Input: estimated effect size (default **[deferred]**; if literature suggests a specific value, it must be cited; otherwise, report power limitations based on available sample size), alpha=0.05, sample size (N per group). Output: `data/derived/power_analysis.yaml` containing minimum detectable effect size and achieved power. **Note**: Do not hardcode a specific effect size like Cohen's d = 0.5 unless explicitly required by a future FR.
- [ ] T044 [US2] Implement logic in `code/statistics.py` to check if N < 80 per group. If so, append a warning to `data/derived/power_analysis.yaml` and ensure the final report explicitly states power limitations (as per plan "Sample size/power is [deferred]" and SC-005).
- [ ] T045 [US2] Integrate power analysis results into the final `data/derived/group_comparison_results.csv` or a separate summary report, ensuring that effect sizes are reported alongside p-values and q-values.
