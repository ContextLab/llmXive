# Tasks: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

**Input**: Design documents from `/specs/001-evaluating-the-robustness-of-common-stat/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-483-evaluating-the-robustness-of-common-stat/`)
- [X] T002 Initialize Python 3.10+ project with dependencies: `numpy`, `scipy`, `pandas`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest` in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ NOTE**: Tasks in this phase define *libraries* and *interfaces*. They do NOT execute the Monte Carlo simulation (which happens in Phase 3).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to load and validate `code/config.yaml` against `contracts/simulation_config.schema.yaml`
- [X] T005a [P] Create `data/manifests/datasets.yaml` with **verified UCI/OpenML URLs** for datasets containing continuous or categorical variables suitable for t-tests, ANOVA, or chi-squared tests. **Must include specific URLs**: e.g., ` (UCI Adult), ` (UCI Wine), and ` (OpenML example). This file must be populated before T005 runs.
- [X] T005 [P] Implement `code/data_loader.py` (FR-001): Fetch datasets from **verified URLs defined in `data/manifests/datasets.yaml`**, parse them, **verify they contain continuous or categorical variables suitable for t-tests/ANOVA/chi-squared**, and save raw CSVs to `data/raw/` and generate `data/manifests/checksums.json`.
- [X] T006a [P] Implement `code/dependency_injector.py` (FR-003): Vectorized **AR(1) resampling** function with tunable strength $r \in [0, 0.9]$. **Validation**: Verify injected autocorrelation matches target $r$ within 5% tolerance.
- [ ] T006b [P] Implement `code/dependency_injector.py` (FR-003): **Block bootstrap** function for hierarchical dependency with tunable block size (range starting from a small lower bound up to 50) and strength parameters. **Validation**: Verify block size distribution matches target.
- [ ] T006c [P] Implement `code/dependency_injector.py` (FR-003): **Spatial kernel smoothing** function for spatial dependency with tunable bandwidth (range low to high). **Requirement**: Must use a **validated feature-space clustering proxy** (provided by T037) for datasets lacking explicit coordinates.
- [X] T037 [P] Implement `code/dependency_injector.py` (FR-003): **Feature-space clustering proxy** logic to generate spatial proxies for datasets lacking explicit coordinates. Output a proxy generation report to `data/manifests/spatial_proxy_report.json`.
- [ ] T041 [P] Implement `code/dependency_injector.py` (FR-003): **Validation logic** for the feature-space clustering proxy. Ensure the proxy is validated as per FR-003 requirements. Output a validation report to `data/manifests/spatial_proxy_validation.json`.
- [ ] T035 [P] Implement `code/data_loader.py` (FR-001, Spec Assumptions): **Dataset validation logic** to verify $N \ge 50$. If $N < 50$, skip the dataset and log a violation to `results/validation_report.json`. **If all fetched datasets fail this check, raise a `CriticalValidationError`** to prevent pipeline deadlock. **Note**: This task applies to ALL user stories.
- [X] T007 [P] **Library Definition**: Create `code/metrics.py` (FR-005, SC-001). **Define** functions `calculate_type1_error`, `calculate_power`, `clopper_pearson_ci`, and `train_logistic_model`. **Do NOT run the simulation here**. Ensure all functions are designed to accept aggregated p-values and return metrics with **Clopper-Pearson confidence intervals**.
- [ ] T016-logistic [P] **Library Definition**: Extend `code/metrics.py` (Constitution Principle VII): **Define** the logic to train and save logistic regression models relating **error rate to dependency strength** to `results/logistic_models.pkl`. **Verification**: Ensure model convergence and AUC > 0.5 logic is defined. **Execution** of this training will occur in Phase 3 after data generation.
- [X] T008 [P] **Library Definition**: Implement `code/visualizer.py` (FR-006). **Define** plot generation logic for error rate curves and power comparisons. **Do NOT generate plots here**.
- [~] T009 Setup `tests/unit/` with mock data fixtures for dependency injection logic validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Type I Error Inflation Quantification (Priority: P1) 🎯 MVP

**Goal**: Quantify false-positive rate inflation of t-tests/ANOVA under varying dependency strengths (AR(1), Block Bootstrap).

**Independent Test**: Run 10,000 replications for a single test (t-test) and single dependency (AR(1), $r=0.3$) on a sampled dataset, outputting a table of observed error rates vs. nominal alpha with Clopper-Pearson CI.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for AR(1) injection logic in `tests/unit/test_dependency_injector.py` (verify autocorrelation matches target $r$)
- [X] T011 [P] [US1] Unit test for Null Hypothesis construction in `tests/unit/test_simulation_runner.py` (verify p-values are uniform under $r=0$). **Note**: Create failing stub first.

### Implementation for User Story 1

- [~] T012 [US1] **Execution**: Implement `code/simulation_runner.py` (FR-004, FR-005): Implement **"Generate-then-Inject"** Monte Carlo loop for t-test and ANOVA. **Algorithm**: 1) Generate synthetic data under true null (Normal(0,1)), 2) Inject dependency structure (AR(1)/Block Bootstrap) with strength $r$, 3) Apply statistical test, 4) Record p-value. **Note**: This implements the paradigm defined in `plan.md` Summary to ensure a true null hypothesis. Ensure a sufficient number of replications per config to achieve statistical robustness. **Output**: Save raw p-values to `results/simulation_raw.csv`. **This task is the PRODUCER of data for T007/T008 functions.**
- [~] T013 [US1] **Execution**: Implement sensitivity analysis sweep in `code/main.py`: Sweep $r$ across a range of values including zero and positive increments. **Depends on T012 completion**. Aggregate results using functions defined in T007 to `results/aggregated.csv`.
- [~] T014 [US1] **Execution**: Implement trend verification logic in `code/metrics.py`: Calculate **trend test (e.g., Spearman rank correlation)** to verify monotonic increase of error rates with $r$ (p < 0.05) as per US-1 AC-2. **This task consumes `results/aggregated.csv` from T013**. Output `trend_status` column to `results/aggregated.csv`.
- [~] T040 [US1] **Execution**: Implement edge case handling logic in `code/simulation_runner.py`: Define and implement behavior for datasets where the **null hypothesis cannot be cleanly constructed** (e.g., all variables highly correlated) or when **injected dependency violates normality assumptions** beyond non-independence, as defined in **spec.md Edge Cases**. Log specific edge case failures to `results/edge_case_report.json`. **Note**: This task applies to all user stories.
- [ ] T016-logistic [US1] **Execution**: **Run** the logistic regression training defined in T016-logistic (Phase 2) using the aggregated data from T013. Save model to `results/logistic_models.pkl`. **Verification**: Ensure model convergence and AUC > 0.5.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Test and Structure Comparison (Priority: P2)

