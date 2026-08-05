# Tasks: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Input**: Design documents from `/specs/001-evaluating-dp-federated-learning/`
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

- [ ] T001 [P] Create project structure per implementation plan: `mkdir -p code/data code/training code/analysis code/models tests/unit tests/integration data/raw data/partitions results artifacts` in `projects/PROJ-044-evaluating-the-effectiveness-of-differen/`. **Completion Criterion**: Execute `tree` or `find` command and redirect output to `tree_output.txt` to verify creation deterministically.
- [X] T002 [P] Initialize Python 3.10+ project with PyTorch, Opacus, Hugging Face datasets, pandas, scipy, numpy, matplotlib, statsmodels in `requirements.txt` containing pinned versions
- [ ] T003 [P] Configure linting (black, ruff) and formatting tools in `.pre-commit-config.yaml`. **Requirement**: Must include hooks for `black`, `ruff`, and `pre-commit-hooks` to ensure valid configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement data checksumming and verification utility in `code/data/checksum_utils.py`
- [X] T005 [P] Setup experiment logging infrastructure (CSV + JSON) in `code/training/logging.py`
- [X] T006 [P] Create base configuration management for seeds, α, ε values and dataset name in `code/config.py` defining a `Config` dataclass with fields: `seed: int`, `alpha: float`, `epsilon: float`, `dataset: str` (valid values: "femnist" only; "shakespeare" must raise ValueError with message: "Shakespeare excluded per plan.md Gap Analysis (no verified source).")
- [X] T007 Create base model entity (Small CNN/MLP) for FEMNIST in `code/models/cnn.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Heterogeneity Simulation (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible client data partitions from FEMNIST using Dirichlet distributions with varying α to establish a controlled baseline. (Shakespeare excluded per plan.md).

**⚠️ SPEC DISCREPANCY NOTE**: FR-001 and US-1 Scenario 2 in spec.md mandate Shakespeare. Plan.md Gap Analysis explicitly excludes Shakespeare due to lack of verified sources. The tasks below implement FEMNIST ONLY. Any task attempting Shakespeare is DEPRECATED and must raise an error.

**Independent Test**: Run partitioning script with specific seeds and α values; verify label distributions match theoretical expectations (high variance for α=0.1, balanced for α=1.0) without training.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for Dirichlet partitioning logic verifying label distribution variance in `tests/unit/test_partition.py`
- [X] T010 [P] [US1] Reproducibility test ensuring identical partitions with same seed in `tests/unit/test_partition.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement FEMNIST data downloader using Hugging Face `datasets` (Verified Source: `leaf/femnist` per plan.md) in `code/data/download.py`. **Completion Criterion**: The task is only complete when `data/raw/femnist.parquet` and `data/raw/femnist.sha256` exist on disk. Save downloaded data to `data/raw/femnist.parquet` and generate `data/raw/femnist.sha256`. No synthetic fallback allowed. If dataset != "femnist", raise ValueError.
- [X] T008 [P] [US1] Setup error handling for data fetch failures in `code/data/download.py`. MUST implement retry logic (3 attempts with exponential backoff) before failing loudly with a clear error message. NO synthetic fallback allowed. **Constraint**: If the requested dataset is not "femnist" (e.g., "shakespeare"), the script MUST fail loudly with a specific error indicating the dataset is unverified/excluded per plan.md. **Dependency**: Depends on T011 completion (Refine fetch logic).
- [X] T030 [P] [US1] Refactor `code/data/download.py` to remove all `try/except` blocks that suppress errors, ensuring only `ValueError` is raised on failure (Depends on T008, T011 completion). **Note**: Moved from Phase 2 to Phase 3 to ensure robustness after fetch implementation.
- [X] T012 [P] [US1] Implement Dirichlet partitioning logic (α ∈ {0.1, 0.5, 1.0}) for FEMNIST in `code/data/partition.py`
- [X] T013 [US1] Implement client partition metadata generation and save to `data/partitions/`. **Scope**: FEMNIST only. Use file naming convention `partition_{dataset}_{seed}_{alpha}.json` with schema: `{client_id, label_distribution, total_samples}` in `code/data/partition.py`.
- [X] T014 [US1] Add validation to exclude clients with zero samples for specific classes in critical heterogeneity scenarios (α=0.1) in `code/data/partition.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - DP-FL Training and Convergence Measurement (Priority: P2)

**Goal**: Train models using FedAvg with Opacus-enabled DP across varying ε and α, logging global and per-client accuracy.

**Independent Test**: Run a single training job (FEMNIST, α=0.1, ε=0.5); verify training completes, privacy budget tracked via moments accountant, and metrics logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Integration test for DP training loop ensuring noise application and budget tracking in `tests/integration/test_training_loop.py`
- [X] T016 [P] [US2] Test for handling clients with zero gradient updates (skipping) without crashing in `tests/integration/test_training_loop.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement Opacus Gaussian noise wrapper and moments accountant configuration in `code/training/dp_utils.py`
- [X] T018 [P] [US2] Implement FedAvg orchestrator supporting ε ∈ {0.1, 0.5, 1.0, 5.0, 10.0} in `code/training/fedavg.py` <!-- FAILED: unspecified -->
- [ ] T018b [US2] Implement the 5-seed orchestration loop mandated by FR-004. This script/CLI must iterate through seeds and configurations, calling T018, and aggregate logs. **Dependency**: Depends on T018. **Completion**: Produces `results/raw_logs.csv` with 5 seeds per config.
- [X] T019 [US2] Implement per-client accuracy logging and aggregation logic. **Scope**: FEMNIST only. MUST explicitly identify "minority" clients based on label frequency in partition metadata (e.g., clients with <5% of total class samples) and log separate metrics for majority vs. minority in `code/training/fedavg.py`.
- [X] T019b [US2] Implement runtime logic in the training loop to skip gradient updates for clients with zero samples for a target class, logging a warning as specified in Edge Cases, in `code/training/fedavg.py`.
- [X] T020 [US2] Implement timeout handling and early stopping logic (flag `is_time_limited`) in `code/training/fedavg.py`
- [X] T021 [US2] Implement "utility collapse" detection for extremely low ε (e.g., ε=0.01) in `code/training/fedavg.py`. **Note**: This flags the result; T035 will filter it from analysis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Threshold Sensitivity (Priority: P3)

