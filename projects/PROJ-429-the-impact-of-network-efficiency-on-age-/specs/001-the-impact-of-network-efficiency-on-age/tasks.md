---

# Tasks: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Input**: Design documents from `/specs/001-network-efficiency-aging/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  

Include exact file paths in descriptions.

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per `plan.md` structure)  
- Paths shown below assume single project structure defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (code/, data/, state/, tests/, docs/)
- [X] T002 Initialize Python 3.11 project with virtualenv and `requirements.txt` (MNE, NetworkX, SciPy, Pandas, Statsmodels, PyWavelets)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T042d [P] Create `contracts/dataset.schema.yaml` defining the schema for input data validation (columns: participant_id, age, cognitive_instrument, cognitive_score, signal_quality). **Dep**: T001.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented  

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `docs/decisions/epoch_length.md`. **Content**:
  - `# Epoch Length Decision`
  - `## Rationale`: "Longer epochs provide sufficient spectral resolution for coherence estimation in the low-to-moderate frequency band, reducing variance compared to shorter epochs. This aligns with the ratified specification which mandates a defined number of training epochs."
  - `## Impact`: "Increased epoch duration improves signal‑to‑noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting‑state analysis."
  - `## Spec Reference`: Explicitly references `spec.md` v1.1 which already mandates 10s epochs.
  - **Deliverable**: Verify file exists with this structure. **Verify consistency with spec.md v1.1** to ensure no divergence. **Dep**: T001.
- [X] T014b [P] Create `docs/decisions/connectivity_metric.md`. **Content**:
  - `# Connectivity Metric Decision`
  - `## Rationale`: "Imaginary Coherence is selected over standard Coherence to mitigate volume conduction effects (field spread) which artificially inflate connectivity estimates. This is a standard practice in EEG functional connectivity analysis to ensure valid graph metrics."
  - `## Impact`: "Overrides the generic 'Coherence' requirement in FR‑003 with 'Imaginary Coherence' for scientific validity. This decision is ratified here to close the traceability gap."
  - `## Spec Reference`: Explicitly overrides FR‑003 for this project.
  - **Deliverable**: Verify file exists with this structure. **Dep**: T001.
- [X] T014c [P] **Formal Ratification**: Update `docs/decisions/` and `spec.md` references to formally ratify the 'Imaginary Coherence' deviation as a Design Decision (T014b) to satisfy traceability requirements. **Deliverable**: Ensure T007 references T014b as the authoritative override for FR‑003. **Dep**: T014b.
- [X] T004 [P] Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as per `spec.md` v1.1 and `docs/decisions/epoch_length.md`. **Deliverable**: Generate the 'initial version map of all source code artifacts with SHA‑256 hashes' required by FR‑006 (code only). Output file path: `state/version_map.yaml`. **Dep**: T014, T014b, T014c.
- [X] T025a [US2] [P] Create `data/config/cognitive_instrument_registry.yaml` with hard‑coded list of valid instruments (MMSE, MoCA) and references as per FR‑007. **Dep**: T004.
- [X] T005 [P] Implement `code/data/download.py` for PhysioNet/TUH access (accession ID: `tuh_eeg`), checksumming, and metadata validation. **Validation Logic**:
  1. **Schema Check**: Verify the existence and validity of `contracts/dataset.schema.yaml` (T042d) before proceeding.  
  2. **Age Check**: Filter for `age >= 18`.  
  3. **FR‑007 Compliance**: Validate `cognitive_instrument` field against the registry defined in `data/config/cognitive_instrument_registry.yaml` (T025a).  
     - If valid: Mark as **Valid**.  
     - If invalid instrument: Mark as **Invalid Instrument** (flag for exclusion in analysis, DO NOT block pipeline).  
     - If missing: Mark as **Missing Cognitive Data** (flag for exclusion in analysis, DO NOT block pipeline).  
  4. **Exit Logic**:  
     - If `total_valid_eeg_count == 0` → status **BLOCKED**, exit code 0, log warning.  
     - If `missing_cognitive_count > 0` OR `invalid_instrument_count > 0` → status **PARTIAL**, exit code 0, log warning.  
     - Else status **OK**.  
  5. **Deliverable**: Write validation results to `data/quality/download_report.json` with schema `{"valid_count": int, "invalid_instrument_count": int, "missing_cognitive_count": int, "total_count": int, "status": "OK" | "PARTIAL" | "BLOCKED"}`. **Dep**: T042d, T025a.
