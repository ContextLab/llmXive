# Tasks: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Input**: Design documents from `/specs/001-network-efficiency-aging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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
 - `## Rationale`: "Longer epochs provide sufficient spectral resolution for coherence estimation in the low-frequency band, reducing variance compared to shorter epochs. [UNRESOLVED-CLAIM: c_34d218d4 — status=not_enough_info] This deviates from initial FR-002 (2s) which has been formally noted as a ratified assumption in the plan."
 - `## Impact`: "Increased epoch duration improves signal-to-noise ratio for connectivity metrics but reduces the number of independent epochs per recording. [UNRESOLVED-CLAIM: c_a98d6714 — status=not_enough_info] This is acceptable for resting-state analysis."
 - `## Spec Reference`: Explicitly references FR-002 (10s epochs) in `spec.md`.
 - Verify file exists with this structure. **Dep**: T001.
- [X] T004 [P] Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as a ratified design decision [UNRESOLVED-CLAIM: c_d7d1f3f0 — status=not_enough_info] (see `docs/decisions/epoch_length.md` created in T014). **Dep**: T014.
- [X] T025a [US2] [P] Create `data/config/cognitive_instrument_registry.yaml` with hardcoded list of valid instruments (MMSE, MoCA) and references as per FR-007. **Dep**: T004 (config paths). **Moved to Foundational Phase**.
- [ ] T005_download [P] **Download** `code/data/download.py` to fetch TUH EEG Corpus from PhysioNet (accession ID: `tuh_eeg`). **Logic**:
 1. Stream/download EDF files using `mne.io.read_raw_edf` or `datasets.load_dataset(..., streaming=True)` to respect RAM constraints.
 2. Store raw files in `data/raw/`.
 3. **Deliverable**: `data/raw/` directory populated with EDF files. **Dep**: T004.
- [ ] T005_validate [P] **Validate Metadata** in `code/data/download.py`. **Logic**:
 1. Check `age >= 18`. [UNRESOLVED-CLAIM: c_086615e9 — status=not_enough_info]
 2. Check `cognitive_score` presence.
 3. **FR-007 Compliance**: Validate `cognitive_instrument` field against the registry defined in `data/config/cognitive_instrument_registry.yaml` (T025a). If present but not in registry, flag as "Invalid Instrument".
 4. **Missing Data Handling**: If `cognitive_score` field is missing from metadata, flag as "Missing Cognitive Data". **Do not fail**; exit with code 0 and generate warning "Proceeding with EEG-only analysis".
 5. **Deliverable**: `data/quality/download_report.json` with schema: `{"valid_count": int, "invalid_instrument_count": int, "missing_cognitive_count": int, "total_count": int, "records": [{"participant_id": str, "status": "Valid"|"Invalid Instrument"|"Missing Cognitive Data"}]}`. **Dep**: T005_download.
- [ ] T005_run [P] **Execute** `code/data/download.py` (T005_download + T005_validate) to generate `data/raw/` and `data/quality/download_report.json`. **Dep**: T005_download, T005_validate.
- [ ] T006 [P] Implement `code/data/preprocess.py` for MNE-Python pipeline:
 - Bandpass filter (low-frequency cutoff to a suitable frequency threshold).
 - Apply ICA for artifact removal.
 - **Epoch the continuous data into 10-second segments**.
 - Reject epochs with >50% artifacts.
 - **Calculate Signal-to-Noise Ratio (SNR) per epoch** and flag SNR < 10dB.
 - **Output**: Write `data/quality/snr_report.csv` with **exact schema**: `epoch_id` (str), `snr_db` (float), `flag` (str: "Low Signal Quality" if snr_db < 10, else "OK").
 - **Deliverable**: `data/processed/epochs/` and `data/quality/snr_report.csv`. **Dep**: T004.
- [ ] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/` epochs and `data/quality/snr_report.csv`. **Dep**: T006, T005_run.
- [ ] T007 [P] Implement `code/network/connectivity.py` for coherence calculation (Welch method on fixed-duration epochs).
- [ ] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/`. **Dep**: T007, T006_run.
- [ ] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient, Modularity. **CRITICAL**:
 - Global Efficiency = 1.0 / Characteristic Path Length (Global). [UNRESOLVED-CLAIM: c_011c6546 — status=not_enough_info]
 - Local Efficiency = 1.0 / mean_shortest_path(subgraph) [UNRESOLVED-CLAIM: c_2efcf9c6 — status=not_enough_info] (calculated via subgraph path lengths, NOT the global inverse).
 - Ensure Local Efficiency is calculated via subgraph path lengths, NOT the global inverse, to satisfy FR-003's requirement for distinct metrics. **Dep**: T007_run.
