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

**Purpose**: Project initialization, spec alignment, and basic structure

- [ ] T000 [P] **Spec Alignment Task**: Update `spec.md` to remove all references to the Shakespeare dataset and US-1 Scenario 2, aligning the specification with the plan.md Gap Analysis which excludes Shakespeare due to lack of verified sources. **Action**: Edit `specs/001-evaluating-dp-federated-learning/spec.md` to remove FR-001's mention of Shakespeare, US-1 Scenario 2, and any other Shakespeare-specific requirements. **Completion Criterion**: `spec.md` contains no references to "Shakespeare" and FR-001 explicitly lists only "FEMNIST". **Verification**: Run `grep -r Shakespeare specs/001-evaluating-dp-federated-learning/spec.md`; exit code must be 1. **Authority**: This task is the authority for the exclusion of Shakespeare in all subsequent tasks.
- [X] T001 [P] Create project structure and verification script. **Action**: Create `scripts/init_project.sh` that executes `mkdir -p code/data code/training code/analysis code/models tests/unit tests/integration data/raw data/partitions results artifacts` in `projects/PROJ-044-evaluating-the-effectiveness-of-differen/`, then runs `tree` and redirects output to `tree_output.txt`. **Completion Criterion**: `scripts/init_project.sh` exists, is executable, and running it produces `tree_output.txt` with the correct directory tree.
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

**Goal**: Generate reproducible client data partitions from FEMNIST using Dirichlet distributions with varying α to establish a controlled baseline. (Shakespeare excluded per T000 Spec Alignment and plan.md Gap Analysis).

**Independent Test**: Run partitioning script with specific seeds and α values; verify label distributions match theoretical expectations (high variance for α=0.1, balanced for α=1.0) without training.

**Sequential Logic**: T011 (Download) MUST complete before T012 (Partition) and T013 (Metadata). T012 and T013 cannot run in parallel with T011.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for Dirichlet partitioning logic verifying label distribution variance in `tests/unit/test_partition.py`
- [X] T010 [P] [US1] Reproducibility test ensuring identical partitions with same seed in `tests/unit/test_partition.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement FEMNIST data downloader using Hugging Face `datasets` (Verified Source: `leaf/femnist` per plan.md) in `code/data/download.py`. **Action**: Implement retry logic with a configurable number of attempts and exponential backoff. **Configuration**: Use `split='train'`, `trust_remote_code=True`. **Completion Criterion**: The task is only complete when `data/raw/femnist.parquet` and `data/raw/femnist.sha256` exist on disk. Save downloaded data to `data/raw/femnist.parquet` and generate `data/raw/femnist.sha256`. No synthetic fallback allowed. If dataset != "femnist", raise ValueError. **Failure Handling**: If retries are exhausted, exit with code 1 and error message "Failed to download FEMNIST after 3 attempts". **Execution Command**: `python code/data/download.py --dataset femnist`. **Constraint**: Explicitly reference T000 (Spec Alignment) and plan.md Gap Analysis as the authority for excluding Shakespeare.
- [X] T012 [P] [US1] Implement Dirichlet partitioning logic (α ∈ {, 0.5, 1.0}) for FEMNIST in `code/data/partition.py`. **Dependency**: T011. **Constraint**: Explicitly reference T000 (Spec Alignment) and plan.md Gap Analysis as the authority for excluding Shakespeare.
- [ ] T013 [US1] Implement client partition metadata generation and save to `data/partitions/`. **Dependency**: T011. **Scope**: FEMNIST only. **Output Format**: File naming pattern `partition_femnist_{seed}_{alpha}.json`. **Schema**: JSON object with keys: `client_id` (string), `label_distribution` (dict of class_id: count), `total_samples` (int). **Constraint**: Explicitly reference T000 (Spec Alignment) and plan.md Gap Analysis as the authority for excluding Shakespeare.
- [X] T014 [US1] Add validation to exclude clients with zero samples for specific classes in critical heterogeneity scenarios (α=0.1) in `code/data/partition.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - DP-FL Training and Convergence Measurement (Priority: P2)

**Goal**: Train models using FedAvg with Opacus-enabled DP across varying ε and α, logging global and per-client accuracy.

**Independent Test**: Run a single training job (FEMNIST, α=0.1, ε=0.5); verify training completes, privacy budget tracked via moments accountant, and metrics logged.

