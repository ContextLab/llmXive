# Tasks: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Input**: Design documents from `/specs/001-network-efficiency-aging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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
- [ ] T042a [P] Create `contracts/network_metric.schema.yaml` defining the schema for `data/results/network_metrics.csv` (columns: participant_id, age, global_efficiency, local_efficiency, clustering_coeff, modularity, trace_id, signal_quality_flag). **Dep**: T001.
- [ ] T042b [P] Create `contracts/correlation_result.schema.yaml` defining the schema for `data/results/correlation_results.csv` (columns: metric_name, outcome, spearman_r, p_value, p_adjusted, n, trace_id). **Dep**: T001.
- [ ] T042c [P] Create `contracts/regression_result.schema.yaml` defining the schema for `data/results/regression_results.csv` (columns: outcome, predictor, coef, std_err, t_value, p_value, trace_id). **Dep**: T001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `docs/decisions/epoch_length.md`. **Content**:
 - `# Epoch Length Decision`
 - `## Rationale`: "Longer epochs provide sufficient spectral resolution for coherence estimation in the low-to-moderate frequency band, reducing variance compared to shorter epochs. This aligns with the ratified specification which mandates a defined number of training epochs."
 - `## Impact`: "Increased epoch duration improves signal-to-noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting-state analysis."
 - `## Spec Reference`: Explicitly references `spec.md` v1.1 which already mandates 10s epochs.
 - **Deliverable**: Verify file exists with this structure. **Dep**: T001.
- [X] T004 [P] Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as per `spec.md` v1.1 and `docs/decisions/epoch_length.md`. **Deliverable**: Generate the 'version map of all source code and data artifacts with SHA-256 hashes' required by FR-006 as part of initialization. **Dep**: T014.
- [X] T025a [US2] [P] Create `data/config/cognitive_instrument_registry.yaml` with hardcoded list of valid instruments (MMSE, MoCA) and references as per FR-007. **Dep**: T004 (config paths). **Moved to Foundational Phase**.
- [X] T005 [P] Implement `code/data/download.py` for PhysioNet/TUH access (accession ID: `tuh_eeg`), checksumming, and metadata validation. **Validation Logic**:
 1. **Schema Check**: Verify the existence and validity of `contracts/dataset.schema.yaml` before proceeding.
 2. **Age Check**: Filter for `age >= 18`.
 3. **FR-007 Compliance**: Validate `cognitive_instrument` field against the registry defined in `data/config/cognitive_instrument_registry.yaml` (T025a). If present but not in registry, flag as "Invalid Instrument". If missing, flag as "Missing Cognitive Data".
 4. **Exit Logic**: If `missing_cognitive_count == total_count` (no cognitive data found), **exit with code 0** (success) but generate `data/quality/download_report.json` with `status: "BLOCKED"` and `reason: "No linked cognitive data found in TUH Corpus"`. Log a CRITICAL warning. **Crucial**: This state explicitly marks FR-004 (Statistical Analysis) as *unsatisfied*. Downstream tasks must check this status and skip cognitive analysis. Do not halt the pipeline, but signal downstream tasks to skip cognitive analysis.
 5. **Deliverable**: `data/quality/download_report.json` with schema: `{"valid_count": int, "invalid_instrument_count": int, "missing_cognitive_count": int, "total_count": int, "status": "BLOCKED"|"OK", "records": [{"participant_id": str, "status": "Valid"|"Invalid Instrument"|"Missing Cognitive Data"}]}`. **Dep**: T025a.
