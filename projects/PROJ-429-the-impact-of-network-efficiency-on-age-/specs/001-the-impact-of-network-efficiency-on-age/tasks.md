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

- [ ] T004 Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length)
- [ ] T005 [P] Implement `code/data/download.py` for PhysioNet/TUH access, checksumming, `trace_id` injection, AND validate metadata (age, cognitive score) to handle missing data flags (covers FR-001 and US1 requirements). **Deliverable**: Ensure code/data/download.py generates `data/quality/download_report.json` with schema: `{"valid_count": int, "invalid_count": int, "total_count": int}`.
- [ ] T005_run [P] **Run** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`.
- [ ] T006 [P] Implement `code/data/preprocess.py` for MNE-Python pipeline (bandpass 1-40Hz, ICA, 10s epochs for connectivity), including logic to reject epochs with >50% artifacts and flag SNR < 10dB (covers FR-002 and US1 requirements). **Note**: This task implements the 10s epoch deviation from FR-002, which is formally ratified in T014a.
- [ ] T006_run [P] **Run** `code/data/preprocess.py` to generate `data/processed/` epochs and flags.
- [ ] T007 [P] Implement `code/network/connectivity.py` for coherence calculation (Welch method on fixed-duration epochs).
- [ ] T007_run [P] **Run** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/`.
- [ ] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient, Modularity, and AUC aggregation across low densities. **Verify**: Each function returns a float or NaN.
- [ ] T008_run [P] **Run** `code/network/metrics.py` to generate `data/results/network_metrics.csv` (intermediate).
- [ ] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple-comparison correction.
- [ ] T010 [P] Implement `code/state/version_map.py` to manage SHA-256 hashes and `updated_at` timestamps (Constitution Principle V).
- [ ] T014a [US1] [Dep: T006_run] **Update `specs/001-network-efficiency-aging/spec.md` Assumptions section** to explicitly record the 10s epoch deviation as a ratified assumption, resolving the conflict with FR-002. **Deliverable**: Verify `spec.md` contains the updated assumption.

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

