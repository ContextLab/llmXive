# Tasks: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Input**: Design documents from `/specs/001-network-efficiency-aging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Project Scope Contingency**: If T005 returns status 'PARTIAL' (missing cognitive data), the project scope is reduced to **EEG-only analysis** (metrics and age correlation). All cognitive correlation tasks (US2, US3) will be skipped or marked as 'N/A' in the final report. This aligns with the Plan's explicit contingency.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per `plan.md` structure)
- Paths shown below assume single project structure defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (code/, data/, state/, tests/, docs/)
- [X] T002 Initialize Python 3.11 project with virtualenv and `requirements.txt` (MNE, NetworkX, SciPy, Pandas, Statsmodels, PyWavelets)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T042d [P] Create `contracts/dataset.schema.yaml` defining the schema for input data validation (columns: participant_id, age, cognitive_instrument, cognitive_score, signal_quality). **Dep**: T001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `docs/decisions/epoch_length.md`. **Content**:
 - `# Epoch Length Decision`
 - `## Rationale`: "Longer epochs provide sufficient spectral resolution for coherence estimation in the low-to-moderate frequency band, reducing variance compared to shorter epochs. This aligns with the ratified specification which mandates a defined number of training epochs."
 - `## Impact`: "Increased epoch duration improves signal-to-noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting-state analysis."
 - `## Spec Reference`: Explicitly references `spec.md` v1.1 which already mandates 10s epochs.
 - **Deliverable**: Verify file exists with this structure. **Verify consistency with spec.md v1.1** to ensure no divergence. **Dep**: T001.
- [X] T014b [P] Create `docs/decisions/connectivity_metric.md`. **Content**:
 - `# Connectivity Metric Decision`
 - `## Rationale`: "Imaginary Coherence is selected over standard Coherence to mitigate volume conduction effects (field spread) which artificially inflate connectivity estimates. This is a standard practice in EEG functional connectivity analysis to ensure valid graph metrics."
 - `## Impact`: "Overrides the generic 'Coherence' requirement in FR-003 with 'Imaginary Coherence' for scientific validity. This decision is ratified here to close the traceability gap."
 - `## Spec Reference`: Explicitly overrides FR-003 for this project.
 - **Deliverable**: Verify file exists with this structure. **Dep**: T001.
- [X] T014c [P] **Formal Ratification**: Update `docs/decisions/` and `spec.md` references to formally ratify the 'Imaginary Coherence' deviation as a Design Decision (T014b) to satisfy traceability requirements. **Deliverable**: Ensure T007 references T014b as the authoritative override for FR-003. **Dep**: T014b.
- [X] T004 [P] Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as per `spec.md` v1.1 and `docs/decisions/epoch_length.md`. **Deliverable**: Generate the 'initial version map of all source code artifacts with SHA-256 hashes' required by FR-006 (code only). Output file path: `state/version_map.yaml`. **Dep**: T014, T014b, T014c.
- [X] T025a [US2] [P] Create `data/config/cognitive_instrument_registry.yaml` with hardcoded list of valid instruments (MMSE, MoCA) and references as per FR-007. **Dep**: T004 (config paths). **Moved to Foundational Phase**.
- [X] T005 [P] Implement `code/data/download.py` for PhysioNet/TUH access (accession ID: `tuh_eeg`), checksumming, and metadata validation. **Validation Logic**:
 1. **Schema Check**: Verify the existence and validity of `contracts/dataset.schema.yaml` (T042d) before proceeding.
 2. **Age Check**: Filter for `age >= 18`.
 3. **FR-007 Compliance**: Validate `cognitive_instrument` field against the registry defined in `data/config/cognitive_instrument_registry.yaml` (T025a). 
    - If valid: Mark as 'Valid'.
    - If invalid instrument: Mark as 'Invalid Instrument' (flag for exclusion in analysis, DO NOT block pipeline).
    - If missing: Mark as 'Missing Cognitive Data' (flag for exclusion in analysis, DO NOT block pipeline).
 4. **Exit Logic**:
    - If `total_valid_eeg_count == 0` (no EEG data at all), **set status to 'BLOCKED'** and **exit with code 0 (SUCCESS)**. Log WARNING: "No valid EEG data found."
    - If `missing_cognitive_count > 0` OR `invalid_instrument_count > 0` (partial data), **set status to 'PARTIAL'** and **exit with code 0 (SUCCESS)**. Log WARNING: "Partial data available. Proceeding with EEG-only analysis for missing/invalid records."
    - If all records have valid cognitive data, **set status to 'OK'**.
 5. **Deliverable**: **Write the validation results to `data/quality/download_report.json`** with schema: `{"valid_count": int, "invalid_instrument_count": int, "missing_cognitive_count": int, "total_count": int, "status": "OK" | "PARTIAL" | "BLOCKED"}`. **Dep**: T042d, T025a.
