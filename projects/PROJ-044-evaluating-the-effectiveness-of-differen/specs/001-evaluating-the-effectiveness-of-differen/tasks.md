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

- [ ] T000 [P] **Spec Alignment Task**: Update `spec.md` to remove references to the Shakespeare dataset as a **SUPPORTED** dataset, aligning the specification with the plan.md Gap Analysis which excludes Shakespeare due to lack of verified sources. **Action**: Edit `specs/001-evaluating-dp-federated-learning/spec.md` to remove FR-001's mention of Shakespeare as a supported dataset, US-1 Scenario 2, and any other Shakespeare-specific requirements. **CRITICAL**: You MUST retain the exclusion constraint and the `ValueError` message requirement ("Shakespeare excluded per plan.md Gap Analysis") in the spec. Do NOT remove the error handling logic. **Verification**: Create and run `scripts/verify_spec_exclusion.py`. This script must: 1) Parse `spec.md`, 2) Find all occurrences of the word "Shakespeare", 3) For each occurrence, verify it appears ONLY in an exclusion context (e.g., "excluded", "not supported", "ValueError", "Gap Analysis", "error"). 4) Exit with code 0 if all occurrences are exclusionary, and code 1 if any occurrence implies support or is ambiguous. **Completion Criterion**: `spec.md` contains no references to "Shakespeare" as a supported dataset. The exclusion logic and error message requirement MUST remain. **Authority**: This task is the authority for the exclusion of Shakespeare in all subsequent tasks.
- [X] T001 [P] Create project structure and verification script. **Action**: Create `scripts/init_project.sh` that executes `mkdir -p code/data code/training code/analysis code/models tests/unit tests/integration data/raw data/partitions results artifacts` in `projects/PROJ-044-evaluating-the-effectiveness-of-differen/`, then runs `tree` and redirects output to `tree_output.txt`. **Completion Criterion**: `scripts/init_project.sh` exists, is executable, and running it produces `tree_output.txt` with the correct directory tree.
- [X] T002 [P] Initialize Python 3.10+ project with PyTorch, Opacus, Hugging Face datasets, pandas, scipy, numpy, matplotlib, statsmodels, pyarrow in `requirements.txt` containing pinned versions
- [ ] T003 [P] Configure linting (black, ruff) and formatting tools in `.pre-commit-config.yaml`. **Requirement**: Must include hooks for `black`, `ruff`, and `pre-commit-hooks`. **Configuration Example**:
 ```yaml
 repos:
 - repo: https://github.com/psf/black
   rev: 23.12.1
   hooks:
   - id: black
     args: [--line-length=88]
 - repo: https://github.com/astral-sh/ruff-pre-commit
   rev: v0.1.9
   hooks:
   - id: ruff
     args: [--fix, --exit-non-zero-on-fix]
 ```
 **Completion Criterion**: `.pre-commit-config.yaml` exists, is valid YAML, and `pre-commit run --all-files` executes without syntax errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement data checksumming and verification utility in `code/data/checksum_utils.py`