- [X] T005_run [P] **Execute** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`. **Verification**: Ensure `download_report.json` exists, is non‑empty, and matches the schema (especially the `status` field). **Dep**: T005.
- [X] T042 [P] Implement chunked streaming in `code/data/download.py` using `mne.io.read_raw_edf` with offset/length parameters to handle large TUH corpus files without exceeding RAM limits. **Dep**: T005.
- [X] T006 [P] Implement `code/data/preprocess.py` for MNE‑Python pipeline. **Steps**:  
  1. Band‑pass filter 1‑40 Hz (`mne.filter.filter_data`).  
  2. ICA artifact removal (`mne.preprocessing.ICA`).  
  3. Epoch into **10‑second** segments (per `code/config.py` & `docs/decisions/epoch_length.md`).  
  4. Reject epochs with >50 % artifacts.  
  5. Calculate SNR per epoch; flag SNR < 10 dB.  
  **Dep**: T004.
- [X] T043 [P] Implement chunked streaming in `code/data/preprocess.py` to process epochs in batches, keeping memory < 6 GB during ICA and filtering. **Dep**: T006.
- [ ] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/epochs/` and flags. **Verification**: Confirm no GPU devices are visible (SC‑001). **Dep**: T006, T005_run, T043.
- [X] T007 [P] Implement `code/network/connectivity.py` for **Imaginary Coherence** calculation (Welch method on fixed‑duration epochs) to address volume conduction as per ratified Design Decision **T014b** (overrides FR‑003). **Dep**: T014b, T014c.
- [ ] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/`. **Verification**: Confirm CPU‑only execution (SC‑001). **Dep**: T007, T006_run.
- [X] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient, Modularity. **Formula Constraints**:  
  - Compute **Characteristic Path Length** explicitly.  
  - `Global_Efficiency = 1.0 / Path_Length`.  
  - `Local_Efficiency = 1.0 / mean_shortest_path(subgraph)` (subgraph‑based).  
  **Dep**: T007.
- [ ] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Implementation Note**: Inject `trace_id` (SHA‑256 of source + code hash) into a `trace_id` column. Update `state/version_map.yaml` with the SHA‑256 hash of the generated CSV. **Dep**: T008, T007_run.
- [X] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple‑comparison correction.
- [X] T010 [P] Implement `code/state/version_map.py` to manage SHA‑256 hashes and `updated_at` timestamps (Constitution Principle V).
- [X] T044 [P] Implement online statistics accumulation in `code/stats/correlation.py` to compute Spearman correlations incrementally if the dataset exceeds memory, ensuring statistical validity without full data load. **Dep**: T023.
- [X] T045 [P] Update `code/config.py` to include streaming parameters (`chunk_size`, `memory_limit_mb`) and ensure downstream tasks respect these settings. **Dep**: T004.
- [X] T046 [P] Add logging in `code/data/download.py` and `code/data/preprocess.py` to track memory usage and chunk progress, ensuring transparency during streaming operations. **Dep**: T042, T043.
- [X] T047 [P] Validate streaming implementation with **T048** integration test (`tests/integration/test_streaming.py`) to ensure no data loss or corruption during streaming. **Dep**: T046.
- [X] T048 [P] Integration test for chunked processing (`tests/integration/test_streaming.py`). **Dep**: T047.
- [X] T049 [P] Update `docs/quickstart.md` to include instructions for enabling/disabling streaming mode based on available system resources.
- [X] T050 [P] Add performance benchmarks (`tests/benchmark/test_streaming_performance.py`) to compare streaming vs. non‑streaming processing times and memory usage.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

## Phase 2.5: Power Analysis (Foundational)

**Purpose**: Verify sample size adequacy for the available data (EEG‑only or Full) before proceeding to correlation. **Ensures SC‑002 compliance for both EEG‑only and Full modes.**

- [X] T027 [US2] [P] Implement `code/stats/power.py` for Monte Carlo power simulation (1000 iterations, seed = 42). Simulate effect size *r* = 0.3 using **total valid participant count** from `download_report.json`. Output `data/results/power_analysis.json` with schema `{"power_for_r03": float, "is_sufficient": bool, "simulation_seed": 42, "simulation_log_path": str, "actual_n": int}`. **Dep**: T005_run.

## Phase 3: User Story 1 – Compute Graph‑Theoretical Network Efficiency Metrics (Priority: P1) 🎯 MVP

**Goal**: Download TUH EEG data, preprocess it, compute functional connectivity, and derive graph metrics (AUC approach) for each participant.

**Independent Test**: Run on a small, fixed subset of PhysioNet data; verify output CSV contains expected metric columns with non‑NaN values for valid epochs.

### Tests for User Story 1 (OPTIONAL)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for `code/network/metrics.py` graph calculations (`tests/unit/test_metrics.py`)
- [X] T012 [P] [US1] Integration test for end‑to‑end preprocessing and metric generation (`tests/integration/test_pipeline.py`)

### Implementation for User Story 1

- [X] T013 [US1] [Dep: T005_run] Validate `download.py` output: ensure `data/raw/` contains TUH corpus with metadata flags; verify `download_report.json` exists and matches schema. **Dep**: T005_run.
- [ ] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: ensure `data/processed/connectivity_matrices/` contains `.npy` files with dimensions matching the standard EEG montage. Verify non‑NaN values. **Dep**: T007_run.
- [X] T016 [US1] [Dep: T008_run] Validate derivation: verify `network_metrics.csv` respects formula constraints (global = 1/PL, local = 1/mean shortest path subgraph). Produce `efficiency_check.json` (`{"formula_verified": bool, "max_deviation": float}`) with `max_deviation` < 1e‑6. **Dep**: T008_run.
- [X] T017 [US1] [Dep: T016] Update `network_metrics.csv` to include a `signal_quality_flag` column (`Low Signal Quality` for SNR < 10 dB).
- [X] T018a [US1] [Dep: T008_run] Sensitivity analysis – sweep network density thresholds 0.1‑0.9 (step 0.1) → `sensitivity_density_report.csv`. Schema: `threshold, metric_name, mean_value, std_dev, is_stable`.
- [X] T018b [US1] [Dep: T006_run, T007_run] Sensitivity analysis – vary artifact‑rejection thresholds → `sensitivity_artifact_report.csv`. Schema: `rejection_threshold, metric_name, std_dev, is_stable`.
- [ ] T018c [US1] [Dep: T018a, T018b] Aggregate sensitivity results → `sensitivity_summary.json` (`{"density_stable": bool, "artifact_stable": bool, "overall_stable": bool, "status": str, "reason": str}`).
- [ ] T019 [US1] [Dep: T018c] Validate that `trace_id` column exists in `network_metrics.csv` and contains valid SHA‑256 hex strings. **Note**: Injection handled in T008_run. Non‑blocking warning if missing.
- [ ] T020 [US1] [Dep: T019] Validate output schema against expected columns (`participant_id, age, global_efficiency, local_efficiency, clustering_coeff, modularity, trace_id, signal_quality_flag`) and data types.
- [X] T051 [US1] [P] Implement a data‑quality check to verify each participant has ≥ 5 valid epochs; flag and exclude participants failing this threshold.
- [X] T052 [US1] [P] Generate a summary report of data‑quality metrics (valid participants, missing cognition, avg valid epochs per participant) → `data/quality/summary_report.json`.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

## Phase 4: User Story 2 – Correlate Network Metrics with Age and Cognition (Priority: P2)

**Goal**: Perform Spearman rank correlations between network metrics and Age/Cognitive scores, applying multiple‑comparison correction. Executes only if `download_report.json` status is **OK** or **PARTIAL**.

**Independent Test**: Run on a synthetic dataset with known correlations; verify output reports correct coefficients and p‑values within tolerance.

### Tests for User Story 2 (OPTIONAL)

- [X] T021 [P] [US2] Unit test for `code/stats/correlation.py` Spearman logic (`tests/unit/test_stats.py`)
- [X] T022 [P] [US2] Unit test for `code/stats/correction.py` FDR/Bonferroni logic (`tests/unit/test_stats.py`)

### Implementation for User Story 2

- [X] T025b [US2] [Dep: T025a] Implement validation in `code/stats/correlation.py` to check instruments against the registry and flag invalid measures.
- [X] T025c [US2] [Dep: T005, T025a] Propagate `Invalid Cognitive Measure` flags from `download_report.json` to correlation analysis; exclude those participants per FR‑007.
- [X] T023 [US2] [Dep: T025b, T025c, T008] Full implementation of Spearman correlation (metrics ↔ Age & Cognitive Score) with Bonferroni/FDR correction. Output `correlation_results.csv` (`metric_name, outcome, spearman_r, p_value, p_adjusted, n, trace_id`). **Dep**: T025b, T025c, T008.
- [ ] T023_run [US2] Execute `code/stats/correlation.py` → generate `correlation_results.csv` (inject `trace_id`). Update `state/version_map.yaml` with CSV hash. **Dep**: T023.
- [ ] T027_run [US2] Execute `code/stats/power.py` → generate `power_analysis.json`. **Dep**: T027.
- [ ] T027b [US2] [Dep: T027_run] Halt check: if `is_sufficient == false` **AND** `actual_n < 85`, log warning *“Study underpowered for cognitive analysis; skipping cognitive visualization tasks”* and skip downstream US2/US3 tasks (T031, T031_run, T034, T035) while continuing to Phase 5. Skip entirely if `download_report.json` status is **PARTIAL** or **BLOCKED**. **Dep**: T027_run.
- [X] T028 [US2] [Dep: T023_run] Validate `trace_id` column exists in `correlation_results.csv` and contains valid SHA‑256 hex strings. Non‑blocking warning if missing.
- [ ] T029 [US2] [Dep: T028] Validate output schema (`metric_name, outcome, spearman_r, p_value, p_adjusted, n, trace_id`) and data types. **Dep**: T028.
- [X] T053 [US2] [P] Sensitivity analysis of multiple‑comparison correction methods (Bonferroni vs. FDR) → `correction_sensitivity_report.csv`. Schema: `method, metric_name, outcome, p_adjusted, is_stable`.

**Checkpoint**: User Stories 1 & 2 should both work independently (if data is available).

## Phase 5: User Story 3 – Generate Age‑Stratified Network Visualization and Regression Analysis (Priority: P3)

**Goal**: Visualize network changes across age groups and run multiple regression controlling for covariates (sex, education).

**Independent Test**: Generate plots from sample data; verify regression output includes coefficients for Age, Sex, Education and plots distinguish age groups.

### Tests for User Story 3 (OPTIONAL)

- [X] T030 [P] [US3] Integration test for regression and visualization (`tests/integration/test_pipeline.py`)

### Implementation for User Story 3

- [X] T031 [US3] [Dep: T008, T005] Conditional implementation of `code/stats/regression.py` (Cognition ~ Efficiency + Age + Sex + Education) with VIF check. Executes only if `download_report.json` status is **OK**. **Dep**: T008, T005.
- [ ] T031_run [US3] Execute `code/stats/regression.py` → generate `regression_results.csv`.
- [ ] T032 [US3] [Dep: T031_run] Create `regression_summary.json` containing a `warnings` array; if `power_analysis.json` shows `is_sufficient == false`, append *“Low Power for Cognitive Analysis”* to the array. **Dep**: T027_run.
- [X] T033 [US3] [Dep: T008_run] Implement `code/viz/plots.py` to generate age‑stratified bar plots with confidence intervals. Always executes (EEG‑only viz).
- [X] T056 [US3] [Dep: T008_run] Implement network‑topology visualizations (e.g., `plot_connectome` & `plot_topomap`) for each age group → `figures/topology_age_{group}.png`. **Dep**: T008_run.
- [ ] T034 [US3] [Dep: T031_run, T032] Conditional: Generate regression table with coefficients, SE, p‑values, inject `trace_id`. **Dep**: T031_run, T032.
- [ ] T035 [US3] [Dep: T034] Validate output schema (`outcome, predictor, coef, std_err, t_value, p_value, trace_id`) and data types. **Dep**: T034.
- [ ] T036 [US3] [Dep: T020, T027, T029, T035, T032, T018c] Generate final summary report (`report/final_report.md`) aggregating data‑quality metrics, power analysis, FWER validation, low‑power warnings, and sensitivity summary.
- [X] T054 [US2] [P] Implement a visualization to display correlation coefficients between network metrics and Age/Cognitive score with confidence intervals → `figures/correlation_heatmap.png`.
- [X] T055 [US3] [P] Implement a script to generate a regression summary report (`report/regression_summary.md`) including coefficients, standard errors, and p‑values for each predictor.

**Checkpoint**: All user stories should now be independently functional.

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization (ensure execution < 6 h on free‑tier CI)
- [ ] T040 [P] Additional unit tests in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure end‑to‑end reproducibility
- [ ] T058 [P] Add GitHub Actions CI workflow (`.github/workflows/ci.yml`) to run linting, tests, and the full pipeline on the free CPU runner.
- [ ] T059 [P] Add unit tests for network‑topology visualizations (`tests/unit/test_viz.py`).
- [ ] T060 [P] Document power‑analysis methodology and results in `docs/power_analysis.md`.
- [ ] T061 [P] Implement graceful handling of missing cognitive scores: participants without cognitive data are automatically excluded from cognitive‑specific analyses but still contribute to age‑only analyses.
- [ ] T062 [P] After every artifact generation step (e.g., `network_metrics.csv`, `correlation_results.csv`, `regression_results.csv`), update `state/version_map.yaml` with the new SHA‑256 hash and timestamp.
- [ ] T063 [P] Create a lightweight Dockerfile for reproducible local execution (CPU‑only) and publish to GitHub Container Registry.

---