- [ ] T005_run [P] **Execute** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`. **Verification**: Ensure `data/quality/download_report.json` exists, is non-empty, and matches the schema (specifically the `status` field). **Note**: Execute `python code/data/download.py` (defaults to `data/raw/` if no args). **Dep**: T005.
- [X] T042 [P] Implement chunked streaming in `code/data/download.py` using `mne.io.read_raw_edf` with offset/length parameters to handle large TUH corpus files without exceeding RAM limits. **Dep**: T005.
- [X] T006 [P] Implement `code/data/preprocess.py` for MNE-Python pipeline. **Steps**:
 1. **Bandpass Filter**: Apply 1-40 Hz filter using `mne.filter.filter_data`.
 2. **ICA**: Apply ICA for artifact removal using `mne.preprocessing.ICA`.
 3. **Epoching**: Epoch continuous data into **10-second** segments as per `code/config.py` and `docs/decisions/epoch_length.md`.
 4. **Artifact Rejection**: Reject epochs with >50% artifacts.
 5. **SNR Calculation**: Calculate Signal-to-Noise Ratio (SNR) per epoch; flag SNR < 10dB.
 **Note**: Implementation can be parallel with T005, but execution depends on T005_run. **Dep**: T004.
- [X] T043 [P] Implement chunked streaming in `code/data/preprocess.py` to process epochs in batches, ensuring memory usage stays below 6GB during ICA and filtering. **Dep**: T006.
- [ ] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/` epochs and flags. **Verification**: Verify no GPU devices are visible during execution to confirm CPU-only infrastructure (SC-001). **Dep**: T006, T005_run, T043.
- [X] T007 [P] Implement `code/network/connectivity.py` for **Imaginary Coherence** calculation (Welch method on fixed-duration epochs) to address volume conduction as per Plan's Technical Context and ratified Design Decision **T014b** (which formally overrides FR-003). **Note**: This task **Overrides FR-003** per T014b. **Dep**: T014b, T014c.
- [ ] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/`. **Verification**: Verify no GPU devices are visible during execution to confirm CPU-only infrastructure (SC-001). **Dep**: T007, T006_run.
- [X] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient. **Formula Constraints**:
 - Calculate **Characteristic Path Length** as a distinct metric and output it.
 - Global Efficiency = 1.0 / Characteristic Path Length (Global).
 - Local Efficiency = 1.0 / mean_shortest_path(subgraph). **Critical**: This must be calculated via subgraph path lengths, NOT as the inverse of the global characteristic path length.
 - Ensure Local Efficiency is calculated via subgraph path lengths, NOT the global inverse, to satisfy FR-003's requirement for distinct metrics. **Dep**: T007.
- [ ] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Implementation Note**: Must inject `trace_id` (SHA-256 of source + code hash) into the `trace_id` column during generation. **Update** `state/version_map.yaml` with the SHA-256 hash of the generated `network_metrics.csv` file. **Dep**: T008, T007_run.
- [X] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple-comparison correction.
- [X] T010 [P] Implement `code/state/version_map.py` to manage SHA-256 hashes and `updated_at` timestamps (Constitution Principle V).
- [X] T044 [P] Implement online statistics accumulation in `code/stats/correlation.py` to compute Spearman correlations incrementally if dataset exceeds memory, ensuring statistical validity without full data load. **Dep**: T023.
- [X] T045 [P] Update `code/config.py` to include streaming parameters (chunk_size, memory_limit_mb) and ensure all downstream tasks respect these settings. **Dep**: T004.
- [X] T046 [P] Add logging in `code/data/download.py` and `code/data/preprocess.py` to track memory usage and chunk progress, ensuring transparency during streaming operations. **Dep**: T042, T043.
- [X] T047 [P] Validate streaming implementation with T048 [P] Integration test for chunked processing in `tests/integration/test_streaming.py` to ensure no data loss or corruption during streaming.
- [X] T049 [P] Update `docs/quickstart.md` to include instructions for enabling/disabling streaming mode based on available system resources.
- [X] T050 [P] Add performance benchmarks in `tests/benchmark/test_streaming_performance.py` to compare streaming vs. non-streaming processing times and memory usage.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Power Analysis (Foundational)

**Purpose**: Verify sample size adequacy for the available data (EEG-only or Full) before proceeding to correlation. **Ensures SC-002 compliance for both EEG-only and Full modes.**

- [X] T027 [US2] [P] Implement `code/stats/power.py` for Monte Carlo Power Simulation. **Requirement**: Perform **1000 iterations** with **seed=42**. Simulate datasets with effect size r=0.3. **Input**: Use the **total valid participant count** (N) from `data/quality/download_report.json` (regardless of cognitive data availability) to ensure power analysis is valid for the Age correlation path. If count is 0, skip analysis and report N=0. **Output**: Generate `data/results/power_analysis.json` with schema: `{"power_for_r03": float, "is_sufficient": bool, "simulation_seed": 42, "simulation_log_path": str, "actual_n": int}`. **Dep**: T005_run.

---

## Phase 3: User Story 1 - Compute Graph-Theoretical Network Efficiency Metrics (Priority: P1) 🎯 MVP

**Goal**: Download TUH EEG data, preprocess it, compute functional connectivity, and derive graph metrics (AUC approach) for each participant.

**Independent Test**: Run on a small, fixed subset of PhysioNet data; verify output CSV contains expected metric columns with non-NaN values for valid epochs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for `code/network/metrics.py` graph calculations in `tests/unit/test_metrics.py`
- [X] T012 [P] [US1] Integration test for end-to-end preprocessing and metric generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] [Dep: T005_run] **Validate** `download.py` output: Ensure `data/raw/` contains TUH corpus with metadata flags; verify `data/quality/download_report.json` exists and matches schema. **Do not generate**; only validate. **Dep**: T005_run.
- [ ] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: Ensure `data/processed/connectivity_matrices/` contains `.npy` files with dimensions matching the Standard EEG electrode systems (e.g., high-density or standard montages). Verify non-NaN values. **Dep**: T007_run.
- [X] T016 [US1] [Dep: T008_run] **Validate Derivation**: Verify `data/results/network_metrics.csv` was generated by `code/network/metrics.py` using the correct formulas:
 - `Global_Efficiency = 1.0 / Path_Length`
 - `Local_Efficiency = 1.0 / mean_shortest_path(subgraph)` (calculated via subgraph path lengths, NOT the global inverse).
 - **Deliverable**: `data/results/efficiency_check.json` with `{"formula_verified": bool, "max_deviation": float}`. **Verification Criteria**: Check column names, data types, non-NaN values, and formula verification details. **Tolerance**: `max_deviation` must be < 1e-6. **Dep**: T008_run.
- [X] T017 [US1] [Dep: T016] **Update** `data/results/network_metrics.csv` to include a `signal_quality_flag` column with values 'Low Signal Quality' for SNR < 10dB.
- [X] T018a [US1] [Dep: T006_run, T007_run, T007, T008] Implement sensitivity analysis (FR-008) to **re-run** connectivity and metric computation for network density thresholds **sweeping a range from 0.1 to 0.9 in steps of 0.1** and **generate** `data/results/sensitivity_density_report.csv`. **Schema**: `threshold`, `metric_name` (one of: Global_Efficiency, Local_Efficiency, Clustering_Coeff, Modularity), `mean_value`, `std_dev`, `is_stable` (true if variation < 0.05).
- [X] T018b [US1] [Dep: T006_run, T007_run] Implement sensitivity analysis (SC-003) to **re-run** preprocessing and metric computation for artifact rejection thresholds (e.g., varying epoch rejection rates) and **generate** `data/results/sensitivity_artifact_report.csv`. **Schema**: `rejection_threshold`, `metric_name`, `std_dev`, `is_stable`.
- [ ] T018c [US1] [Dep: T018a, T018b] **Validate Sensitivity**: Aggregate results from T018a and T018b to generate `data/results/sensitivity_summary.json`. **Logic**: **Must wait for T018a and T018b to complete**. If T018a or T018b output files are missing (e.g., if they failed or were skipped), set `overall_stable` to false and `status` to 'PARTIAL'. If files exist, aggregate them. **Schema**: `{"density_stable": bool, "artifact_stable": bool, "overall_stable": bool, "status": str, "reason": str}`. **Dep**: T018a, T018b.
- [ ] T019 [US1] [Dep: T008_run] **Validate** that `trace_id` column exists in `data/results/network_metrics.csv` and contains valid SHA-256 hex strings. **Note**: Injection is handled in T008_run. **Crucial**: If file is missing or empty (e.g., T008_run not executed), log warning and exit 0 (do not block). **Dep**: T008_run.
- [ ] T020 [US1] [Dep: T019] Validate output schema against expected columns (participant_id, age, global_efficiency, local_efficiency, clustering_coeff, modularity, trace_id, signal_quality_flag) and data types. **Dep**: T019.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Network Metrics with Age and Cognition (Priority: P2)

**Goal**: Perform statistical correlations (Spearman) between network metrics and age/cognitive scores, applying multiple-comparison correction. **Note**: This phase only executes if T005_run status is 'OK' or 'PARTIAL' (cognitive data present or partial).

**Independent Test**: Run on a synthetic dataset with known correlations; verify output reports correct coefficients and p-values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for `code/stats/correlation.py` Spearman logic in `tests/unit/test_stats.py`
- [X] T022 [P] [US2] Unit test for `code/stats/correction.py` FDR/Bonferroni logic in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [X] T025b [US2] [Dep: T025a] Implement validation logic in `code/stats/correlation.py` to check instruments against registry and flag invalid measures.
- [X] T025c [US2] [Dep: T005, T025a] Implement logic to propagate 'Invalid Cognitive Measure' flags from `download_report.json` to the final correlation analysis, ensuring participants with invalid instruments are excluded from cognitive correlation as per FR-007. **Deliverable**: Update `code/stats/correlation.py` to filter based on `download_report.json` flags.
- [X] T023 [US2] [Dep: T025b, T025c, T008] **Full Implementation**: Implement `code/stats/correlation.py` to perform Spearman rank correlation between metrics and (Age, Cognitive Score). **Logic**: Use registry validation from T025b and exclusion logic from T025c. **Critical**: Explicitly account for the family of tests (multiple metrics vs. multiple outcomes) when calculating power and error rates (FR-004) using **Bonferroni or FDR** for multiple-comparison correction. **Output**: Generate `data/results/correlation_results.csv` with columns `metric_name`, `outcome`, `spearman_r`, `p_value`, `p_adjusted`, `n`, `trace_id`. **Dep**: T025b, T025c, T008.
- [ ] T023_run [US2] [Dep: T023] **Execute** `code/stats/correlation.py` to generate `data/results/correlation_results.csv` (filtered to exclude null cognitive scores and invalid instruments). **Implementation Note**: Must inject `trace_id` (SHA-256 hex string) into the `trace_id` column during generation. **Update** `state/version_map.yaml` with the SHA-256 hash of the generated `correlation_results.csv` file. **Dep**: T023.
- [ ] T027_run [US2] [Dep: T027] **Execute** `code/stats/power.py` (or integrated in T023) to generate `data/results/power_analysis.json`.
- [ ] T027b [US2] [Dep: T027_run] **Halt Check**: If `power_analysis.json` shows `is_sufficient == false` AND the cause is insufficient sample size (N < 85), **log warning** "Study underpowered for cognitive analysis; skipping cognitive visualization tasks" and **skip** all downstream US2/US3 tasks (T031, T031_run, T034, T035) while **continuing** to Phase 5 (Viz). **Note**: This check applies ONLY to the cognitive analysis path. If T005 returned 'PARTIAL' or 'BLOCKED' for cognitive data, this task is skipped entirely as T023_run would not have run for cognitive scores. **Dep**: T027_run.
- [X] T028 [US2] [Dep: T023_run] **Validate** that `trace_id` column exists in `data/results/correlation_results.csv` and contains valid SHA-256 hex strings. **Note**: Injection is handled in T023_run. **Crucial**: If file is missing or empty (e.g., T023_run not executed), log warning and exit 0 (do not block). **Dep**: T023_run.
- [ ] T029 [US2] [Dep: T028] Validate output schema against expected columns (metric_name, outcome, spearman_r, p_value, p_adjusted, n, trace_id) and data types. **Dep**: T028.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (if data is available)

---

## Phase 5: User Story 3 - Generate Age-Stratified Network Visualization and Regression Analysis (Priority: P3)

**Goal**: Visualize network changes across age groups and run multiple regression controlling for covariates (sex, education).

**Independent Test**: Generate plots from sample data; verify regression output includes coefficients for Age, Sex, Education and plots distinguish age groups.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Integration test for regression and visualization in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T031 [US3] [Dep: T008, T005] **Conditional**: Implement `code/stats/regression.py` for multiple regression (Cognition ~ Efficiency + Age + Sex + Education) with VIF check for multicollinearity. **Note**: ONLY execute if T005_run status is 'OK' (cognitive data available). **Dep**: T008, T005.
- [ ] T031_run [US3] [Dep: T031] **Execute** `code/stats/regression.py` to generate `data/results/regression_results.csv`.
- [ ] T032 [US3] [Dep: T031_run, T027_run] Create `data/results/regression_summary.json` containing a `warnings` array; if `power_analysis.json` (T027_run) shows `is_sufficient == false`, append 'Low Power for Cognitive Analysis' to the array. **Dep**: T027_run.
- [X] T033 [US3] [Dep: T008_run] Implement `code/viz/plots.py` to generate age-stratified bar plots with % CI error bars. **Note**: Always executes (EEG-only viz).
- [ ] T034 [US3] [Dep: T031_run, T032] **Conditional**: Generate regression table with coefficients, SE, and p-values; inject `trace_id`. **Note**: ONLY execute if T005_run status is 'OK' (cognitive data available). **Dep**: T031_run, T032.
- [ ] T035 [US3] [Dep: T034] Validate output schema against expected columns (outcome, predictor, coef, std_err, t_value, p_value, trace_id) and data types. **Dep**: T034.
- [ ] T036 [US3] [Dep: T020, T027, T029, T035, T032, T018c] Generate final summary report including data quality metrics (SC-001), power analysis results (from T027), FWER validation (SC-004), low-power warnings, and sensitivity summary (T018c).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization (ensure execution < 6h on free-tier CI)
- [ ] T040 [P] Additional unit tests in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Power Analysis (Phase 2.5)**: Depends on T005_run completion
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (metrics CSV) AND T005_run success (cognitive data present)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs (conditional on data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all validation tasks for User Story 1 together (after foundation is done):
Task: "Validate download.py output (T013)"
Task: "Validate preprocess.py output (T014)"
Task: "Validate connectivity.py output (T015)"

# Launch metric invocations:
Task: "Validate Derivation (T016)"
Task: "Implement Sensitivity Analysis (T018a, T018b)"
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
3. Add User Story 2 → Test independently → Deploy/Demo (if data available)
4. Add User Story 3 → Test independently → Deploy/Demo (if data available)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Metrics)
 - Developer B: User Story 2 (Stats & Correlation) - *Only if T005_run passes*
 - Developer C: User Story 3 (Regression & Viz) - *Only if T005_run passes*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (for code implementation). Execution order is strictly sequential for dependent tasks (e.g., T005_run before T006_run).
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI with limited resources; no GPU, no deep learning training, no 8-bit quantization.
- **Data Integrity**: No fabrication of data; use real TUH/PhysioNet data only.
- **Traceability**: All tasks now explicitly link to specific FR/SC requirements and output artifacts.
- **Epoch Deviation**: 10s epochs are implemented as per `spec.md` v1.1 and `docs/decisions/epoch_length.md` (T014).
- **Connectivity Deviation**: Imaginary Coherence is implemented as per ratified Design Decision T014b (overriding FR-003).
- **Contingency**: If T005_run returns status 'PARTIAL', the pipeline continues with EEG-only analysis. Cognitive correlation tasks are skipped.
- **Real Data Requirement**: T005 strictly enforces that the pipeline fails loudly on missing real data; no synthetic fallbacks are permitted.
- **Streaming Strategy**: If TUH corpus size exceeds substantial RAM, `download.py` and `preprocess.py` MUST implement chunked streaming (via `mne.io.read_raw_edf` with offset/length or `datasets.load_dataset(..., streaming=True)`) to process the full real dataset without loading it entirely into memory.
- **Sensitivity Analysis**: T018a covers network density (FR-008) with a configurable sweep (0.1 to 0.9), T018b covers artifact rejection (SC-003), T018c aggregates results (handling missing data gracefully).
- **Data Streaming Implementation**: T042-T050 are integrated into Phase 2 and Phase N, with explicit dependencies on T005/T006 and downstream tasks.
- **Power Analysis**: T027 uses Monte Carlo Simulation (1000 iterations, seed=42) to verify power for r=0.3, using actual N from `data/quality/download_report.json` (total N, not just cognitive N).
- **Version Map**: T004 generates initial code hashes; T008_run and T023_run update the map with data artifact hashes.
- **Connectivity Metric**: T007 implements Imaginary Coherence per ratified Design Decision T014b, overriding FR-003's generic Coherence requirement.
- **Data Filtering**: Invalid cognitive instruments are flagged in T005 and excluded in T023/T031, not rejected at the download stage.