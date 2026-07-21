# Tasks: Statistical Analysis of Flight Delay Distributions

**Input**: Design documents from `/specs/001-flight-delay-distributions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan: Execute `mkdir -p code/tests data/raw data/processed data/results docs code/contracts tests/unit tests/integration tests/contract` and `touch code/__init__.py tests/__init__.py data/.gitkeep docs/.gitkeep` to establish the directory tree.
- [X] T002 Initialize Python 3.11 project with requirements.txt: Create `code/requirements.txt` containing pinned versions of `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, and `pytest`.
- [X] T003 [P] Configure linting (ruff) and formatting (black): Create `pyproject.toml` with both ruff and black configuration for the `code/` directory in a single operation to avoid file conflicts.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/config.py` for paths, random seeds, thresholds, and environment validation: Define constants `RANDOM_SEED=42`, `BTS_URL` (canonical endpoint), `TARGET_YEAR`, and `MEMORY_LIMIT_GB=6.5`. Include validation logic to assert `BTS_URL` and `TARGET_YEAR` are set. **NOTE: Do NOT define `X_MIN_THRESHOLD` as a constant. Per FR-014 and Plan.md Phase 2 Step 4, `x_min` MUST be estimated dynamically via KS minimization at runtime.**
- [X] T005 [P] Implement memory monitoring utilities in `code/utils.py`: Implement `check_memory_limit(limit_gb=6.5)` that raises `MemoryError` if current usage exceeds limit, and `log_peak_memory()` that records peak RAM to stderr.
- [X] T006 [P] Create base entity definitions and JSON schemas in `code/contracts/`: Create `code/contracts/delay_record.schema.yaml`, `code/contracts/distribution_model.schema.yaml`, and **`code/contracts/tail-index-estimate.schema.yaml`**. **Create a FINALIZED JSON schema for 'TailIndexEstimate' based on data-model.md and spec.md FR-016. This schema is the contract that T033 implementation MUST adhere to.**
- [X] T007 Setup pytest environment and base test fixtures in `tests/conftest.py`
- [X] T008 Setup error handling and logging infrastructure in `code/utils.py`: Configure a logging instance with level INFO, file handler to `data/logs/pipeline.log`, and a custom exception class `PipelineError`.
- [X] T019 [P] Implement memory-mapped array handling in `code/preprocessing.py`: Implement logic to use `pandas.read_csv` with `chunksize` or `numpy.memmap` if estimated size > 6.5GB; if impossible, raise `SystemExit` with message "Memory limit exceeded: full dataset cannot be loaded."

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Retrieve, clean, and validate BTS data; produce `cleaned_delays.csv`, `summary_report.json`, and perform component comparison.

**Independent Test**: The pipeline can be run in isolation to download, parse, and filter the BTS data, outputting a summary report ("Loaded N valid records...") without performing any distribution fitting.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for memory estimation logic in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [US1] Unit test for anomaly flagging logic (1440+ min) in `tests/unit/test_preprocessing.py`
- [X] T012 [P] [US1] Integration test for full download-to-clean pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data_loader.py`: Download BTS CSV for specified year with retry/backoff; fail if full year unavailable. **Download from official API endpoint, implementing a maximum of 3 retries with exponential backoff. Raise specific exception message on failure.**
- [X] T014 [P] [US1] Implement `code/preprocessing.py`: Load CSV, filter commercial US flights, compute `total_delay = ArrDelay + DepDelay`, treat missing values as 0.
- [X] T015 [US1] Implement `code/preprocessing.py`: Remove negative delays; flag `is_data_error` (>10,000 min) and `is_anomaly` (>1,440 min); exclude errors from primary set.
- [X] T016 [US1] Implement `code/preprocessing.py`: Calculate retention rate (`valid_records / total_downloaded`) and report in summary. **Per spec.md US-1, this task MUST report the rate. Do NOT enforce a hard pipeline halt (SystemExit) if the rate is < 95%. The spec requires reporting and graceful failure on memory limits only.**
- [X] T017 [US1] Implement `code/preprocessing.py`: Create zero-excluded subset for sensitivity analysis; flag zero-inflation. **MUST output file `data/processed/cleaned_delays_no_zero.csv`.**
- [X] T018 [US1] Implement `code/main.py` (Stage 1): Orchestrate download, cleaning, and save `cleaned_delays.csv` + `summary_report.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Parametric Model Fitting and Goodness-of-Fit Evaluation (Priority: P2)

**Goal**: Fit multiple distributions, compute metrics (AIC/BIC/KS/AD), and perform Vuong test on tail subset

**Independent Test**: The analysis can be run on a static, pre-processed CSV to verify all 5 distributions are fitted, parameters estimated via MLE, metrics calculated, and Vuong test performed.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for MLE convergence handling (non-convergence catch) in `tests/unit/test_models.py`
- [X] T021 [P] [US2] Unit test for Vuong test implementation in `tests/unit/test_models.py`
- [X] T022 [P] [US2] Integration test for model fitting and metrics generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T023a [US2] **Fit models to FULL cleaned dataset**: Implement `code/models.py` to fit Exponential, Gamma, Log-Normal, Weibull, Pareto to the *full* cleaned dataset (excluding data errors). **This step establishes the bulk fit as required by plan.md Phase 1 (T007).**
- [X] T026 [US2] **Estimate x_min via KS minimization**: Implement `code/diagnostics.py` to estimate `x_min` using the Kolmogorov-Smirnov minimization method over a grid. Save the estimated value and confidence intervals to `data/results/x_min_estimate.json`. **Must run before T024 and T025a.**
- [X] T024 [US2] Implement `code/models.py`: MLE fitting for Pareto restricted to `delay >= x_min` using the `x_min` value from T026. **Depends on: T026.**
- [X] T025a [US2] Implement `code/models.py`: Re-fit Exponential, Gamma, Log-Normal, Weibull on the *tail subset* (`delay >= x_min`) to enable tail-metric comparison. **Depends on: T026.**
- [X] T028 [US2] **Compare sum distribution vs. components**: Implement `code/models.py` to perform a Kolmogorov-Smirnov test between the `total_delay` distribution and the `ArrDelay`/`DepDelay` distributions. Generate side-by-side histograms for visualization. Save results, including the KS p-value, to `data/results/component_comparison.json`. **This task implements FR-002 and SC-008. Moved from Phase 3 to align with plan.md Phase 1 (T008).**
- [X] T025 [US2] Implement `code/models.py`: Calculate AIC, BIC, KS, AD for all 5 models on the tail subset; save to `model_comparison.json`.
- [X] T027 [US2] Implement `code/models.py`: Perform Vuong test (best heavy-tail vs. best short-tail) on tail subset; report p-value in `vuong_test_results.json`.
- [X] T029 [US2] Implement `code/main.py` (Stage 2): Orchestrate fitting, metric calculation, and Vuong test; ensure at least 3 models converge.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Heavy-Tail Diagnostics and Visualization (Priority: P3)

**Goal**: Perform Hill estimator stability analysis, Bootstrap GoF, and generate diagnostic plots.

**Independent Test**: The system can generate the log-log survival plot, Hill estimator output, and tail KS test results for a provided dataset, producing a visual confirmation of linearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for Hill estimator variance minimization logic in `tests/unit/test_diagnostics.py`.
 - **Input**: Mock data array representing tail indices for k=1 to k_max.
 - **Logic**: Verify that the function correctly identifies the k value that minimizes variance over a sliding window of size w=10, constrained to k/n <= 0.1.
 - **Assertion**: Assert that the returned `optimal_k` matches the expected value for the mock data, and that the `stability_curve` is generated correctly.
 - **Dependency**: Relies on interface definition in T006 (`tail-index-estimate.schema.yaml`).

### Implementation for User Story 3

- [X] T033 [P] [US3] **Implement Hill estimator stability analysis**: Implement `code/diagnostics.py` to compute the tail index using the Hill estimator on the top k records.
 - **Algorithm**:
 1. Load `x_min` from `data/results/x_min_estimate.json`.
 2. Load the zero-excluded subset from `data/processed/cleaned_delays_no_zero.csv`.
 3. Filter data to `delay >= x_min`.
 4. Iterate `k` from a small positive integer to `floor(0.1 * n)` (where n is the number of tail records).
 5. For each `k`, compute the Hill estimate `alpha_k`.
 6. Compute the variance of `alpha` over a sliding window of size `w=10`.
 7. Identify the `k` that minimizes this variance.
 - **Constraint**: Ensure `k/n <= 0.1` is strictly enforced.
 - **Input**: `x_min` from `data/results/x_min_estimate.json`, zero-excluded subset from T017.
 - **Output**:
 1. Save the full stability curve (variance vs k) to `data/results/stability_curve.csv`.
 2. Save summary stats (min_k, max_k, variance_min, estimated_alpha, confidence_interval) to `data/results/tail_index_estimate.json`.
 - **Verification**: Explicitly check that the returned `optimal_k` satisfies `k/n <= 0.1` and that the variance minimization logic matches the spec (w=10).
 - **Error Handling**: If `x_min` is missing or invalid, raise `PipelineError` with message "x_min estimation failed: cannot proceed with Hill estimator."
 - **Dependency**: Requires T026 (x_min estimation) and T017 (zero-excluded subset).

- [X] T034 [US3] **Implement Model Rejection Logic**: Implement `code/diagnostics.py` to compute R² using OLS regression on the log-log transformed survival data and reject models with R² < 0.95 or unstable Hill index.
 - **Input**: Best-fit model parameters from `data/results/model_comparison.json`, tail data from `data/processed/cleaned_delays.csv`.
 - **Logic**:
 1. Generate log-log survival plot data.
 2. Perform OLS regression on the log-log transformed tail data.
 3. Calculate R².
 4. If R² < 0.95 OR Hill index (from T033) is unstable (variance > threshold), mark model as "rejected".
 - **Output**: Save results to `data/results/model_rejection.json` with schema: `{ "model_name": "string", "r_squared": float, "hill_stable": bool, "status": "accepted|rejected", "reason": "string" }`.
 - **Propagation**: Update `data/results/model_comparison.json` to include a `status` field reflecting this rejection logic.

- [X] T035 [US3] Generate log-log survival plot and QQ-plot for visualization.
 - **Input**: Best-fit model parameters, tail data.
 - **Output**: Save plots to `data/results/` (e.g., `log_log_survival.png`, `qq_plot.png`).

- [X] T036 [US3] **Implement Tail KS test**: Implement `code/diagnostics.py` to perform a Kolmogorov-Smirnov goodness-of-fit test on the tail subset (x >= x_min).
 - **Input**: Tail subset data (from `data/processed/cleaned_delays.csv` filtered by `x_min`), best-fit heavy-tail model parameters.
 - **Logic**: Use `scipy.stats.kstest` to compare the empirical tail distribution against the theoretical cumulative distribution function (CDF) of the fitted model.
 - **Output**: Save results to `data/results/tail_ks.json` with schema: `{ "model_name": "string", "ks_statistic": float, "p_value": float, "tail_threshold": float }`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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