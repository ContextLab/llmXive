---
description: "Task list template for feature implementation"
---

# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

**Input**: Design documents from `/specs/001-brain-proprioception-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification. **Note: No test tasks are included in this list as they were not explicitly requested.**

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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing: `nibabel==5.2.0`, `numpy==1.26.0`, `pandas==2.2.0`, `scikit-learn==1.4.0`, `networkx==3.2.1`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `nilearn==0.10.2`, `requests==2.31.0`, `pytest==7.4.0`, `statsmodels==0.14.1`, `bctpy==1.0.2`, `openneuro-py==2.0.0`, `hcp==0.0.1`
- [X] T003 [P] Configure linting (ruff) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management (`code/config.py`) with keys: `HCP_CREDENTIALS`, `BATCH_SIZE`, `MEMORY_LIMIT` (7GB), `HCP_API_VERSION`, `SCHAEFER_ATLAS_URL`, `PCA_COMPONENTS` (2)
- [X] T004a [P] Generate `pipeline_config.yaml` documenting the 'QC Only' workflow (skipped steps: motion correction, slice-time, normalization) and checksums for Minimal Preprocessed data to satisfy Constitution Principle VI. **Output**: `pipeline_config.yaml`.
- [X] T005 [P] Implement memory profiling and dynamic batch sizing utility (`code/utils/memory_monitor.py`)
- [X] T006 [P] Setup logging infrastructure with structured logging to `logs/pipeline.log`
- [X] T007 Create base data models (`code/models.py`) with attributes: `Subject` (id, age, sex, motor_score, fd), `ConnectivityMatrix` (data: 400x400 array, atlas_id), `NetworkMetric` (name, value, subject_id), `CorrelationResult` (metric_name, r, p, q, significant, covariate_controlled)
- [X] T008 Setup data directory structure (`data/raw`, `data/processed`, `data/analysis`) with `.gitignore` rules
- [X] T009 Configure retry logic with exponential backoff for HCP API requests
- [X] T056 [P] Implement `pipeline_dag.yaml` defining the strict execution order of all tasks to ensure data flow validity. **Output**: `code/utils/pipeline_dag.yaml`. **DEPENDS ON**: T004, T006.
- [X] T057 [P] Implement `DAGExecutor` class in `code/main_pipeline.py` to enforce the DAG defined in T056, ensuring tasks run only when dependencies are met. **Output**: `code/main_pipeline.py` (DAGExecutor). **DEPENDS ON**: T056.
- [X] T058 [P] Implement dependency verification logic in `code/main_pipeline.py` to validate that `data/analysis/` outputs are generated only after `data/raw` and `data/processed` tasks complete. **Output**: `code/main_pipeline.py` (validation logic). **DEPENDS ON**: T057.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download and preprocess HCP data (prioritizing ICA-FIX derived data) to generate clean time-series. **Must include full raw pipeline execution on CI for validation (FR-007) using preprocessed ICA-FIX data for the analysis path; raw preprocessing is local-only.**

**Independent Test**: The pipeline can be fully tested by executing the download and preprocessing scripts on a small subset of HCP data and verifying that output NIfTI files exist with the expected dimensions and that no preprocessing errors are logged.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement HCP data fetcher in `code/data/download.py` (supports ICA-FIX verified URLs). **CRITICAL**: Must use streaming for N=5 subset on CI to prevent OOM. **DEPENDS ON**: T004, T009.
- [X] T014 [US1] Implement tSNR calculator in `code/data/preprocess.py` (mean signal / std dev, excluding the initial volumes). **DEPENDS ON**: T012 (for ICA-FIX data). **Note**: Preprocessing steps (motion correction, etc.) are SKIPPED per Plan; this task performs QC only.
- [X] T014b [US1] Implement tSNR Evidence Recorder in `code/data/preprocess.py`. **CRITICAL**: Must calculate tSNR for all subjects and record the actual percentage of voxels meeting the threshold (≥50) and the count of subjects passing/failing into `data/analysis/qc_summary.csv`. **Output**: `data/analysis/qc_summary.csv`. **DEPENDS ON**: T014a.
- [X] T014a [US1] Implement tSNR threshold enforcement in `code/data/preprocess.py`. **CRITICAL**: Must filter subjects with tSNR < 50 and fail the pipeline if the threshold is not met. **Output**: `validation_status.json` with status 'passed', 'failed', or 'skipped'. **DEPENDS ON**: T014.
- [X] T015 [US1] Implement motion parameter validator in `code/data/preprocess.py` (threshold < 0.5mm). **Output**: Always write `validation_status.json` with status 'passed', 'failed', or 'skipped'. **DEPENDS ON**: T012 (for ICA-FIX data).
- [X] T016 [US1] Implement subject exclusion logic for missing behavioral data in `code/data/download.py`. **DEPENDS ON**: T012.
- [X] T017 [US1] Extract time-series using the Schaefer high-resolution parcellation atlas in `code/data/metrics.py`. **CRITICAL**: Must output the raw time-series matrix (N×T) for each subject. **Output**: Raw time-series matrix (N×T). **DEPENDS ON**: T014a (QC passed). **Note**: Data is pre-denoised; no motion regression applied.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Network Metric Extraction and Correlation Analysis (Priority: P2)

**Goal**: Compute graph metrics, perform multivariate analysis, and run correlations with covariates.

**Independent Test**: The analysis can be tested by running the metric extraction and correlation code on a synthetic dataset with known correlations and verifying that the output statistics match the ground truth within an acceptable tolerance.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement functional connectivity matrix builder (400x400 Pearson) in `code/data/metrics.py`. **DEPENDS ON**: T017.
- [X] T021 [US2] Implement graph metric extractor (Modularity, Participation Coeff, Within-Module Degree) in `code/data/metrics.py`. **CRITICAL**: Must explicitly calculate and output Modularity, Participation Coefficient, and Within-Module Degree. **Output**: `data/analysis/metrics_raw.csv` containing these three metrics. **DEPENDS ON**: T020.
- [X] T021b [US2] Implement Global Efficiency calculation specifically in `code/data/metrics.py`. **CRITICAL**: Must calculate Global Efficiency as a global scalar (not node-level) and append to `data/analysis/metrics_raw.csv`. **Output**: Append `global_efficiency` column to `data/analysis/metrics_raw.csv`. **DEPENDS ON**: T020.
- [ ] T022 [US2] Implement aggregation logic for node-level metrics (mean across nodes) in `code/data/metrics.py`. **CRITICAL**: Must read `metrics_raw.csv` (containing all 4 metrics from T021 and T021b), aggregate Participation Coefficient and Within-Module Degree (node-level) into scalars, and pass Modularity and Global Efficiency (already scalars) through unchanged. **Output**: `data/analysis/aggregated_metrics.csv` containing all four metrics. **DEPENDS ON**: T021, T021b.
- [ ] T023a [US2] Implement PCA on network metrics in `code/analysis/correlations.py`. **Input**: `data/analysis/aggregated_metrics.csv`. **Output**: `data/analysis/pca_loadings.csv` and `data/analysis/factor_scores.csv`.
- [ ] T023b [US2] Implement File Output & Metric Preservation in `code/analysis/correlations.py`. **Output**: `data/analysis/full_metrics.csv`. **DEPENDS ON**: T023a.
- [X] T024 [US2] Implement Spearman/Pearson correlation with Framewise Displacement (FD) covariate in `code/analysis/correlations.py`. **DEPENDS ON**: T023b.
- [ ] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis/correlations.py`. **CRITICAL**: Must merge all p-values (from individual metrics and PCA factors) into a single set, apply FDR correction, and output a single `data/analysis/fdr_corrected_results.csv`. **DEPENDS ON**: T024.
- [X] T026 [US2] Implement post-hoc power analysis in `code/analysis/power.py`. **CRITICAL**: Must output `data/analysis/power_analysis.json` containing detectable effect size (r) for N subjects at 80% power, α=0.05, FDR corrected. **DEPENDS ON**: T025.
- [X] T027 [US2] Implement correlation threshold logging (r > 0.3) in `code/analysis/correlations.py`.
- [X] T028 [US2] Implement dynamic batch sizing for matrix computation to respect memory capacity constraints. **CRITICAL**: CPU-only constraint; NO GPU escape hatch. Must reduce batch size if OOM detected. **DEPENDS ON**: T005.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting Generation (Priority: P3)

