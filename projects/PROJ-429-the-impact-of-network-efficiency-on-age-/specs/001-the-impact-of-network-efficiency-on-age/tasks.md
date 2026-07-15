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
- [ ] T002 Initialize Python 3.11 project with virtualenv and `requirements.txt` (MNE, NetworkX, SciPy, Pandas, Statsmodels, PyWavelets)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as a ratified design decision (see `docs/decisions/epoch_length.md`).
- [ ] T005 [P] Implement `code/data/download.py` for PhysioNet/TUH access (accession ID: `tuh_eeg`), checksumming, and metadata validation. **Validation Logic**:
 1. Check `age >= 18`.
 2. Check `cognitive_score` presence.
 3. **FR-007 Compliance**: Validate `cognitive_instrument` field against a hardcoded registry (MMSE, MoCA). If present but not in registry, flag as "Invalid Instrument". If missing, flag as "Missing Cognitive Data" (do not fail).
 4. **Deliverable**: `data/quality/download_report.json` with schema: `{"valid_count": int, "invalid_instrument_count": int, "missing_cognitive_count": int, "total_count": int}`.
- [ ] T005_run [P] **Execute** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`. **Dep**: T005.
- [ ] T006 [P] Implement `code/data/preprocess.py` for MNE-Python pipeline (bandpass -40Hz, ICA, **10s epochs** as per `code/config.py` and `docs/decisions/epoch_length.md`), including logic to reject epochs with >50% artifacts and flag SNR < 10dB. **Dep**: T004.
- [ ] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/` epochs and flags. **Dep**: T006, T005_run.
- [~] T007 [P] Implement `code/network/connectivity.py` for coherence calculation (Welch method on fixed-duration epochs).
- [ ] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/`. **Dep**: T007, T006_run.
- [~] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient, Modularity. **CRITICAL**: Global/Local Efficiency MUST be calculated as the reciprocal of characteristic_path_length to satisfy FR-003. **Dep**: T007_run.
- [ ] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Dep**: T008, T007_run.
- [ ] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple-comparison correction.
- [ ] T010 [P] Implement `code/state/version_map.py` to manage SHA-256 hashes and `updated_at` timestamps (Constitution Principle V).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Graph-Theoretical Network Efficiency Metrics (Priority: P1) 🎯 MVP

**Goal**: Download TUH EEG data, preprocess it, compute functional connectivity, and derive graph metrics (AUC approach) for each participant.

**Independent Test**: Run on a small, fixed subset of PhysioNet data; verify output CSV contains expected metric columns with non-NaN values for valid epochs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Unit test for `code/network/metrics.py` graph calculations in `tests/unit/test_metrics.py`
- [ ] T012 [P] [US1] Integration test for end-to-end preprocessing and metric generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] [Dep: T005_run] **Validate** `download.py` output: Ensure `data/raw/` contains TUH corpus with metadata flags; verify `data/quality/download_report.json` exists and matches schema. **Do not generate**; only validate.
- [ ] T014 [US1] [Dep: T004] **Create** `docs/decisions/epoch_length.md`. **Content**:
 - `# Epoch Length Decision`
 - `## Rationale`: "10-second epochs provide sufficient spectral resolution for coherence estimation in the 1-40Hz band, reducing variance compared to 2-second epochs. This deviates from initial FR-002 (2s) which has been formally noted as a ratified assumption in the plan."
 - `## Impact`: "Increased epoch duration improves signal-to-noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting-state analysis."
 - Verify file exists with this structure.