- [ ] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Dep**: T008, T007_run.
- [ ] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple-comparison correction.
- [X] T010 [P] Implement `code/state/version_map.py` to manage SHA-256 hashes and `updated_at` timestamps (Constitution Principle V).

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

- [X] T013 [US1] [Dep: T005_run] **Validate** `download.py` output: Ensure `data/raw/` contains TUH corpus with metadata flags; verify `data/quality/download_report.json` exists and matches schema. **Do not generate**; only validate.
- [X] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: Ensure `data/processed/connectivity_matrices/` contains `.npy` files with dimensions matching the Standard EEG electrode systems (e.g., high-density or standard montages). Verify non-NaN values.
- [X] T016 [US1] [Dep: T008_run] **Validate Derivation**: Verify `data/results/network_metrics.csv` was generated by `code/network/metrics.py` using the correct formulas:
 - `Global_Efficiency = 1.0 / Path_Length`
 - `Local_Efficiency = 1.0 / mean_shortest_path(subgraph)` (calculated via subgraph path lengths, NOT the global inverse).
 - **Deliverable**: `data/results/efficiency_check.json` with `{"formula_verified": bool, "max_deviation": float}`. **Tolerance**: `max_deviation` must be < 1e-6. **Dep**: T008_run.
- [ ] T017 [US1] [Dep: T008_run, T006_run] **Merge SNR Flags**: Read `data/quality/snr_report.csv` (generated in T006_run) and `data/results/network_metrics.csv`. Merge the `flag` column into `network_metrics.csv` as `signal_quality_flag`. **Logic**: If any epoch for a participant has `flag == "Low Signal Quality"`, set `signal_quality_flag` to "Low Signal Quality" for that participant. [UNRESOLVED-CLAIM: c_97c6d71a — status=not_enough_info] **Dep**: T008_run, T006_run.
- [ ] T018a [US1] [Dep: T007_run, T008_run] Implement sensitivity analysis (FR-008) to **re-run** connectivity and metric computation for network density thresholds explicitly defined as low, medium, and high levels and **generate** `data/results/sensitivity_density_report.csv`. **Schema**: `threshold`, `metric_name`, `std_dev`, `is_stable` (true if variation < 0.05).
- [ ] T018a_run [P] **Execute** `code/network/sensitivity_density.py` (or equivalent logic in T018a) to generate `data/results/sensitivity_density_report.csv`. **Dep**: T018a.
- [ ] T018b [US1] [Dep: T006_run, T007_run, T008_run] Implement sensitivity analysis (SC-003) to **re-run** preprocessing and metric computation for artifact rejection thresholds (e.g., varying epoch rejection rates) and **generate** `data/results/sensitivity_artifact_report.csv`. **Schema**: `rejection_threshold`, `metric_name`, `std_dev`, `is_stable`.
- [ ] T018b_run [P] **Execute** `code/network/sensitivity_artifact.py` (or equivalent logic in T018b) to generate `data/results/sensitivity_artifact_report.csv`. **Dep**: T018b.
- [ ] T018c [US1] [Dep: T018a_run, T018b_run] **Aggregate Sensitivity**: Combine `data/results/sensitivity_density_report.csv` and `data/results/sensitivity_artifact_report.csv`. **Logic**: Calculate `is_stable` as true if `std_dev < 0.05` for all metrics in both reports. **Deliverable**: `data/results/sensitivity_summary.json`. **Schema**: `{"density_stable": bool, "artifact_stable": bool, "overall_stable": bool}`. **Dep**: T018a_run, T018b_run.
- [ ] T018c_run [P] **Execute** `code/network/sensitivity_aggregator.py` (or equivalent logic in T018c) to generate `data/results/sensitivity_summary.json`. **Dep**: T018c.
- [ ] T019 [US1] [Dep: T010, T017] Inject `trace_id` (SHA-256 hex string of source + code hash) into a column named `trace_id` in `data/results/network_metrics.csv`. **Note**: Requires T017 to have generated the file with flags. **Dep**: T017.
- [ ] T020 [US1] [Dep: T042a, T019] Validate output schema against `contracts/network_metric.schema.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Network Metrics with Age and Cognition (Priority: P2)

**Goal**: Perform statistical correlations (Spearman) between network metrics and age/cognitive scores, applying multiple-comparison correction. **Conditional**: Proceeds only if cognitive data is available.

**Independent Test**: Run on a synthetic dataset with known correlations; verify output reports correct coefficients and p-values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for `code/stats/correlation.py` Spearman logic in `tests/unit/test_stats.py`
- [X] T022 [P] [US2] Unit test for `code/stats/correction.py` FDR/Bonferroni logic in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T023a [US2] [Dep: T005_run] **Cognitive Data Gate**: Check `data/quality/download_report.json`.
 - **Logic**:
 1. If `missing_cognitive_count == total_count` (no cognitive data found) [UNRESOLVED-CLAIM: c_19664a64 — status=not_enough_info]: Generate `data/results/cognitive_status.json` with `{"status": "BLOCKED", "reason": "No linked cognitive data found in TUH Corpus"}`. Mark all subsequent tasks in Phase 4 (T025b-T029) as **SKIPPED**. Log status and proceed to Phase 5 (Viz) with EEG-only data.
 2. If `invalid_instrument_count > 0` but `valid_count > 0`: Proceed to T025b. **Filter** participants with `Invalid Instrument` status from correlation analysis as per FR-007. Do NOT skip the entire analysis.
 3. If `valid_count > 0`: Proceed to T025b.
 - **Deliverable**: `data/results/cognitive_status.json`.
- [X] T025b [US2] [Dep: T025a] Implement validation logic in `code/stats/correlation.py` to check instruments against registry and flag invalid measures.
- [X] T025c [US2] [Dep: T005, T023a] Implement logic to propagate 'Invalid Cognitive Measure' flags from `download_report.json` to the final correlation analysis, ensuring participants with invalid instruments are excluded from cognitive correlation as per FR-007. **Deliverable**: Update `code/stats/correlation.py` to filter based on `download_report.json` flags.
- [ ] T023 [US2] [Dep: T023a (proceed), T025b, T025c, T008_run] Implement `code/stats/correlation.py` to perform Spearman rank correlation between metrics and (Age, Cognitive Score). **Logic**: Use registry validation from T025b and exclusion logic from T025c. **Critical**: Explicitly account for the family of tests (multiple metrics vs. multiple outcomes) when calculating power and error rates (FR-004).
- [ ] T023_run [US2] [Dep: T023] **Execute** `code/stats/correlation.py` to generate `data/results/correlation_results.csv` (filtered to exclude null cognitive scores and invalid instruments).
- [ ] T026 [US2] [Dep: T023_run, T009] **Apply Correction**: Apply Bonferroni/FDR correction to the family of tests (multiple metrics vs. multiple outcomes). **Output**: Generate `data/results/fwer_check.json` with schema: `{"method": str, "family_size": int, "alpha": float, "adjusted_p_values": dict, "significant_count": int}`.
- [ ] T026_run [US2] [Dep: T026] **Execute** `code/stats/correction.py` (or equivalent logic in T026) to generate `data/results/fwer_check.json`.
- [X] T027 [US2] [Dep: T023_run] Implement power analysis (SC-002) to verify minimum power ≥ 0.80 **for the target effect size r=0.3** and **calculate the Minimum Detectable Effect Size (MDES)**. **Requirement**: Perform a simulation that **varies effect sizes** to find the MDES, but explicitly report power for r=0.3. **Deliverable**: `data/results/power_analysis.json` with schema: `{"power_for_r03": float, "is_sufficient": bool, "mdes": float, "simulation_seed": int, "simulation_log_path": str}`.
- [ ] T027_run [US2] [Dep: T027] **Execute** `code/stats/power_analysis.py` to generate `data/results/power_analysis.json`.
- [ ] T027b [US2] [Dep: T027_run] **Halt Check**: If `power_analysis.json` shows `is_sufficient == false` AND the cause is missing cognitive data (N < 85), **log warning** "Study underpowered for cognitive analysis; proceeding with EEG-only analysis" and **continue**. If underpowered due to other reasons (e.g., N < 15 total), **exit with code 1**.
- [ ] T028 [US2] [Dep: T023_run] Inject `trace_id` (SHA-256 hex string) into a column named `trace_id` in `data/results/correlation_results.csv`. **Note**: Requires T023_run to have generated the file. **Dep**: T023_run.
- [ ] T029 [US2] [Dep: T042b, T028] Validate output schema against `contracts/correlation_result.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (if data is available)

