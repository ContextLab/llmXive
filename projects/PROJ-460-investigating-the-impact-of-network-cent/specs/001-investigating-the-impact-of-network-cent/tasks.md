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

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p projects/${PROJECT_ID}/{data/{raw,processed,derived},code,tests/{unit,integration,contract}}` and creating `.gitkeep` files in each data subdirectory. Also install `bids-validator` via Node.js (npm) or curl binary, as it is not a Python package.
- [ ] T002 Initialize Python 3.11 project with dependencies: `nibabel==5.2.1`, `nilearn==0.10.4`, `networkx==3.2.1`, `scikit-learn==1.5.0`, `pandas==2.2.0`, `numpy==1.26.4`, `scipy==1.13.0`, `pyyaml==6.0.1`, `tqdm==4.66.2` in `projects/PROJ-460-investigating-the-impact-of-network-cent/requirements.txt`. Note: `bids-validator` is NOT a Python package; do not include in requirements.txt.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-460-investigating-the-impact-of-network-cent/pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement data directory structure: `data/raw`, `data/processed`, `data/derived` with `.gitkeep` files.
- [ ] T005 [P] Create `code/__init__.py` and define module interfaces for `download`, `preprocess`, `atlas`, `graph_analysis`, `statistics`, `classification`, `viz`.
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` that configures a FileHandler writing to `logs/pipeline.log` with JSON format, INFO level, and capturing participant exclusion reasons and preprocessing stats.
- [ ] T007 [P] Create schema validation utilities in `code/utils/schema_validator.py` using `pyyaml` to load `contracts/*.schema.yaml`.
- [ ] T008 [P] Implement `code/config.py` to manage environment variables (e.g., `OPENNEURO_BASE_URL`, `RANDOM_SEED`, `PROJECT_ID`, `MAX_MEMORY_GB`).
- [ ] T009 [P] Create `code/state_manager.py` to track artifact hashes in `state/projects/PROJ-460-...yaml` per Constitution Principle V (Versioning Discipline). Specifically: track `data/raw` for raw scans (if any) using glob `sub-*_space-MNI_desc-preproc_bold.nii.gz` (currently empty per strategy), and `data/processed` for pre-processed derivatives using glob `*`. Update the `updated_at` timestamp on every change. **Note**: Per Constitution VI, `data/raw` is reserved for raw scans; derivatives are stored in `data/processed`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download ABIDE pre-processed derivatives, validate them, and extract cleaned time-series data for each participant.