**Goal**: Compare robustness of t-test, ANOVA, and Chi-squared across temporal, spatial, and hierarchical dependency structures.

**Independent Test**: Run simulation for all three tests and at least two dependency structures, producing a comparative plot showing error rate curves.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test for multi-test pipeline in `tests/integration/test_cross_test_comparison.py`
- [X] T018 [P] [US2] Contract test for output CSV schema in `tests/contract/test_result_schema.py`

### Implementation for User Story 2

- [~] T019 [US2] (Removed: Covered by T006c)
- [X] T020a [US2] Extend `code/simulation_runner.py` to include **Chi-squared test logic** and block bootstrap for hierarchical structures.
- [X] T020b [US2] Extend `code/metrics.py` to implement **Chi-squared error rate calculation and reporting** as required by FR-005.
- [X] T021 [US2] Implement aggregation logic in `code/main.py` to group results by test type and dependency structure
- [X] T022 [US2] Update `code/visualizer.py` to generate comparative line plots (x=dependency strength, y=error rate, hue=test type) per AC-1
- [~] T023 [US2] Implement threshold detection logic to report specific $r$ where error rate exceeds $\alpha=0.10$ per AC-2

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Power Analysis under Dependency (Priority: P3)

**Goal**: Quantify the reduction in statistical power when non-independence is present.

**Independent Test**: Inject true effects (mean shift $\delta=1.0\sigma$) into dependency-injected data and measure proportion of significant results vs. baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for effect injection logic in `tests/unit/test_effect_injection.py`
- [ ] T025 [P] [US3] Integration test for power calculation in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Extend `code/simulation_runner.py` to support "True Effect" mode (inject mean shift $\delta$ before dependency injection). **Depends on T012** (Generate-then-Inject loop).
- [ ] T027a [US3] Implement power calculation logic in `code/metrics.py`: Calculate observed power at $r=0$ and $r=0.3$ for true effect scenarios.
- [ ] T027b [US3] Implement delta calculation logic in `code/metrics.py`: Calculate **percentage reduction in power** between $r=0$ and $r=0.3$ as required by US-3 AC-2.
- [ ] T028 [US3] Update `code/visualizer.py` to generate power loss curves (x=dependency strength, y=power)
- [ ] T029 [US3] Add reporting logic in `code/main.py` to output the **percentage reduction in power** calculated by **T027b** to the final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` and `README.md`
- [ ] T031a [P] Refactor: Extract simulation loop into `run_single_replication` function in `code/simulation_runner.py`
- [ ] T031b [P] Refactor: Vectorize aggregation logic in `code/main.py` for CPU efficiency
- [ ] T032a [P] Profile `code/simulation_runner.py` and optimize vectorized operations to ensure 10,000 replications complete in < 6 hours.
- [ ] T032b [P] Log execution time and memory usage to `results/perf_log.json` to verify FR-008.
- [ ] T033 [P] Additional unit tests for edge cases (null hypothesis construction, small N) in `tests/unit/`
- [ ] T034 Run quickstart.md validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T005a must run before T005.
 - T041 must run before T006c (or T006c must handle missing proxy gracefully).
 - T035 must run after T005 to validate fetched data.
 - **T007/T008 (Library Definitions)** must be completed before T012/T022 (Execution) to ensure functions exist.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **T012 (Simulation Runner)** is the **first** execution task in Phase 3. It produces the data consumed by T013/T014.
 - **T013** depends on **T012** completion.
 - **T014** depends on **T013** completion.
 - **T016-logistic (Execution)** depends on **T013** completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for AR(1) injection logic in tests/unit/test_dependency_injector.py"
Task: "Unit test for Null Hypothesis construction in tests/unit/test_simulation_runner.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation_runner.py (FR-004, FR-005)"
Task: "Implement sensitivity analysis sweep in code/main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Execution Order: T012 -> T013 -> T014 -> T016-logistic)
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions (multi-core, sufficient RAM). No GPU, no deep learning, no low-bit quantization. Use vectorized NumPy operations.
- **Scientific Validity**: The "Generate-then-Inject" paradigm (Plan) is the authoritative method for null hypothesis construction.
- **Data Integrity**: All datasets must be fetched from verified, canonical URLs (UCI/OpenML) defined in `data/manifests/datasets.yaml`. No synthetic or fake data generation for input.
- **Reproducibility**: All random seeds must be pinned in `code/config.yaml` and logged in `results/perf_log.json`.
- **Edge Cases**: T040 ensures robust handling of datasets where standard null construction fails.
- **Task ID Integrity**: T016-logistic is the unique ID for the logistic regression task. T016 is no longer used.
- **Execution Flow**: Phase 2 defines *how* to calculate metrics (Library). Phase 3 *runs* the simulation (Producer) and then *applies* the metrics (Consumer).