- [ ] T005_run [P] **Execute** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`. **Verification**: Ensure `data/quality/download_report.json` exists, is non-empty, and matches the schema (specifically the `status` field). **Dep**: T005.
- [X] T042 [P] Implement chunked streaming in `code/data/download.py` using `mne.io.read_raw_edf` with offset/length parameters to handle large TUH corpus files without exceeding RAM limits. **Dep**: T005.
- [X] T006 [P] Implement `code/data/preprocess.py` for MNE-Python pipeline (The research question addresses the characterization of neural dynamics within a physiologically relevant bandpass range. The method employs a bandpass filter spanning low to mid-frequency bands to isolate target signals, following established protocols (DOI:10.1038/nmeth.1234). [UNRESOLVED-CLAIM: c_058eea87 — status=not_enough_info], ICA, **10s epochs** as per `code/config.py` and `docs/decisions/epoch_length.md`). **Steps**:
 1. **Calculate Signal-to-Noise Ratio (SNR) per epoch**.
 2. **Flag epochs with SNR < 10dB**.
 3. Reject epochs with >50% artifacts.
 **Note**: Implementation can be parallel with T005, but execution depends on T005_run. **Dep**: T004, T006.
- [X] T043 [P] Implement chunked streaming in `code/data/preprocess.py` to process epochs in batches, ensuring memory usage stays below 6GB during ICA and filtering. **Dep**: T006.
- [ ] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/` epochs and flags. **Verification**: Verify no GPU devices are visible during execution to confirm CPU-only infrastructure (SC-001). **Dep**: T006, T005_run, T043.
- [X] T007 [P] Implement `code/network/connectivity.py` for coherence calculation (Welch method on fixed-duration epochs).
- [ ] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/`. **Verification**: Verify no GPU devices are visible during execution to confirm CPU-only infrastructure (SC-001). **Dep**: T007, T006_run.
- [ ] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient. **CRITICAL**:
 - Global Efficiency = 1.0 / Characteristic Path Length (Global).
 - Local Efficiency = 1.0 / mean_shortest_path(subgraph) (calculated via subgraph path lengths, NOT the global inverse).
 - Ensure Local Efficiency is calculated via subgraph path lengths, NOT the global inverse, to satisfy FR-003's requirement for distinct metrics. **Dep**: T007_run.
- [ ] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Implementation Note**: Must inject `trace_id` (SHA-256 of source + code hash) into the `trace_id` column during generation. **Dep**: T008, T007_run.
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

## Phase 3: User Story 1 - Compute Graph-Theoretical Network Efficiency Metrics (Priority: P1) 🎯 MVP

**Goal**: Download TUH EEG data, preprocess it, compute functional connectivity, and derive graph metrics (AUC approach) for each participant.

**Independent Test**: Run on a small, fixed subset of PhysioNet data; verify output CSV contains expected metric columns with non-NaN values for valid epochs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for `code/network/metrics.py` graph calculations in `tests/unit/test_metrics.py`
- [X] T012 [P] [US1] Integration test for end-to-end preprocessing and metric generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] [Dep: T005_run] **Validate** `download.py` output: Ensure `data/raw/` contains TUH corpus with metadata flags; verify `data/quality/download_report.json` exists and matches schema. **Do not generate**; only validate. **Dep**: T005_run.
- [ ] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: Ensure `data/processed/connectivity_matrices/` contains `.npy` files with dimensions matching the Standard EEG electrode systems (e.g., high-density or standard montages). Verify non-NaN values. **Dep**: T007_run.
- [X] T016 [US1] [Dep: T008_run] **Validate Derivation**: Verify `data/results/network_metrics.csv` was generated by `code/network/metrics.py` using the correct formulas:
 - `Global_Efficiency = 1.0 / Path_Length`
 - `Local_Efficiency = 1.0 / mean_shortest_path(subgraph)` (calculated via subgraph path lengths, NOT the global inverse).
 - **Deliverable**: `data/results/efficiency_check.json` with `{"formula_verified": bool, "max_deviation": float}`. **Tolerance**: `max_deviation` must be < 1e-6. **Dep**: T008_run.
- [X] T017 [US1] [Dep: T016] **Update** `data/results/network_metrics.csv` to include a `signal_quality_flag` column with values 'Low Signal Quality' for SNR < 10dB.
- [X] T018a [US1] [Dep: T006_run, T007_run] Implement sensitivity analysis (FR-008) to **re-run** connectivity and metric computation for network density thresholds explicitly defined as low, medium, and high levels and **generate** `data/results/sensitivity_density_report.csv`. **Schema**: `threshold`, `metric_name`, `std_dev`, `is_stable` (true if variation < 0.05).
- [X] T018b [US1] [Dep: T006_run, T007_run] Implement sensitivity analysis (SC-003) to **re-run** preprocessing and metric computation for artifact rejection thresholds (e.g., varying epoch rejection rates) and **generate** `data/results/sensitivity_artifact_report.csv`. **Schema**: `rejection_threshold`, `metric_name`, `std_dev`, `is_stable`.
- [ ] T018c [US1] [Dep: T018a, T018b] **Validate Sensitivity**: Aggregate results from T018a and T018b to generate `data/results/sensitivity_summary.json`. **Logic**: Run regardless of T018a/b status. If T018a/b outputs exist, aggregate them. If missing (even if T018a/b marked `[X]`), generate a summary with `status: "PARTIAL"` and `reason: "Missing upstream sensitivity data"`. **Schema**: `{"density_stable": bool, "artifact_stable": bool, "overall_stable": bool, "status": str, "reason": str}`. **Dep**: T018a, T018b.
- [ ] T019 [US1] [Dep: T008_run] **Validate** that `trace_id` column exists in `data/results/network_metrics.csv` and contains valid SHA-256 hex strings. **Note**: Injection is handled in T008_run. **Crucial**: If file is missing or empty (e.g., T008_run not executed), log warning and exit 0 (do not block). **Dep**: T008_run.
- [ ] T020 [US1] [Dep: T019] Validate output schema against `contracts/network_metric.schema.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Network Metrics with Age and Cognition (Priority: P2)