**Goal**: Perform statistical tests (t-tests, Mann-Whitney U) and sensitivity analysis on α to validate the "critical heterogeneity" hypothesis.

**Independent Test**: Feed CSV results from US-2 into analysis script; verify p-values are calculated and sensitivity plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test for t-test calculation logic on synthetic accuracy data in `tests/unit/test_stats.py`
- [X] T023 [P] [US3] Test for sensitivity analysis plot generation in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [X] T027a [US3] Implement metric calculation for "rounds to reach target" accuracy. MUST include a `filter_time_limited(df)` function that returns a DataFrame excluding rows where `is_time_limited` is True, and apply this filter before calculating SC-001 metrics in `code/analysis/stats.py`.
- [ ] T035 [US3] Filter utility collapse results from the dataset. **Prerequisites**: Depends on T021 (Detection) and T027a (Time Filter). Input: Raw logs. Logic: Exclude rows where `is_utility_collapse` is True. Output: `results/filtered_data.csv`. **Constraint**: This filtered dataset is the ONLY input for T024a, T024b, T025, and T028.
- [X] T024a [US3] Implement paired t-tests on the accuracy difference (DP accuracy minus Non-DP accuracy) per seed as strictly required by FR-005. Input: Filtered data from T027a and T035. Output: p-values for DP vs Non-DP comparison in `code/analysis/stats.py`.
- [X] T024b [US3] Implement unpaired t-tests (or Mann-Whitney U) comparing majority vs. minority client accuracies for each configuration as required by FR-005. Input: Filtered data from T027a and T035. MUST include fallback logic: if valid runs < 3, switch to Mann-Whitney U and flag results as `power_reduced`. in `code/analysis/stats.py`.
- [X] T025 [US3] Implement sensitivity analysis sweep for α ∈ {0.05, 0.1, 0.5, 1.0} (Depends on T027a, T035 filtered data) in `code/analysis/stats.py`
- [ ] T026 [US3] Implement plotting module for accuracy gap vs. α, accuracy vs. ε curves, AND **specifically generate an overlay plot showing minority-client degradation curves against global accuracy curves** as mandated by Constitution Principle VII (Depends on T025 results). **Output**: `results/plots/` directory. **Format**: PNG. **Resolution**: 300 DPI.
- [X] T028 [US3] Generate final results summary CSV and validation report. **Prerequisites**: MUST execute T027a, T035, T024a, T024b, T025, and T026 successfully before running this task. **Traceability**: [FR-005] [SC-002]. Create `results/summary.csv` with columns: `seed`, `alpha`, `epsilon`, `global_accuracy`, `minority_accuracy`, `majority_accuracy`, `rounds_to_target`, `is_time_limited`, `p_value_dp_vs_nondp` (list of individual p-values per seed from T024a), `p_value_majority_vs_minority`. **Constraint**: The generation loop MUST exclude any data for the Shakespeare dataset (FEMNIST only). **Input**: Must read from the filtered dataset produced by T035. Create `results/validation_report.md` including count of excluded `is_time_limited` runs and `is_utility_collapse` runs in `code/analysis/stats.py`.
- [X] T035b [US3] Additional validation for statistical power: Ensure Mann-Whitney U fallback is correctly flagged in `results/validation_report.md` if power is reduced. (Note: Renamed from duplicate T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `docs/`. **Requirement**: Update 'Installation', 'Usage', and 'Results' sections in `README.md` with new CLI arguments and expected outputs. **Note**: Explicitly state Shakespeare is excluded per plan.md.
- [ ] T031 [P] Implement dynamic batch sizing in `code/training/fedavg.py` that reduces batch size by [deferred] (floor to next power of 2), with a hard minimum of 16, if OOM occurs.
- [ ] T032 [P] Additional unit tests for edge cases (missing classes, timeout triggers) in `tests/unit/`
- [ ] T033 [P] Run quickstart.md validation to ensure end-to-end reproducibility

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
 - *Note: Must complete T011 (Download) before T012 (Partition) within this phase.*
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T012 (Partitions) to load data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018b (Training logs) to analyze results
 - *Critical: T027a (Filtering) and T035 (Utility Filter) MUST precede T024a/T024b (Stats) and T025 (Sensitivity).*

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Dirichlet partitioning logic in tests/unit/test_partition.py"
Task: "Reproducibility test ensuring identical partitions in tests/unit/test_partition.py"

# Launch data tasks for User Story 1 together (sequential logic, parallel code structure):
Task: "Implement FEMNIST downloader in code/data/download.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Download + Partition for FEMNIST)
4. **STOP and VALIDATE**: Test partitioning logic and reproducibility independently
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Training) - *Can start once T012 is done*
 - Developer C: User Story 3 (Analysis) - *Can start once T018b is done*
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
- **Critical**: T008 MUST implement retry logic (3 attempts, exponential backoff) before failing loudly; no synthetic data fallback allowed.
- **Critical**: T027a MUST filter out `is_time_limited` runs for SC-001 analysis.
- **Critical**: T035 MUST filter `is_utility_collapse` runs.
- **Critical**: T024a and T024b MUST implement the specific paired and unpaired tests as mandated by FR-005.
- **Critical**: T026 MUST generate the overlay plot of minority vs global accuracy curves (PNG, 300 DPI).
- **Critical**: T019 MUST explicitly define minority client logic based on label frequency.
- **Critical**: T019b MUST implement the "skip and log" logic for zero-sample clients.
- **Critical**: T011 MUST generate `data/raw/femnist.parquet` and `.sha256` before completion.
- **Critical**: T028 MUST execute T027a, T035, T024a, T024b, T025, T026 before generating summary CSV.
- **Critical**: T028 MUST list individual p-values per seed (no averaging).
- **Critical**: T001 MUST generate `tree_output.txt` for verification.
- **Critical**: T003 MUST include `black`, `ruff`, `pre-commit-hooks`.
- **Critical**: T029 MUST update 'Installation', 'Usage', 'Results' sections.
- **Critical**: T011b, T012b removed per plan.md exclusion of Shakespeare.
- **Critical**: T031 MUST enforce minimum batch size of 16.
- **Critical**: T006 MUST raise ValueError for Shakespeare with reference to plan.md.