- [X] T005 [P] Setup experiment logging infrastructure (CSV + JSON) in `code/training/logging.py`
- [X] T006 [P] Create base configuration management for seeds, α, ε values and dataset name in `code/config.py` defining a `Config` dataclass with fields: `seed: int`, `alpha: float`, `epsilon: float`, `dataset: str` (valid values: "femnist" only; "shakespeare" must raise ValueError with message: "Shakespeare excluded per plan.md Gap Analysis (no verified source)." This error message is a code artifact required by T000's exclusion constraint.)
- [X] T007 Create base model entity (Small CNN/MLP) for FEMNIST in `code/models/cnn.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Heterogeneity Simulation (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible client data partitions from FEMNIST using Dirichlet distributions with varying α to establish a controlled baseline. (Shakespeare excluded per T000 Spec Alignment and plan.md Gap Analysis).

**Independent Test**: Run partitioning script with specific seeds and α values; verify label distributions match theoretical expectations (high variance for α=0.1, balanced for α=1.0) without training.

**Sequential Logic**: T011 (Download) MUST complete before T012 (Partition) and T013 (Metadata). T012 and T013 cannot run in parallel with T011.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T009 and T010 are written *before* T012 implementation (parallel to T012 coding) but must be executed *after* T012 logic is available. They test the logic, not the full pipeline.

- [X] T009 [P] [US1] Unit test for Dirichlet partitioning logic verifying label distribution variance in `tests/unit/test_partition.py`
- [X] T010 [P] [US1] Reproducibility test ensuring identical partitions with same seed in `tests/unit/test_partition.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement FEMNIST data downloader using Hugging Face `datasets` (Verified Source: `leaf/femnist` per plan.md) in `code/data/download.py`. **Action**: Implement streaming download for FEMNIST to handle large datasets within CI time limits. Use `datasets.load_dataset(..., streaming=True)` to iterate over the dataset. **Materialization Logic**: Accumulate rows into a list or use `pyarrow.Table.from_pylist` in chunks, then write to `data/raw/femnist.parquet` using `pyarrow.parquet.ParquetWriter` after the stream ends. **Configuration**: Use `split='train'`, `trust_remote_code=True`. **Completion Criterion**: The task is only complete when `data/raw/femnist.parquet` and `data/raw/femnist.sha256` exist on disk. No synthetic fallback allowed. If dataset != "femnist", raise ValueError. **Failure Handling**: If retries are exhausted, exit with code 1 and error message "Failed to download FEMNIST after 3 attempts". **Execution Command**: `python code/data/download.py --dataset femnist`. **Constraint**: Explicitly reference T000 (Spec Alignment) and plan.md Gap Analysis as the authority for excluding Shakespeare. Add a flag `is_streaming` to the metadata if streaming was used. **Dependencies**: None.
- [X] T012 [US1] Implement Dirichlet partitioning logic (α ∈ {low, moderate, high}) for FEMNIST in `code/data/partition.py`. **Dependency**: T011. **Constraint**: Explicitly reference the exclusion logic defined in T000 (the updated spec) as the authority for excluding Shakespeare.
- [ ] T013 [US1] Implement client partition metadata generation and save to `data/partitions/`. **Dependency**: T011. **Scope**: FEMNIST only. **Output Format**: File naming pattern `partition_femnist_{seed}_{alpha}.json`. **Schema**: JSON object with keys: `client_id` (string), `label_distribution` (dict of class_id: count), `total_samples` (int). **Constraint**: Explicitly reference the exclusion logic defined in T000 (the updated spec) as the authority for excluding Shakespeare.
- [X] T014 [US1] Add validation to exclude clients with zero samples for specific classes in critical heterogeneity scenarios (α=0.1) in `code/data/partition.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - DP-FL Training and Convergence Measurement (Priority: P2)

**Goal**: Train models using FedAvg with Opacus-enabled DP across varying ε and α, logging global and per-client accuracy.

**Independent Test**: Run a single training job (FEMNIST, α=0.1, ε=0.5); verify training completes, privacy budget tracked via moments accountant, and metrics logged.

**Sequential Logic**: 
1. T018a (Core FedAvg) must be implemented first.
2. T018b (DP Integration) and T018d (Non-DP Baseline) depend on T018a. T018b and T018d can be implemented in parallel.
3. T018c-1 (Pilot) depends on the *implementation* of T018b and T018d to measure runtime.
4. T018c-2 (Orchestration) depends on T018c-1 (budget calculation) and the *implementation* of T018b/T018d. It is the driver that calls the implemented logic.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Integration test for DP training loop ensuring noise application and budget tracking in `tests/integration/test_training_loop.py`
- [X] T016 [P] [US2] Test for handling clients with zero gradient updates (skipping) without crashing in `tests/integration/test_training_loop.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement Opacus Gaussian noise wrapper and moments accountant configuration in `code/training/dp_utils.py`
- [X] T018a [P] [US2] Implement Core FedAvg orchestrator (client selection, gradient aggregation) in `code/training/fedavg.py`. **Completion**: Core loop without DP noise.
- [X] T018b [P] [US2] Integrate Opacus DP noise wrapper and moments accountant into FedAvg loop in `code/training/fedavg.py`. **Dependency**: T018a. **Completion**: Orchestrates DP noise application for a range of privacy budgets (ε).
- [ ] T018c-1 [US2] **Pilot Run & Budget Calculation**: Execute a pilot training run (1 seed, 1 config: ε=1.0, α=0.1) to measure `time_per_round`. **Action**: Run the training loop for a sufficient number of rounds. Measure total time. Calculate `time_per_round = total_time / 10`. **Formula**: Calculate `max_rounds = floor(300 seconds / time_per_round)`. **Configuration Space**: The full experiment consists of 5 seeds × 5 ε values (0.01, 0.1, 0.5, 1.0, ∞) × 4 α values (0.05, 0.1, 0.5, 1.0) = 100 runs. **Output**: Save `max_rounds` to `results/budget_config.json`. **Constraint**: This task MUST define `num_configs` as 20 (5 ε × 4 α) to ensure the 6-hour budget (21600s) is respected: `total_time = 5 seeds * 20 configs * max_rounds * time_per_round`. **Fallback Algorithm**: If `total_time > 21600s`, the task MUST reduce `num_configs` by dropping the lowest priority α values (e.g., drop α=0.05 first) until the budget fits. **CRITICAL**: The task must NOT reduce the number of seeds (must remain 5 per FR-004). If reducing all α values still exceeds the budget, abort with `CONFIGURATION_ERROR`. **Completion**: Produces `results/budget_config.json` with a deterministic `max_rounds` and the final list of `active_configs` (α values to run).
- [ ] T018c-2 [US2] Implement the 5-seed orchestration loop mandated by FR-004. **Dependency**: T018c-1, T018b, T018d. This script/CLI must iterate through 5 seeds and the `active_configs` determined in T018c-1, calling T018b (DP) and T018d (Non-DP), using the `max_rounds` calculated in T018c-1. **Constraint**: Must respect the plan.md 6-hour CPU budget. If the budget is strictly exceeded even with reduced configurations, the task must abort and log a `constraint_violation` flag. **Completion**: Produces `results/raw_logs.csv` with Multiple seeds per config (DP and Non-DP).
- [ ] T018d [P] [US2] Implement Non-DP Baseline Training Loop (ε=∞) for paired t-test requirements in `code/training/fedavg.py`. **Dependency**: T018a. **Action**: Run the same FedAvg loop as T018b but without DP noise. **Output**: Logs identical to T018b but with `epsilon=inf` and `is_dp=False`. **Completion**: Produces `results/raw_logs.csv` entries for non-DP runs corresponding to every DP run seed.
- [X] T019 [US2] Implement per-client accuracy logging and aggregation logic. **Scope**: FEMNIST only. MUST explicitly identify "minority" clients based on label frequency in partition metadata (e.g., clients with <5% of total class samples) and log separate metrics for majority vs. minority in `code/training/fedavg.py`.
- [X] T019b [US2] Implement runtime logic in the training loop to skip gradient updates for clients with zero samples for a target class, logging a warning as specified in Edge Cases, in `code/training/fedavg.py`.
- [X] T020 [US2] Implement timeout handling and early stopping logic (flag `is_time_limited`) in `code/training/fedavg.py`
- [X] T021 [US2] Implement "utility collapse" detection for extremely low ε (e.g., ε=0.01) in `code/training/fedavg.py`. **Note**: This flags the result; T035 will filter it from analysis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Threshold Sensitivity (Priority: P3)

**Goal**: Perform statistical tests (t-tests, Mann-Whitney U) and sensitivity analysis on α to validate the "critical heterogeneity" hypothesis.

**Independent Test**: Feed CSV results from US-2 into analysis script; verify p-values are calculated and sensitivity plots are generated.

**Sequential Logic**: T027a and T035 must complete before T024a, T024b, T025. T025 must complete before T026. T028-1, T028-2, T028-3 depend on all previous analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test for t-test calculation logic on synthetic accuracy data in `tests/unit/test_stats.py`
- [X] T023 [P] [US3] Test for sensitivity analysis plot generation in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [X] T027a [US3] Implement metric calculation for "rounds to reach target" accuracy. MUST include a `filter_time_limited(df)` function that returns a DataFrame excluding rows where `is_time_limited` is True, and apply this filter before calculating SC-001 metrics in `code/analysis/stats.py`. **Output**: `results/filtered_time.csv`.
- [ ] T035 [US3] Filter utility collapse results from the dataset. **Prerequisites**: Depends on T027a (Time Filter). Input: `results/filtered_time.csv`. **Logic**: Implement a dynamic detection mechanism for "utility collapse" as per FR-006. Exclude rows where `epsilon < 0.05` OR where `accuracy < 1.0/62` (1 divided by FEMNIST classes). **Output**: `results/filtered_data.csv`. **Constraint**: This filtered dataset is the ONLY input for T024a, T024b, T025, and T028. **Validation**: If Mann-Whitney U fallback is triggered in T024b, flag results as `power_reduced` in the final report.
- [X] T024a [US3] Implement **paired t-tests** on the accuracy difference (DP accuracy minus Non-DP accuracy) per seed as strictly required by FR-005 and Constitution Principle VII. **Dependency**: T027a, T035. **Requirement**: Requires a corresponding non-DP run (ε=∞ or no noise) for the *exact same* seed and configuration (α, dataset) to perform the pairing. If the non-DP run is missing for a specific seed (e.g., due to plan budget constraints), that seed MUST be excluded from the paired test and the result for that configuration flagged as `power_reduced` in the output. **Note**: If the plan's 3-seed budget prevents generating 5 non-DP pairs, the task will exclude missing pairs and flag `power_reduced` as a direct consequence of the plan budget, not a task error. Output: p-values for DP vs Non-DP comparison in `code/analysis/stats.py`.
- [X] T024b [US3] Implement unpaired t-tests (or Mann-Whitney U) comparing majority vs. minority client accuracies for each configuration as required by FR-005. **Dependency**: T027a, T035. Input: Filtered data. **Definition**: "Valid runs" = rows in the filtered CSV where accuracy is not null. **Fallback**: If valid runs < 3, the task MUST ABORT with a `CONFIGURATION_ERROR` flag. DO NOT fallback to Mann-Whitney U. **Constitution Exception**: This abort is an explicit enforcement of Constitution Principle VII (Statistical Rigor). The project design (Plan.md seed budget vs Spec seed requirement) must be corrected to avoid this abort. Flag results as `statistically_invalid` if aborted. in `code/analysis/stats.py`.
- [X] T025 [US3] Implement sensitivity analysis sweep for α across a range of representative values (Depends on T027a, T035 filtered data) in `code/analysis/stats.py`. **Output**: Calculate slope ratios for accuracy vs. ε curves for α=0.1 and α=1.0 as part of the sensitivity analysis.
- [ ] T026 [US3] Implement plotting module for accuracy gap vs. α, accuracy vs. ε curves, AND **specifically generate an overlay plot showing minority-client degradation curves against global accuracy curves** as mandated by Constitution Principle VII. **Dependency**: T025 results. **Metric Definition**: Y-axis = Accuracy Gap = Global_Acc - Minority_Acc. **Output**: `results/plots/minority_vs_global_overlay.png`. **Format**: PNG. **Resolution**: Standard DPI (no specific metadata requirement). **Validation**: Ensure the plot is generated correctly. **Note**: Removed 300 DPI metadata validation requirement as it is not in the plan.
- [ ] T028-1 [US3] Generate final results summary CSV. **Dependency**: T027a, T035, T024a, T024b, T025, T026. **Action**: Consolidate all filtered results into a single DataFrame, calculate variance of accuracy metrics across 5 seeds (for SC-005) per configuration. **Output**: Create `results/summary.csv` with columns: `seed`, `alpha`, `epsilon`, `global_accuracy`, `minority_accuracy`, `majority_accuracy`, `rounds_to_target`, `is_time_limited`, `accuracy_variance` (float), `p_value_dp_vs_nondp` (scalar, average of p-values from T024a), `p_value_majority_vs_minority`. **Constraint**: The generation loop MUST exclude any data for the Shakespeare dataset (FEMNIST only). **Input**: Must read from the filtered dataset produced by T035.
- [ ] T028-2 [US3] Generate validation report. **Dependency**: T028-1. **Action**: Create `results/validation_report.md` including count of excluded `is_time_limited` runs, `is_utility_collapse` runs, and `power_reduced` flags in `code/analysis/stats.py`.
- [ ] T028-3 [US3] Export P-Values JSON. **Dependency**: T028-1. **Action**: Store individual p-values per seed in a separate JSON file `results/p_values_by_seed.json` for traceability, as the spec's Data Model defines `p_value_dp_vs_nondp` as a scalar.

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
 - *Note: Must complete T011 (Download) before T012 (Partition) within this phase. T011, T012, T013 are NOT parallel with each other.*
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T012 (Partitions) to load data
 - *Note: T018c-1 -> T018c-2 is a strict serial chain. T018c-2 depends on T018b/T018d implementations. T018b -> T018a. T018d -> T018a. T018b and T018d can be implemented in parallel.*
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018c-2 (Training logs) to analyze results
 - *Critical: T027a (Filtering) and T035 (Utility Filter) MUST precede T024a/T024b (Stats) and T025 (Sensitivity). T025 must precede T026. T028-1/2/3 depend on all previous.*

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T000, T001, T002, T003)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Important**: T011, T012, T013 are NOT parallel with each other.
- **Important**: T018c-1, T018c-2, T018b, T018d are NOT parallel with each other (except T018b/T018d parallel to each other).
- **Important**: T024a, T024b, T025, T026, T028-1/2/3 are NOT parallel with T027a/T035.

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
 - Developer C: User Story 3 (Analysis) - *Can start once T018c-2 is done*
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
- **Critical**: T000 MUST amend `spec.md` to remove Shakespeare as a *supported* dataset and verify via script, while preserving exclusion/error message.
- **Critical**: T001 MUST generate `tree_output.txt` via `scripts/init_project.sh`.
- **Critical**: T003 MUST include `black`, `ruff`, `pre-commit-hooks` with specific config.
- **Critical**: T029 MUST update 'Installation', 'Usage', 'Results' sections.
- **Critical**: T011 MUST use streaming download for FEMNIST and materialize to `data/raw/femnist.parquet` using `pyarrow` chunks, and fail loudly on retry exhaustion.
- **Critical**: T028-1/2/3 MUST execute T027a, T035, T024a, T024b, T025, T026 before generating summary CSV.
- **Critical**: T028-1 MUST output `p_value_dp_vs_nondp` as a scalar and T028-3 MUST store individual p-values in JSON.
- **Critical**: T011b, T012b removed per plan.md exclusion of Shakespeare.
- **Critical**: T031 MUST enforce minimum batch size of 16 and reduce by half.
- **Critical**: T026 MUST generate the overlay plot of minority vs global accuracy curves (PNG, standard DPI).
- **Critical**: T019 MUST explicitly define minority client logic based on label frequency.
- **Critical**: T019b MUST implement the "skip and log" logic for zero-sample clients.
- **Critical**: T024a MUST implement **paired** t-tests for DP vs Non-DP and handle missing non-DP runs by excluding the seed and flagging `power_reduced`.
- **Critical**: T024b MUST define 'valid runs' and ABORT if < 3 (no fallback), flagging `statistically_invalid`.
- **Critical**: T013 MUST output `partition_femnist_{seed}_{alpha}.json` with specific schema.
- **Critical**: T028-1 MUST use scalar p-value format and T028-3 separate JSON file.
- **Critical**: T008 removed; logic merged into T011.
- **Critical**: T035 depends on T027a; no circular dependency.
- **Critical**: T028-1/2/3 depend on data from T024/T025/T026, not on T028a/b (aggregation).
- **Critical**: T036 removed; logic merged into T025/T026.
- **Critical**: T012/T013 are NOT parallel with T011.
- **Critical**: T018c-1/T018c-2 are NOT parallel with T018a/T018b/T018d.
- **Critical**: T024a, T024b, T025, T026, T028-1/2/3 are NOT parallel with T027a/T035.
- **Critical**: T018c-1 MUST define `num_configs` as 20 and use `max_rounds = floor(300s / time_per_round)` formula.
- **Critical**: T018c-1 MUST drop configurations (α values) to fit budget, NOT seeds.
- **Critical**: T035 MUST use `1.0/62` as the random guessing threshold.
- **Critical**: T000 MUST allow exclusion/error message references to "Shakespeare".
- **Critical**: T018d MUST generate non-DP baselines for T024a.
- **Critical**: T018a, T018b, T018c-1, T018c-2, T018d are NOT parallel with each other (except T018d parallel to T018b).
- **Critical**: T024a, T024b, T025, T026, T028-1/2/3 are NOT parallel with T027a/T035.