---

## Phase 5: User Story 3 - Generate Age-Stratified Network Visualization and Regression Analysis (Priority: P3)

**Goal**: Visualize network changes across age groups and run multiple regression controlling for covariates (sex, education).

**Independent Test**: Generate plots from sample data; verify regression output includes coefficients for Age, Sex, Education and plots distinguish age groups.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Integration test for regression and visualization in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T031 [US3] [Dep: T008_run, T005_run] Implement `code/stats/regression.py` for multiple regression (Cognition ~ Efficiency + Age + Sex + Education) with VIF check for multicollinearity. **Note**: Depends on raw metrics and demographics, NOT correlation results.
- [ ] T031_run [US3] [Dep: T031] **Execute** `code/stats/regression.py` to generate `data/results/regression_results.csv`.
- [ ] T032 [US3] [Dep: T031_run] Create `data/results/regression_summary.json` containing a `warnings` array; if N < 15 for Older group, append 'Low Power for Older Group' to the array.
- [X] T033 [US3] [Dep: T032] Implement `code/viz/plots.py` to generate age-stratified bar plots with % CI error bars **AND network topology visualizations (connectivity matrices/graph plots)** to satisfy FR-005.
- [ ] T034 [US3] [Dep: T031_run] Generate regression table with coefficients, SE, and p-values; inject `trace_id`. **Note**: Requires T031_run to have generated the file. **Dep**: T031_run.
- [ ] T035 [US3] [Dep: T042c, T034] Validate output schema against `contracts/regression_result.schema.yaml`.
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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs

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

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI with limited resources; no GPU, no deep learning training, no 8-bit quantization.
- **Data Integrity**: No fabrication of data; use real TUH/PhysioNet data only.
- **Traceability**: All tasks now explicitly link to specific FR/SC requirements and output artifacts.
- **Epoch Deviation**: 10s epochs are implemented as a ratified design decision in `code/config.py` and `docs/decisions/epoch_length.md` (T014), **formally ratified in spec.md**.
- **Contingency**: T027b ensures the pipeline logs a warning and proceeds with EEG-only analysis if underpowered due to missing cognitive data, rather than halting the entire pipeline. No graceful degradation for invalid studies (e.g., N < 15 total).
- **Real Data Requirement**: T005_download and T005_validate strictly enforce that the pipeline fails loudly on missing real data; no synthetic fallbacks are permitted. T023a handles missing cognitive data by skipping US2/US3 rather than halting the entire pipeline. T005_download exits with code 0 on missing cognitive data to allow EEG-only analysis.
- **Streaming Strategy**: If TUH corpus size exceeds substantial RAM, `download.py` and `preprocess.py` MUST implement chunked streaming (via `mne.io.read_raw_edf` with offset/length or `datasets.load_dataset(..., streaming=True)`) to process the full real dataset without loading it entirely into memory.
- **Sensitivity Analysis**: T018a covers network density (FR-008), T018b covers artifact rejection (SC-003), T018c aggregates results.
- **Data Streaming Implementation**: T005_download and T006 must implement `streaming=True` for dataset loading to respect RAM constraints.
- **Cognitive Data Handling**: T023a explicitly defines the "BLOCKED" state for cognitive analysis if no linked data exists, preventing pipeline failure while maintaining data integrity. **Critical**: T023a distinguishes between "missing data" (skip US2) and "invalid instruments" (filter records), ensuring FR-007 compliance.
- **SNR Flag Propagation**: T006 generates `data/quality/snr_report.csv` immediately. T017 merges these flags into `data/results/network_metrics.csv` to ensure data persistence and compliance with FR-002.
- **FWER Verification**: T026_run generates `data/results/fwer_check.json` to satisfy SC-004 and verify FWER control.
- **Sensitivity Summary**: T018c_run generates `data/results/sensitivity_summary.json` with explicit stability criteria (std_dev < 0.05) to satisfy SC-003.