- [ ] T013 [US1] [Dep: T005_run] Validate `download.py` output: Ensure `data/raw/` contains TUH corpus with metadata flags for missing cognitive scores; **Generate `data/quality/download_report.json`** with keys: `valid_count`, `invalid_count`, `total_count`; verify file exists.
- [ ] T014 [US1] [Dep: T006_run] Validate `preprocess.py` output: Verify 10s epochs are used; **Create `docs/decisions/epoch_length.md`** documenting the 10s vs 2s deviation and verify file exists with content structure: `# Epoch Length Decision`, `## Rationale`, `## Impact`.
- [ ] T015 [US1] [Dep: T007_run] Validate `connectivity.py` output: Ensure coherence matrices are generated for 10-20 system electrodes.
- [ ] T016a [US1] [Dep: T008_run, T007_run, T006_run] Invoke Global Efficiency calculation and validate output values in `data/results/network_metrics.csv`.
- [ ] T016b [US1] [Dep: T008_run, T007_run, T006_run] Invoke Local Efficiency calculation and validate output values in `data/results/network_metrics.csv`.
- [ ] T016c [US1] [Dep: T008_run, T007_run, T006_run] Invoke Modularity and AUC aggregation; verify stability across densities ranging from low to moderate values.
- [ ] T017 [US1] [Dep: T006_run] **Update `data/results/network_metrics.csv`** to include a `signal_quality_flag` column with values 'Low Signal Quality' for SNR < 10dB; verify column exists.
- [ ] T018 [US1] [Dep: T016c, T007_run, T006_run] Implement sensitivity analysis (FR-008) to sweep thresholds and **generate `data/results/sensitivity_report.csv`** containing stability metrics (variation < 0.05).
- [ ] T019 [US1] [Dep: T016a, T016b, T016c, T010] Inject `trace_id` (SHA-256 of source + code hash) into `data/results/network_metrics.csv`.
- [ ] T020 [US1] [Dep: T019, T016a, T016b, T016c] Validate output schema against `contracts/network_metric.schema.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Network Metrics with Age and Cognition (Priority: P2)

**Goal**: Perform statistical correlations (Spearman) between network metrics and age/cognitive scores, applying multiple-comparison correction.

**Independent Test**: Run on a synthetic dataset with known correlations; verify output reports correct coefficients and p-values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for `code/stats/correlation.py` Spearman logic in `tests/unit/test_stats.py`
- [ ] T022 [P] [US2] Unit test for `code/stats/correction.py` FDR/Bonferroni logic in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T023 [US2] [Dep: T016a, T016b, T016c, T004] Implement `code/stats/correlation.py` to perform Spearman rank correlation between metrics and (Age, Cognitive Score).
- [ ] T023_run [US2] [Dep: T023] **Run** `code/stats/correlation.py` to generate `data/results/correlation_results.csv`.
- [ ] T024 [US2] [Dep: T023_run] **Generate `data/results/correlation_results.csv`** excluding rows where cognitive_score is null; verify row count matches expected N for cognitive analysis.
- [ ] T025a [US2] [Dep: T004] Create `data/config/cognitive_instrument_registry.yaml` with hardcoded list of valid instruments (MMSE, MoCA) and references as per FR-007; **treat this file as a hardcoded registry (immutable at runtime)**.
- [ ] T025b [US2] [Dep: T025a] Implement validation logic in `code/stats/correlation.py` to check instruments against registry and flag invalid measures.
- [ ] T026 [US2] [Dep: T009] Apply Bonferroni/FDR correction to the family of tests (multiple metrics vs. multiple outcomes).
- [ ] T027 [US2] [Dep: T023, T009] Implement power analysis (SC-002) to verify minimum power ≥ 0.80 for r=0.3; **generate `data/results/power_analysis.json`** with calculated power, `is_sufficient` flag.
- [ ] T027a [US2] [Dep: T027] **Implement Contingency Handling**: If power < 0.80, generate `data/results/power_contingency_report.json` and trigger 'graceful degradation' (partial report generation); verify contingency path is executable.
- [ ] T028 [US2] [Dep: T023_run, T010] Inject `trace_id` into `data/results/correlation_results.csv`.
- [ ] T029 [US2] [Dep: T028, T023_run] Validate output schema against `contracts/correlation_result.schema.yaml`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Age-Stratified Network Visualization and Regression Analysis (Priority: P3)

**Goal**: Visualize network changes across age groups and run multiple regression controlling for covariates (sex, education).

**Independent Test**: Generate plots from sample data; verify regression output includes coefficients for Age, Sex, Education and plots distinguish age groups.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Integration test for regression and visualization in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T031 [US3] [Dep: T023_run, T016a, T016b, T016c] Implement `code/stats/regression.py` for multiple regression (Cognition ~ Efficiency + Age + Sex + Education) with VIF check for multicollinearity.
- [ ] T031_run [US3] [Dep: T031] **Run** `code/stats/regression.py` to generate `data/results/regression_results.csv`.
- [ ] T032 [US3] [Dep: T031_run] Create `data/results/regression_summary.json` containing a `warnings` array; if N < 15 for Older group, append 'Low Power for Older Group' to the array; verify file exists and contains warning.
- [ ] T033 [US3] [Dep: T032] Implement `code/viz/plots.py` to generate age-stratified bar plots with % CI error bars.
- [ ] T034 [US3] [Dep: T031_run] Generate regression table with coefficients, SE, and p-values; inject `trace_id`.
- [ ] T035 [US3] [Dep: T034, T031_run] Validate output schema against `contracts/regression_result.schema.yaml`.
- [ ] T036 [US3] [Dep: T020, T027, T027a, T032, T029, T035] Generate final summary report including data quality metrics (SC-001), power analysis results (from T027), FWER validation (SC-004), and low-power warnings.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (metrics CSV)
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
Task: "Invoke Global Efficiency (T016a)"
Task: "Invoke Local Efficiency (T016b)"
Task: "Invoke Modularity/AUC (T016c)"
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
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data & Metrics)
   - Developer B: User Story 2 (Stats & Correlation)
   - Developer C: User Story 3 (Regression & Viz)
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
- **Epoch Deviation**: FR-002 (2s epochs) is formally overridden by the ratified assumption in T014a (10s epochs for connectivity stability).
- **Contingency**: T027a ensures graceful degradation if power assumptions are not met.