- [ ] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: Ensure coherence matrices are generated for 10-20 system electrodes.
- [ ] T016 [US1] [Dep: T008_run] **Validate Derivation**: Verify `data/results/network_metrics.csv` was generated by `code/network/metrics.py` using the formula `Global_Efficiency = 1.0 / Path_Length` and `Local_Efficiency = 1.0 / Path_Length`. **Deliverable**: `data/results/efficiency_check.json` with `{"formula_verified": bool, "max_deviation": float}`. **Tolerance**: `max_deviation` must be < 1e-6.
- [ ] T017 [US1] [Dep: T008_run] **Update** `data/results/network_metrics.csv` to include a `signal_quality_flag` column with values 'Low Signal Quality' for SNR < 10dB.
- [ ] T018 [US1] [Dep: T008_run] Implement sensitivity analysis (FR-008) to sweep thresholds across a range of significance levels and **generate** `data/results/sensitivity_report.csv`. **Schema**: `threshold`, `metric_name`, `std_dev`, `is_stable` (true if variation < 0.05).
- [ ] T019 [US1] [Dep: T010, T008_run] Inject `trace_id` (SHA-256 of source + code hash) into `data/results/network_metrics.csv`.
- [ ] T020 [US1] [Dep: T019] Validate output schema against `contracts/network_metric.schema.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Network Metrics with Age and Cognition (Priority: P2)

**Goal**: Perform statistical correlations (Spearman) between network metrics and age/cognitive scores, applying multiple-comparison correction. **Conditional**: Proceeds only if cognitive data is available.

**Independent Test**: Run on a synthetic dataset with known correlations; verify output reports correct coefficients and p-values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for `code/stats/correlation.py` Spearman logic in `tests/unit/test_stats.py`
- [ ] T022 [P] [US2] Unit test for `code/stats/correction.py` FDR/Bonferroni logic in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T023a [US2] [Dep: T005_run] **Cognitive Data Gate**: Check `data/quality/download_report.json`.
 - If `missing_cognitive_count == total_count` (no cognitive data found): Generate `data/results/cognitive_status.json` with `{"status": "BLOCKED", "reason": "No linked cognitive data found in TUH Corpus"}`. Mark all subsequent tasks in Phase 4 (T025a-T029) as **SKIPPED**. Log status and proceed to Phase 5 (Viz) with EEG-only data.
 - If data exists: Proceed to T025a.
 - **Deliverable**: `data/results/cognitive_status.json`.
- [ ] T025a [US2] [Dep: T023a (proceed)] Create `data/config/cognitive_instrument_registry.yaml` with hardcoded list of valid instruments (MMSE, MoCA) and references as per FR-007.
- [ ] T025b [US2] [Dep: T025a] Implement validation logic in `code/stats/correlation.py` to check instruments against registry and flag invalid measures.
- [ ] T023 [US2] [Dep: T023a (proceed), T025a, T008_run] Implement `code/stats/correlation.py` to perform Spearman rank correlation between metrics and (Age, Cognitive Score). **Logic**: Use registry validation from T025b. **Critical**: Explicitly account for the family of tests (multiple metrics vs. multiple outcomes) when calculating power and error rates (FR-004).
- [ ] T023_run [US2] [Dep: T023] **Execute** `code/stats/correlation.py` to generate `data/results/correlation_results.csv` (filtered to exclude null cognitive scores).
- [ ] T026 [US2] [Dep: T023_run, T009] Apply Bonferroni/FDR correction to the family of tests (multiple metrics vs. multiple outcomes).
- [ ] T027 [US2] [Dep: T023_run] Implement power analysis (SC-002) to verify minimum power ≥ 0.80 for r=0.3; **generate** `data/results/power_analysis.json` with calculated power, `is_sufficient` flag.
- [ ] T027b [US2] [Dep: T027] **Halt Check**: If `power_analysis.json` shows `is_sufficient == false`, log error message: "ERROR: Study underpowered (power < 0.80)" and **exit with code 1**. Study is invalid.
- [ ] T028 [US2] [Dep: T027b (pass)] Inject `trace_id` into `data/results/correlation_results.csv`.
- [ ] T029 [US2] [Dep: T028] Validate output schema against `contracts/correlation_result.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (if data is available)

---

## Phase 5: User Story 3 - Generate Age-Stratified Network Visualization and Regression Analysis (Priority: P3)

**Goal**: Visualize network changes across age groups and run multiple regression controlling for covariates (sex, education).

**Independent Test**: Generate plots from sample data; verify regression output includes coefficients for Age, Sex, Education and plots distinguish age groups.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Integration test for regression and visualization in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T031 [US3] [Dep: T023_run, T016] Implement `code/stats/regression.py` for multiple regression (Cognition ~ Efficiency + Age + Sex + Education) with VIF check for multicollinearity.
- [ ] T031_run [US3] [Dep: T031] **Execute** `code/stats/regression.py` to generate `data/results/regression_results.csv`.
- [ ] T032 [US3] [Dep: T031_run] Create `data/results/regression_summary.json` containing a `warnings` array; if N < 15 for Older group, append 'Low Power for Older Group' to the array.
- [ ] T033 [US3] [Dep: T032] Implement `code/viz/plots.py` to generate age-stratified bar plots with % CI error bars.
- [ ] T034 [US3] [Dep: T031_run, T032] Generate regression table with coefficients, SE, and p-values; inject `trace_id`.
- [ ] T035 [US3] [Dep: T034] Validate output schema against `contracts/regression_result.schema.yaml`.
- [ ] T036 [US3] [Dep: T020, T027, T029, T035, T032] Generate final summary report including data quality metrics (SC-001), power analysis results (from T027), FWER validation (SC-004), and low-power warnings.

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
Task: "Implement Sensitivity Analysis (T018)"
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
- **Epoch Deviation**: 10s epochs are implemented as a ratified design decision in `code/config.py` and `docs/decisions/epoch_length.md`, acknowledging the deviation from FR-002 (2s) as recorded in the plan.
- **Contingency**: T027b ensures the pipeline halts if power is insufficient. No graceful degradation for invalid studies.
- **Real Data Requirement**: T005 and T023a strictly enforce that the pipeline fails loudly on missing real data; no synthetic fallbacks are permitted. T023a handles missing cognitive data by skipping US2/US3 rather than halting the entire pipeline.
- **Streaming Strategy**: If TUH corpus size exceeds substantial RAM, `download.py` and `preprocess.py` MUST implement chunked streaming (via `mne.io.read_raw_edf` with offset/length or `datasets.load_dataset(..., streaming=True)`) to process the full real dataset without loading it entirely into memory.