**Goal**: Generate publication-quality plots and a comprehensive Markdown/PDF report.

**Independent Test**: The visualization module can be tested by running the plotting code on a dummy correlation result and verifying that the output image files (PNG/PDF) are generated, labeled correctly with axis titles and p-values, and saved to the designated output directory.

### Implementation for User Story 3

- [X] T031 [US3] Implement scatter plot generator (metric vs. score, regression line, annotated r/q) in `code/viz/scatter.py`.
- [X] T032 [US3] Implement network diagram generator (module coloring, significant edges) in `code/viz/network.py`. <!-- FAILED: unspecified -->
- [X] T060 [US3] Implement Power Analysis Integration in `code/report/generate.py`. **CRITICAL**: Must explicitly load `data/analysis/power_analysis.json` (from T026) and embed the detectable effect size into the report text. **Output**: Updates to `reports/summary.md` (logic). **DEPENDS ON**: T026.
- [X] T033 [US3] Implement report generator in `code/report/generate.py` (Markdown/PDF assembly). **CRITICAL**: Must programmatically inject the phrase "associational relationship" or "correlational evidence" and the limitation statement regarding Motor Task Performance as a proxy. Must include the power analysis data from T060. **Output**: `reports/summary.md`. **DEPENDS ON**: T025, T060.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `docs/` and `README.md`
- [X] T038 Code cleanup and refactoring
- [X] T039 Performance optimization (batching logic verification)
- [X] T041 Security hardening (API credential handling)
- [X] T042 Run quickstart.md validation
- [ ] T055 [US2] Implement FDR threshold logging in `code/analysis/correlations.py` to log `q < 0.05` used in analysis log and report. **DEPENDS ON**: T025.

---

## Phase X: Testing (Optional)

**Purpose**: Test tasks are included here for reference. They are OPTIONAL and should only be uncommented if tests are explicitly requested. **Note: No test tasks are included in this list.**

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T061 Reconcile run-book vs implementation for `code/download/fetch_openneuro.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/download/fetch_openneuro.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T062 Reconcile run-book vs implementation for `code/download/fetch_hcp_behavioral.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/download/fetch_hcp_behavioral.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T063 Reconcile run-book vs implementation for `code/preprocess/run_qc_only.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/preprocess/run_qc_only.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T064 Reconcile run-book vs implementation for `code/viz/generate_report.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/viz/generate_report.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T065 Reconcile run-book vs implementation for `code/utils/checksums.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/utils/checksums.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