**Independent Test**: Run on a sample of 5 participants; verify output files exist in `data/processed` with expected dimensions (timepoints × ROIs) and valid BIDS sidecars. The system MUST retrieve data from OpenNeuro (ds0002800) for ≥100 ASD and ≥100 control participants.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [US1] Contract test for time-series output schema in `tests/contract/test_time_series_schema.py`.
- [ ] T011 [US1] Integration test for download pipeline on 2 participants in `tests/integration/test_download_pipeline.py`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download.py` to fetch **pre-processed derivatives** (NIfTI + JSON) from OpenNeuro (dataset ID: a selected ABIDE Preprocessed derivatives dataset), using `bids-validator` to verify integrity. The task MUST filter/select participants to ensure a minimum of ≥100 ASD and ≥100 control participants are downloaded. Read diagnosis labels from `phenotypic.tsv`, column `Diagnosis` (1=ASD, 0=Control). Save to `data/processed`. **Crucial**: This task implements the 'External fMRIPrep' strategy by downloading derivatives that are the direct output of fMRIPrep, acknowledging FR-002 is satisfied via external provenance rather than local execution of the Docker container.
- [ ] T013 [US1] Implement `code/preprocess.py` to **validate** the pre-processed derivatives downloaded in T012. Logic: Read BIDS sidecars to extract and record provenance (fMRIPrep version, parameters) in `data/derived/preprocessing_log.yaml`. **Do not run fMRIPrep**; this task confirms the input data meets the spec's requirement for fMRIPrep-processed data.
- [ ] T014 [P] [US1] Implement motion exclusion logic in `code/feature_extraction.py`: flag participants with >3mm translation (extracted from fMRIPrep motion parameters in BIDS sidecar JSON) and log the exclusion count and reason to `data/derived/preprocessing_log.yaml`.
- [ ] T015 [P] [US1] Implement missing data handling in `code/feature_extraction.py`: exclude participants with missing diagnosis/age/sex and report counts.
- [ ] T016 [US1] Validate output against `contracts/participant.schema.yaml` and `contracts/centrality_completeness_report.schema.yaml`.
- [ ] T017 [US1] Implement `code/feature_extraction.py` to **extract time-series from downloaded pre-processed NIfTI files** (output of T012, located in `data/processed`) using the Schaefer atlas. Input must be from `data/processed`. Output to `data/processed/timeseries`. Depends on T013, T014, T015 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Centrality Metric Computation and Group Comparison (Priority: P2)

**Goal**: Compute degree, betweenness, and eigenvector centrality for a set of ROIs, perform FDR-corrected group comparisons, and conduct threshold sensitivity analysis.

**Independent Test**: Run on a subset of participants; Verify centrality values exist for all ROIs with expected ranges and FDR-corrected q-values are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for centrality metrics output in `tests/contract/test_centrality_output_schema.py`.
- [ ] T019 [P] [US2] Integration test for group comparison logic in `tests/integration/test_group_comparison.py`.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/atlas.py` to download and validate the Schaefer atlas (a fine-grained parcellation) from the official source. Save to `data/derived/atlas/`.
- [ ] T021 [US2] Implement `code/graph_analysis.py` to apply the Schaefer atlas (from T020) to the pre-processed NIfTI files (from T012) to generate parcellated time-series.
- [ ] T022 [US2] Implement `code/graph_analysis.py` to compute Pearson correlation matrices from time-series files in `data/processed`. Apply a top percentile edge threshold to create binary adjacency matrices. **Default threshold: a top percentile value**. **Variable range for sensitivity: [deferred], [deferred], [deferred], [deferred]**.
- [ ] T023 [US2] Implement `code/graph_analysis.py` to compute degree, betweenness, and eigenvector centrality using `networkx` for all nodes in the network.
- [ ] T024 [P] [US2] Implement `code/graph_analysis.py` to handle disconnected graphs: adjust threshold to the top percentile and log warning if still disconnected.
- [ ] T025 [US2] Implement `code/statistics.py` to perform sensitivity analysis: sweep thresholds over the set {%, 15%, [deferred], [deferred]} (selected based on literature standards for robustness). Reuse graph construction and centrality logic from T022/T023 for each threshold. Count nodes significant at all thresholds and calculate Jaccard similarity of significant node sets. Save results to `data/derived/sensitivity_analysis.csv`. This task depends on the *logic* of T022/T023, not the static output of T024.
- [ ] T026 [US2] Implement `code/statistics.py` to perform two-sample t-tests (ASD vs Control) for each centrality metric and ROI.
- [ ] T027 [US2] Implement `code/statistics.py` to apply FDR correction (q < 0.05) to p-values and output `data/derived/group_comparison_results.csv`.
- [ ] T028 [US2] Implement `code/statistics.py` to compute and save collinearity diagnostics (VIF/correlation matrix) for the three centrality metrics in `data/derived/collinearity_diagnostics.yaml`.
- [ ] T029 [US2] Implement `code/statistics.py` to generate descriptive narrative text framing joint relationships descriptively (avoiding causal claims) based on collinearity diagnostics, and save to `data/derived/collinearity_narrative.txt` as required by FR-010.
- [ ] T030 [US2] Validate output against `contracts/centrality_output.schema.yaml`, `contracts/sensitivity_analysis.schema.yaml`, and `contracts/collinearity_diagnostics.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Diagnostic Classification and Visualization (Priority: P3)

**Goal**: Train a logistic regression classifier on centrality features with 5-fold CV and generate brain surface visualizations of significant differences.

**Independent Test**: Run on held-out test set; verify accuracy, AUC, and confusion matrix are reported with confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for classification results in `tests/contract/test_classification_results_schema.py`.
- [ ] T032 [P] [US3] Integration test for visualization generation in `tests/integration/test_viz_generation.py`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/classification.py` to prepare feature matrix (centrality metrics from T023) and labels (ASD/Control) with stratified splitting. Depends on T023 completion.
- [ ] T034 [US3] Implement `code/classification.py` to train logistic regression with k-fold cross-validation, reporting accuracy, AUC, and confusion matrix. **Must calculate and save baseline accuracy. If class imbalance ratio > 1.5, report ratio as baseline; otherwise report accuracy.** Calculate and save confidence intervals via bootstrapping (1000 iterations) in `data/derived/classification_results.yaml`.
- [ ] T035 [US3] Implement `code/viz.py` to load significant ROIs from `data/derived/group_comparison_results.csv` (output of T027).
- [ ] T036 [US3] Implement `code/viz.py` to generate brain surface visualizations using `nilearn` showing color-coded effect sizes for significant regions.
- [ ] T037 [US3] Save visualizations to `data/derived/figures/` and validate against `contracts/classification_results.schema.yaml`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update `README.md` with instructions for running the full pipeline and CI subset. Explicitly document that memory limits are controlled by the `MAX_MEMORY_GB` environment variable defined in `code/config.py` rather than a hardcoded value.
- [ ] T039 Code cleanup: ensure all scripts handle edge cases (missing data, disconnected graphs) gracefully.
- [ ] T040 Add memory profiling to `code/graph_analysis.py` using `tracemalloc` and create `tests/integration/test_memory.py` to assert peak usage **does not exceed the value of `MAX_MEMORY_GB` environment variable defined in `code/config.py`**.