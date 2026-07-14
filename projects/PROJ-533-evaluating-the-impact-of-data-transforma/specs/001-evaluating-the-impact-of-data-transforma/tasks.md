# Tasks: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Input**: Design documents from `/specs/001-data-transformation-sensitivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure using exact command: `mkdir -p code/utils data/raw data/processed results/type1_error results/power results/aggregated results/checkpoints tests/unit tests/integration` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

- [ ] T002 Initialize Python 3.11 project with dependencies (`scikit-learn`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`) in `requirements.txt`

- [ ] T003 Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `utils/checkpointing.py` to handle state saving/loading for resumption (Constitution Principle V)

- [ ] T005 Implement `utils/statistical_tests.py` with t-test, ANOVA, Shapiro-Wilk, and Friedman test wrappers

- [ ] T006 Implement `utils/transformations.py` with Box-Cox, Yeo-Johnson, and rank-based inverse normal functions (handling positive-value constraints)

- [~] T007 Create `data/datasets.csv` with headers `[dataset_id, source_url, sample_size, continuous_vars, group_labels, excluded_reason]` (Note: Only retained datasets are included; `shapiro_p_value` is logged but not stored in the final CSV per US-1 filtering logic) and `data/checksums.csv` with headers `[dataset_id, sha256_hash]` <!-- ATOMIZE: requested -->

- [~] T008 Create `results/simulation_seeds.txt` to log seeds per run ID (format: `RUN_ID=<id> SEED=42`) ensuring the file is located in `results/` alongside specific simulation outputs to satisfy Constitution VII "alongside results" requirement

- [~] T009 Create `code/utils/logging_config.py` that configures a logger writing to `results/pipeline.log` with specific format to record exclusions, imputation rates, and transformation interventions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Filter Real-World Datasets (Priority: P1) 🎯 MVP

**Goal**: Download at least 50 public datasets from UCI/OpenML, filter for non-normality (Shapiro-Wilk p < 0.05) and sample size (N ≥ 30), and preserve metadata.

**Independent Test**: Execute `code/download_datasets.py` and `code/filter_datasets.py` and verify `data/datasets.csv` contains ≥50 valid entries with SHA-256 checksums in `data/checksums.csv`.

### Tests for User Story 1 (TDD First - Write these BEFORE implementation)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These are atomic tasks, one per test function.

- [~] T010a [US1] Unit test for valid URL validation: Implement `tests/unit/test_download.py::test_valid_url_returns_true_for_valid_url` asserting `is_valid_url("...")` returns True

- [~] T010b [US1] Unit test for invalid URL validation: Implement `tests/unit/test_download.py::test_invalid_url_returns_false` asserting `is_valid_url("not_a_url")` returns False

- [~] T011a [US1] Unit test for Shapiro-Wilk p-value calculation: Implement `tests/unit/test_filter.py::test_shapiro_wilk_p_value_calculation` asserting `shapiro_test([1,2,3,4,5])` returns a p-value object

- [~] T011b [US1] Unit test for Shapiro-Wilk filtering logic (p < 0.05): Implement `tests/unit/test_filter.py::test_filter_keeps_non_normal` asserting a dataset with p=0.01 is kept and p=0.10 is excluded

- [~] T012a [US1] Integration test for full download-and-filter pipeline: Implement `tests/integration/test_pipeline.py::test_full_download_filter_pipeline` asserting that running both scripts produces a valid `data/datasets.csv` with ≥1 entry

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/download_datasets.py` to fetch datasets from UCI/OpenML with explicit URL logging

- [ ] T014 [US1] Append SHA-256 checksum computation to `code/download_datasets.py`, write to `data/checksums.csv`, AND update `state/projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml` artifact_hashes map (FR-010, Constitution III/V). **Dependency**: Must run immediately AFTER T013 (Download) to checksum the raw downloaded data before any filtering or exclusion logic is applied.

- [ ] T015 [US1] Implement missing value imputation (mean/median) and exclusion logic (>10% missing) in `code/filter_datasets.py`

- [ ] T016 [US1] Implement Shapiro-Wilk normality test and sample size filtering (N ≥ 30) in `code/filter_datasets.py` (FR-002). **Dependency**: Must run AFTER T015 (Imputation) to ensure complete data for testing.

- [ ] T017 [US1] Implement metadata extraction (sample size, continuous variables, group labels) and write to `data/datasets.csv` (FR-001). **Dependency**: Must run AFTER T016 (Filtering) to record only retained datasets.

- [ ] T018 [US1] Add checkpointing logic to `code/download_datasets.py` to allow resumption after each dataset

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply Transformations and Run Type I Error Tests (Priority: P2)

**Goal**: Apply Box-Cox, Yeo-Johnson, and rank-based transformations to filtered datasets and estimate Type I error via label shuffling.

**Independent Test**: Run `code/apply_transformations.py` and `code/simulate_null.py` on a single dataset and verify Type I error is estimated via a sufficient number of shuffles with a fixed seed.

### Tests for User Story 2 (TDD First - Write these BEFORE implementation)

- [ ] T019a [US2] Unit test for transformation success/failure handling (log-shift intervention): Implement `tests/unit/test_transformations.py::test_log_shift_applied_on_negative_values` asserting a log-shift is applied and logged when Box-Cox fails on negative data

- [ ] T019b [US2] Unit test for transformation failure logging: Implement `tests/unit/test_transformations.py::test_transformation_failure_logs_reason` asserting a specific error message is written to the log when a transformation fails

- [ ] T020a [US2] Unit test for null simulation label shuffling logic: Implement `tests/unit/test_simulate_null.py::test_label_shuffling_preserves_distribution` asserting that shuffled labels maintain the original group size distribution

- [ ] T020b [US2] Unit test for fixed seed reproducibility: Implement `tests/unit/test_simulate_null.py::test_seed_reproducibility` asserting that two runs with seed=42 produce identical p-value sequences

- [ ] T021a [US2] Integration test for transformation + null simulation on one dataset: Implement `tests/integration/test_type1_error.py::test_type1_error_estimation_single_dataset` asserting the pipeline produces a valid JSON result file

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/apply_transformations.py` to apply Box-Cox (log-shift if needed), Yeo-Johnson, and rank-based inverse normal (FR-003) after raw data file paths are available (T015/T017). **Dependency**: Must have access to raw data file path, not just metadata.

- [ ] T023 [P] [US2] Implement `code/apply_transformations.py` to log interventions (e.g., log-shift applied) and skip failures with reasons

- [ ] T024 [US2] Implement `code/simulate_null.py` to shuffle group labels multiple times with a fixed seed (default 42), compute t-test/ANOVA p-values (FR-004), and record the seed value in `results/simulation_seeds.txt` BEFORE the simulation loop executes (Constitution VII). **Note**: Seed must be logged as a precondition to ensure reproducibility.

- [ ] T025 [P] [US2] Implement `code/simulate_null.py` to record proportion of p < 0.05 as Type I error estimate

- [ ] T026 [P] [US2] Implement checkpointing in `code/simulate_null.py` to save progress per dataset

- [ ] T027 [US2] Write per-dataset Type I error results to `results/type1_error/[dataset_id].json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Simulate Data with Known Ground Truth for Power Analysis (Priority: P4)

**Goal**: Generate simulated datasets with known effect sizes (Cohen's d) and measure statistical power.

**Independent Test**: Run `code/simulate_power.py` with fixed effect sizes and Power estimates will match expected values within 95% CI half-width ±0.02..

### Tests for User Story 4 (TDD First - Write these BEFORE implementation)

- [ ] T028a [US4] Unit test for simulated data generation (non-normal distributions): Implement `tests/unit/test_simulate_power.py::test_non_normal_data_generation` asserting Generated data has skewness > 0.5

- [ ] T028b [US4] Unit test for ground truth label assignment: Implement `tests/unit/test_simulate_power.py::test_ground_truth_labels_assigned` asserting labels match the known effect size group

- [ ] T029a [US4] Unit test for power calculation logic: Implement `tests/unit/test_simulate_power.py::test_power_calculation_proportion` asserting power = count(significant) / total_runs

- [ ] T030a [US4] Integration test for full power simulation pipeline: Implement `tests/integration/test_power_analysis.py::test_full_power_simulation_pipeline` asserting the pipeline produces valid JSON results for all effect sizes

### Implementation for User Story 4

- [ ] T031 [US4] Implement `code/simulate_power.py` to generate multiple simulated datasets per effect size (small, medium, large) with ground truth labels (FR-005, US-4 Acceptance Scenario 1). **Note**: Concrete count of used to satisfy precision targets.

- [ ] T032 [US4] Implement `code/apply_transformations.py` to apply the three transformations to simulated data after T031 writes batch to disk. **Dependency**: T031 (batch complete signal) must be complete. **Note**: Strict sequential ordering required to ensure T032 waits for entire batch write (Addressing ordering-3b06abaf)

- [ ] T033 [US4] Implement `code/simulate_power.py` to run t-test/ANOVA on transformed simulated data and record proportion of p < 0.05 as power (FR-006)

- [ ] T034 [US4] Implement `code/simulate_power.py` to compute bootstrap confidence intervals for power estimates to satisfy US-4 Acceptance Scenario 3 requirement for CI validation (FR-006, US-4)

- [ ] T035 [US4] Write per-simulation power results to `results/power/[effect_size]_[transform]_[test].json`

**Checkpoint**: All user stories (1, 2, 4) should now be independently functional

---

## Phase 6: User Story 3 - Aggregate Results and Generate Reports (Priority: P3)

**Goal**: Aggregate results across all datasets, compute mean Type I error and power with bootstrap CIs, perform Friedman test, and generate visualizations.

**Independent Test**: Execute `code/aggregate_results.py` on pre-computed results and verify summary tables contain mean metrics with CIs and bar plots are generated.

### Tests for User Story 3 (TDD First - Write these BEFORE implementation)

- [ ] T036a [US3] Unit test for aggregation logic (mean/CI calculation): Implement `tests/unit/test_aggregate.py::test_bootstrap_ci_calculation` asserting the function returns a tuple (mean, ci_lower, ci_upper)

- [ ] T036b [US3] Unit test for aggregation logic (mean calculation): Implement `tests/unit/test_aggregate.py::test_mean_calculation` asserting the function returns the correct arithmetic mean

- [ ] T037a [US3] Unit test for Friedman test and post-hoc Bonferroni correction: Implement `tests/unit/test_aggregate.py::test_friedman_test_and_bonferroni` asserting the function returns a p-value and adjusted p-values

- [ ] T038a [US3] Integration test for full aggregation and visualization pipeline: Implement `tests/integration/test_aggregation.py::test_full_aggregation_pipeline` asserting the script produces summary tables and plots

### Implementation for User Story 3

- [ ] T039 [US3] Implement `code/aggregate_results.py` to load all Type I error and power results and compute means per transformation-test combination (FR-007)

- [ ] T040 [P] [US3] Implement `code/aggregate_results.py` to compute bootstrap confidence intervals for aggregated metrics (FR-007)

- [ ] T041 [US3] Implement `code/aggregate_results.py` to perform Friedman test (non-parametric repeated measures ANOVA) on error rates (FR-008)

- [ ] T042 [P] [US3] Implement `code/aggregate_results.py` to perform post-hoc pairwise comparisons with Bonferroni correction (FR-008)

- [ ] T043 [US3] Implement `code/aggregate_results.py` to perform sensitivity analysis sweeping α across a range of small values and generate a trend report showing how false-positive rates vary (FR-008). **Note**: Explicit range and output format defined for verification.

- [ ] T044 [US3] Implement `code/aggregate_results.py` to generate summary tables (CSV/JSON) in `results/aggregated/` (FR-009)

- [ ] T045 [P] [US3] Implement `code/aggregate_results.py` to generate bar plots (matplotlib/seaborn) showing error rates and power by transformation and test type (FR-009)

**Checkpoint**: All user stories should now be independently functional and aggregated

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 Update README.md to include installation instructions, usage examples for code/download_datasets.py, and a description of the results/ directory structure

- [ ] T047 Refactor `code/apply_transformations.py` to use a Strategy pattern by extracting Box-Cox, Yeo-Johnson, and Rank-based logic into separate classes implementing a common Transform interface, reducing cyclomatic complexity in main loop

- [ ] T048 Profile `code/aggregate_results.py` and optimize loop X; record runtime in `results/benchmark.log` to ensure < 6h total runtime

- [ ] T049 Additional unit tests (if requested) in `tests/unit/`

- [ ] T050 Execute all code blocks in quickstart.md and verify they complete without error, logging output to `results/quickstart_validation.log`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P4 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for input data
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of real data, but depends on Foundational utils
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 and US4 completion for aggregation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US4 can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together (after tests are written):
Task: "Implement missing value imputation in code/filter_datasets.py"
Task: "Implement Shapiro-Wilk normality test in code/filter_datasets.py"
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
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Acquisition)
 - Developer B: User Story 2 (Type I Error)
 - Developer C: User Story 4 (Power Analysis)
3. All stories complete, then Developer D/E handles User Story 3 (Aggregation)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Check**: All tasks are CPU-only, no GPU/CUDA required, Memory usage < 6GB, Runtime < 6h. No 8-bit/4-bit quantization or large model training.