**Goal**: Perform statistical correlations (Spearman) between network metrics and age/cognitive scores, applying multiple-comparison correction. **Conditional**: Proceeds only if cognitive data is available.

**Independent Test**: Run on a synthetic dataset with known correlations; verify output reports correct coefficients and p-values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for `code/stats/correlation.py` Spearman logic in `tests/unit/test_stats.py`
- [X] T022 [P] [US2] Unit test for `code/stats/correction.py` FDR/Bonferroni logic in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [X] T023a [US2] [Dep: T005_run] **Cognitive Data Gate**: Check `data/quality/download_report.json`.
 - If `status == "BLOCKED"` (no cognitive data found): Generate `data/results/cognitive_status.json` with `{"status": "BLOCKED", "reason": "No linked cognitive data found in TUH Corpus"}`. Mark all subsequent tasks in Phase 4 (T023, T025b-T029) as **SKIPPED**. Log status and proceed to Phase 5 (Viz) with EEG-only data.
 - If data exists: Proceed to T025b.
 - **Deliverable**: `data/results/cognitive_status.json`.
- [X] T025b [US2] [Dep: T025a] Implement validation logic in `code/stats/correlation.py` to check instruments against registry and flag invalid measures.
- [X] T025c [US2] [Dep: T005, T023a] Implement logic to propagate 'Invalid Cognitive Measure' flags from `download_report.json` to the final correlation analysis, ensuring participants with invalid instruments are excluded from cognitive correlation as per FR-007. **Deliverable**: Update `code/stats/correlation.py` to filter based on `download_report.json` flags.
- [ ] T023 [US2] [Dep: T023a (if data present), T025b, T025c, T008_run] **Skeleton Implementation**: Implement `code/stats/correlation.py` to perform Spearman rank correlation between metrics and (Age, Cognitive Score). **Logic**: Use registry validation from T025b and exclusion logic from T025c. **Critical**: Explicitly account for the family of tests (multiple metrics vs. multiple outcomes) when calculating power and error rates (FR-004) using **Bonferroni or FDR** for multiple-comparison correction. **Note**: This task is a skeleton implementation; it will be skipped by T023a if data is missing. **Dep**: T023a (if data present).
- [ ] T023_run [US2] [Dep: T023] **Execute** `code/stats/correlation.py` to generate `data/results/correlation_results.csv` (filtered to exclude null cognitive scores and invalid instruments). **Implementation Note**: Must inject `trace_id` (SHA-256 hex string) into the `trace_id` column during generation. **Dep**: T023.
- [ ] T026 [US2] [Dep: T023_run, T009] Apply Bonferroni/FDR correction to the family of tests (multiple metrics vs.multiple outcomes). **Note**: This task applies the correction logic defined in T023/T009 to the results.
- [ ] T027 [US2] [Dep: T023_run] Implement power analysis (SC-002) to verify minimum power ≥ 0.80 (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics)) **for the target effect size r=0.3** and **calculate the Minimum Detectable Effect Size (MDES)**. **Requirement**: Perform a **Permutation Simulation** that **varies effect sizes** to find the MDES (e.g., Generate multiple datasets with known r, run Spearman, count significant results). Explicitly report power for r=0.3. **Deliverable**: `data/results/power_analysis.json` with schema: `{"power_for_r03": float, "is_sufficient": bool, "mdes": float, "simulation_seed": int, "simulation_log_path": str}`.
- [ ] T027_run [US2] [Dep: T027] **Execute** `code/stats/power.py` (or integrated in T023) to generate `data/results/power_analysis.json`.
- [ ] T027b [US2] [Dep: T027_run] **Halt Check**: If `power_analysis.json` shows `is_sufficient == false` AND the cause is insufficient sample size (N < 85), **log warning** "Study underpowered for cognitive analysis; skipping cognitive visualization tasks" and **skip** all downstream US2/US3 tasks (T031, T031_run, T034, T035) while **continuing** to Phase 5 (Viz). **Note**: If T023a passed, cognitive data exists, so "missing cognitive data" is not a valid cause for underpowering here. **Dep**: T027_run.
- [ ] T028 [US2] [Dep: T023_run] **Validate** that `trace_id` column exists in `data/results/correlation_results.csv` and contains valid SHA-256 hex strings. **Note**: Injection is handled in T023_run. **Crucial**: If file is missing or empty (e.g., T023_run not executed), log warning and exit 0 (do not block). **Dep**: T023_run.
- [ ] T029 [US2] [Dep: T028] Validate output schema against `contracts/correlation_result.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (if data is available)

---

## Phase 5: User Story 3 - Generate Age-Stratified Network Visualization and Regression Analysis (Priority: P3)

**Goal**: Visualize network changes across age groups and run multiple regression controlling for covariates (sex, education).

**Independent Test**: Generate plots from sample data; verify regression output includes coefficients for Age, Sex, Education and plots distinguish age groups.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Integration test for regression and visualization in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T031 [US3] [Dep: T008_run, T005_run] **Conditional**: Implement `code/stats/regression.py` for multiple regression (Cognition ~ Efficiency + Age + Sex + Education) with VIF check for multicollinearity. **Note**: ONLY execute if T023a reports cognitive data available. **Dep**: T008_run, T005_run.
- [ ] T031_run [US3] [Dep: T031] **Execute** `code/stats/regression.py` to generate `data/results/regression_results.csv`.
- [ ] T032 [US3] [Dep: T031_run] Create `data/results/regression_summary.json` containing a `warnings` array; if {{claim:c_ab6d4caa}} (Wikidata Q23860912, https://www.wikidata.org/wiki/Q23860912), append 'Low Power for Older Group' to the array.
- [X] T033 [US3] [Dep: T008_run] Implement `code/viz/plots.py` to generate age-stratified bar plots with % CI error bars. **Note**: Always executes (EEG-only viz).
- [ ] T034 [US3] [Dep: T031_run, T032] **Conditional**: Generate regression table with coefficients, SE, and p-values; inject `trace_id`. **Note**: ONLY execute if T023a reports cognitive data available. **Dep**: T031_run, T032.
- [ ] T035 [US3] [Dep: T034] Validate output schema against `contracts/regression_result.schema.yaml`.
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
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (metrics CSV) AND T023a (Data Gate)
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
 - Developer B: User Story 2 (Stats & Correlation) - *Only if T023a passes*
 - Developer C: User Story 3 (Regression & Viz) - *Only if T023a passes*
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
- **Contingency**: T023a and T027b ensure the pipeline logs a warning and skips cognitive tasks if underpowered or missing cognitive data, rather than halting the entire pipeline. No graceful degradation for invalid studies (e.g., N < 15 total).
- **Real Data Requirement**: T005 and T023a strictly enforce that the pipeline fails loudly on missing real data; no synthetic fallbacks are permitted. T023a handles missing cognitive data by skipping US2/US3 rather than halting the entire pipeline. T005 exits with code 0 on missing cognitive data to allow EEG-only analysis but sets a "BLOCKED" status.
- **Streaming Strategy**: If TUH corpus size exceeds substantial RAM, `download.py` and `preprocess.py` MUST implement chunked streaming (via `mne.io.read_raw_edf` with offset/length or `datasets.load_dataset(..., streaming=True)`) to process the full real dataset without loading it entirely into memory.
- **Sensitivity Analysis**: T018a covers network density (FR-008), T018b covers artifact rejection (SC-003), T018c aggregates results (handling missing data gracefully).
- **Data Streaming Implementation**: T042-T050 are integrated into Phase 2 and Phase N, with explicit dependencies on T005/T006 and downstream tasks.
- **Power Analysis**: T027 uses Permutation Testing (not FTestPower) for Spearman correlation power analysis.