**Sequential Logic**: T018a (Core) must complete before T018b (DP) and T018c (Orchestration).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Integration test for DP training loop ensuring noise application and budget tracking in `tests/integration/test_training_loop.py`
- [X] T016 [P] [US2] Test for handling clients with zero gradient updates (skipping) without crashing in `tests/integration/test_training_loop.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement Opacus Gaussian noise wrapper and moments accountant configuration in `code/training/dp_utils.py`
- [ ] T018a [P] [US2] Implement Core FedAvg orchestrator (client selection, gradient aggregation) in `code/training/fedavg.py`. **Completion**: Core loop without DP noise.
- [ ] T018b [P] [US2] Integrate Opacus DP noise wrapper and moments accountant into FedAvg loop in `code/training/fedavg.py`. **Dependency**: T018a. **Completion**: Orchestrates DP noise application for a range of privacy budgets (ε).
- [ ] T018c [US2] Implement the 5-seed orchestration loop mandated by FR-004. **Dependency**: T018b. This script/CLI must iterate through seeds and configurations, calling T018b, and aggregate logs. **Completion**: Produces `results/raw_logs.csv` with 5 seeds per config.
- [X] T019 [US2] Implement per-client accuracy logging and aggregation logic. **Scope**: FEMNIST only. MUST explicitly identify "minority" clients based on label frequency in partition metadata (e.g., clients with <5% of total class samples) and log separate metrics for majority vs. minority in `code/training/fedavg.py`.
- [X] T019b [US2] Implement runtime logic in the training loop to skip gradient updates for clients with zero samples for a target class, logging a warning as specified in Edge Cases, in `code/training/fedavg.py`.
- [X] T020 [US2] Implement timeout handling and early stopping logic (flag `is_time_limited`) in `code/training/fedavg.py`
- [X] T021 [US2] Implement "utility collapse" detection for extremely low ε (e.g., ε=0.01) in `code/training/fedavg.py`. **Note**: This flags the result; T035 will filter it from analysis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Threshold Sensitivity (Priority: P3)

**Goal**: Perform statistical tests (t-tests, Mann-Whitney U) and sensitivity analysis on α to validate the "critical heterogeneity" hypothesis.

**Independent Test**: Feed CSV results from US-2 into analysis script; verify p-values are calculated and sensitivity plots are generated.

**Sequential Logic**: T027a and T035 must complete before T024a, T024b, T025. T026 must complete before T028c.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test for t-test calculation logic on synthetic accuracy data in `tests/unit/test_stats.py`
- [X] T023 [P] [US3] Test for sensitivity analysis plot generation in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [X] T027a [US3] Implement metric calculation for "rounds to reach target" accuracy. MUST include a `filter_time_limited(df)` function that returns a DataFrame excluding rows where `is_time_limited` is True, and apply this filter before calculating SC-001 metrics in `code/analysis/stats.py`. **Output**: `results/filtered_time.csv`.
- [X] T035 [US3] Filter utility collapse results from the dataset. **Prerequisites**: Depends on T027a (Time Filter). Input: `results/filtered_time.csv`. Logic: Exclude rows where `is_utility_collapse` is True (defined as `accuracy < 0.05` OR `epsilon < 0.05`). Output: `results/filtered_data.csv`. **Constraint**: This filtered dataset is the ONLY input for T024a, T024b, T025, and T028. **Validation**: If Mann-Whitney U fallback is triggered in T024b, flag results as `power_reduced` in the final report.
- [ ] T024a [US3] Implement **paired t-tests** on the accuracy difference (DP accuracy minus Non-DP accuracy) per seed as strictly required by FR-005 and Constitution Principle VII. **Dependency**: T027a, T035. **Requirement**: Requires a corresponding non-DP run (ε=∞ or no noise) for the *exact same* seed and configuration (α, dataset) to perform the pairing. If the non-DP run is missing for a specific seed, that seed MUST be excluded from the paired test and the result for that configuration flagged as `power_reduced` in the output. Output: p-values for DP vs Non-DP comparison in `code/analysis/stats.py`.
- [ ] T024b [US3] Implement unpaired t-tests (or Mann-Whitney U) comparing majority vs. minority client accuracies for each configuration as required by FR-005. **Dependency**: T027a, T035. Input: Filtered data. **Definition**: "Valid runs" = rows in the filtered CSV where accuracy is not null. **Fallback**: If valid runs < 3, switch to Mann-Whitney U. **Constitution Exception**: This fallback is an explicit exception to Constitution Principle VII (Statistical Rigor) triggered only when seed count is insufficient, and MUST flag results as `power_reduced` in the final report. in `code/analysis/stats.py`.
- [X] T025 [US3] Implement sensitivity analysis sweep for α across a range of representative values (Depends on T027a, T035 filtered data) in `code/analysis/stats.py`
- [ ] T026 [US3] Implement plotting module for accuracy gap vs. α, accuracy vs. ε curves, AND **specifically generate an overlay plot showing minority-client degradation curves against global accuracy curves** as mandated by Constitution Principle VII. **Dependency**: T025 results. **Metric Definition**: Y-axis = Accuracy Gap = Global_Acc - Minority_Acc. **Output**: `results/plots/minority_vs_global_overlay.png`. **Format**: PNG. **Resolution**: 300 DPI. **Validation**: Embed DPI metadata in PNG header and verify via `code/analysis/validate_plot_dpi.py` script (must check PNG header bytes 0x00-0x04 and DPI chunk).
- [ ] T028a [US3] Implement data aggregation and filtering logic for final report. **Dependency**: T027a, T035, T024a, T024b, T025, T026. **Action**: Consolidate all filtered results into a single DataFrame.
- [ ] T028b [US3] Implement statistical column calculation. **Dependency**: T028a. **Action**: Calculate p-values (from T024a, T024b) and **variance of accuracy metrics across 5 seeds** (for SC-005) per configuration.
- [ ] T028c [US3] Generate final results summary CSV and validation report. **Dependency**: T028a, T028b, T026. **Traceability**: [FR-005] [SC-002] [SC-005]. Create `results/summary.csv` with columns: `seed`, `alpha`, `epsilon`, `global_accuracy`, `minority_accuracy`, `majority_accuracy`, `rounds_to_target`, `is_time_limited`, `accuracy_variance` (float), `p_value_dp_vs_nondp` (JSON-encoded string of list of individual p-values per seed from T024a, e.g., `"[0.04, 0.02,...]"`), `p_value_majority_vs_minority`. **Constraint**: The generation loop MUST exclude any data for the Shakespeare dataset (FEMNIST only). **Input**: Must read from the filtered dataset produced by T035. Create `results/validation_report.md` including count of excluded `is_time_limited` runs, `is_utility_collapse` runs, and `power_reduced` flags in `code/analysis/stats.py`.
- [ ] T036 [US3] Implement slope ratio calculation for SC-004. **Dependency**: T025 results. **Action**: Calculate the slope of the accuracy vs. ε curve for α=0.1 and α=1.0. **Validation**: Verify that the slope for α=0.1 is ≥ 2x steeper (more negative) than the slope for α=1.0. **Output**: Report `results/slope_ratio_validation.md` with the calculated slopes and a pass/fail status.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `docs/`. **Requirement**: Update 'Installation', 'Usage', and 'Results' sections in `README.md` with new CLI arguments and expected outputs. **Note**: Explicitly state Shakespeare is excluded per T000 and plan.md.
- [X] T031 [P] Implement dynamic batch sizing in `code/training/fedavg.py` that reduces batch size by half (floor to next power of 2), with a hard minimum of 16, if OOM occurs.
- [ ] T032 [P] Additional unit tests for edge cases (missing classes, timeout triggers) in `tests/unit/`
- [ ] T033 [P] Run quickstart.md validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (T000 and T001 can run in parallel)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - *Note: Must complete T011 (Download) before T012 (Partition) within this phase.*
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T012 (Partitions) to load data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018c (Training logs) to analyze results
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

# Launch data tasks for User Story 1 (Sequential Logic):
# T011 must complete before T012 and T013.
Task: "Implement FEMNIST downloader in code/data/download.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T000, T001)
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
 - Developer C: User Story 3 (Analysis) - *Can start once T018c is done*
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
- **Critical**: T000 MUST amend `spec.md` to remove Shakespeare references and verify via grep.
- **Critical**: T001 MUST generate `tree_output.txt` via `scripts/init_project.sh`.
- **Critical**: T003 MUST include `black`, `ruff`, `pre-commit-hooks`.
- **Critical**: T029 MUST update 'Installation', 'Usage', 'Results' sections.
- **Critical**: T011 MUST generate `data/raw/femnist.parquet` and `.sha256` before completion and fail loudly on retry exhaustion.
- **Critical**: T028c MUST execute T027a, T035, T024a, T024b, T025, T026 before generating summary CSV.
- **Critical**: T028c MUST list individual p-values per seed as a JSON-encoded string and include `accuracy_variance`.
- **Critical**: T011b, T012b removed per plan.md exclusion of Shakespeare.
- **Critical**: T031 MUST enforce minimum batch size of 16 and reduce by half.
- **Critical**: T026 MUST generate the overlay plot of minority vs global accuracy curves (PNG, 300 DPI, with metadata) and a validation script.
- **Critical**: T019 MUST explicitly define minority client logic based on label frequency.
- **Critical**: T019b MUST implement the "skip and log" logic for zero-sample clients.
- **Critical**: T024a MUST implement **paired** t-tests for DP vs Non-DP and handle missing non-DP runs by excluding the seed and flagging `power_reduced`.
- **Critical**: T024b MUST define 'valid runs' and flag `power_reduced` if fallback used (Constitution Exception).
- **Critical**: T013 MUST output `partition_femnist_{seed}_{alpha}.json` with specific schema.
- **Critical**: T028c MUST use JSON string format for p-value list column.
- **Critical**: T008 removed; logic merged into T011.
- **Critical**: T035 depends on T027a; no circular dependency.
- **Critical**: T028c depends on data from T024/T025/T026, not on T028a/b (aggregation).
- **Critical**: T036 MUST calculate and verify the slope ratio for SC-004.
- **Critical**: T012/T013 are NOT parallel with T011.
- **Critical**: T018b/T018c are NOT parallel with T018a.