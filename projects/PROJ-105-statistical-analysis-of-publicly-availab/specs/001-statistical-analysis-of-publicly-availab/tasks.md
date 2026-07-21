# Tasks: Statistical Analysis of Flight Delay Distributions

**Input**: Design documents from `/specs/001-flight-delay-distributions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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
- [X] T006 [P] Create base entity definitions and JSON schemas in `code/contracts/`: Create `code/contracts/delay_record.schema.yaml`, `code/contracts/distribution_model.schema.yaml`, and **`code/contracts/tail-index-estimate.schema.yaml`** with fields defined in `data-model.md`. **This task consolidates the schema generation for all core entities, including TailIndexEstimate (FR-016), to ensure contracts are ready before code generation.**
- [X] T007 Setup pytest environment and base test fixtures in `tests/conftest.py`
- [X] T008 Setup error handling and logging infrastructure in `code/utils.py`: Configure a logging instance with level INFO, file handler to `data/logs/pipeline.log`, and a custom exception class `PipelineError`.
- [X] T019 [P] Implement memory-mapped array handling in `code/preprocessing.py`: Implement logic to use `pandas.read_csv` with `chunksize` or `numpy.memmap` if estimated size > 6.5GB; if impossible, raise `SystemExit` with message "Memory limit exceeded: full dataset cannot be loaded."

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Retrieve, clean, and validate BTS data; produce `cleaned_delays.csv`, `summary_report.json`, and perform component comparison.

**Independent Test**: The pipeline can be run in isolation to download, parse, and filter the BTS data, outputting a summary report ("Loaded N valid records...") and component comparison results without performing any distribution fitting.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for memory estimation logic in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [US1] Unit test for anomaly flagging logic (1440+ min) in `tests/unit/test_preprocessing.py`
- [X] T012 [P] [US1] Integration test for full download-to-clean pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data_loader.py`: Download BTS CSV for specified year with retry/backoff; fail if full year unavailable. <!-- FAILED: unspecified -->
- [X] T014 [P] [US1] Implement `code/preprocessing.py`: Load CSV, filter commercial US flights, compute `total_delay = ArrDelay + DepDelay`, treat missing as 0.
- [X] T015 [US1] Implement `code/preprocessing.py`: Remove negative delays; flag `is_data_error` (>10,000 min) and `is_anomaly` (>1,440 min); exclude errors from primary set.
- [X] T016 [US1] Implement `code/preprocessing.py`: Calculate retention rate (`valid/total`); save `summary_report.json` with the rate. **Per spec.md US-1, this task MUST report the rate. Do NOT enforce a hard pipeline halt (SystemExit) if the rate is < 95%. The spec requires reporting and graceful failure on memory limits only.**
- [X] T017 [US1] Implement `code/preprocessing.py`: Create zero-excluded subset for sensitivity analysis; flag zero-inflation.
- [X] T028 [US1] **Compare sum distribution vs. components**: Implement `code/models.py` to perform a Kolmogorov-Smirnov test between the `total_delay` distribution and the `ArrDelay`/`DepDelay` distributions. Generate side-by-side histograms for visualization. Save results, including the KS p-value, to `data/results/component_comparison.json`. **This task implements FR-002 and SC-008. Moved to Phase 3 to align with plan.md Phase 1 (T008) which lists this as a deliverable for the initial model fitting/data analysis workflow.** **Depends on: T018.**
- [X] T018 [US1] Implement `code/main.py` (Stage 1): Orchestrate download, cleaning, and save `cleaned_delays.csv` + `summary_report.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Parametric Model Fitting and Goodness-of-Fit Evaluation (Priority: P2)

**Goal**: Fit multiple distributions, compute metrics (AIC/BIC/KS/AD), and perform Vuong test on tail subset

**Independent Test**: The analysis can be run on a static, pre-processed CSV to verify all 5 distributions are fitted, parameters estimated via MLE, metrics calculated, and Vuong test performed.

**⚠️ PHASE 4 INTERNAL DEPENDENCIES**:
- **T026** (x_min estimation) MUST complete before **T024** (Pareto fitting) and **T025a** (Tail subset refitting).
- **T018** (US1 completion) MUST complete before **T026** (requires cleaned data).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for MLE convergence handling (non-convergence catch) in `tests/unit/test_models.py`
- [X] T021 [P] [US2] Unit test for Vuong test implementation in `tests/unit/test_models.py`
- [X] T022 [P] [US2] Integration test for model fitting and metrics generation in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement `code/models.py`: MLE fitting for Exponential, Gamma, Log-Normal, Weibull on **full cleaned data** (excluding data errors).
- [X] T026 [US2] **Estimate `x_min` via KS minimization with Bootstrap Uncertainty**: Implement `code/diagnostics.py` to estimate `x_min` via KS minimization over a grid. **Per spec.md FR-014, estimate `x_min` before fitting Pareto. Ensure the method converges or reports failure; do not use arbitrary iteration caps that may compromise accuracy.** Use standard convergence checks. Report confidence intervals (lower/upper percentiles). Save output to `data/results/x_min_estimate.json` with fields `x_min`, `confidence_interval`, and `method`. **This task must complete before T024 and T025a within Phase 4 to ensure x_min is available for tail subset definition.** **NOTE: This task depends on T018 (US1) producing the cleaned dataset.**
- [X] T024 [US2] Implement `code/models.py`: MLE fitting for Pareto restricted to `delay >= x_min` using the `x_min` value from T026. **Depends on: T026.**
- [X] T025a [US2] Implement `code/models.py`: Re-fit Exponential, Gamma, Log-Normal, Weibull on the **tail subset** (delay >= x_min) to enable tail-metric comparison. **Depends on: T026.**
- [X] T025 [US2] Implement `code/models.py`: Calculate AIC, BIC, KS, AD for all 5 models on the tail subset; save to `model_comparison.json`.
- [X] T027 [US2] Implement `code/models.py`: Perform Vuong test (best heavy-tail vs. best short-tail) on tail subset; report p-value in `vuong_test_results.json`.
- [X] T029 [US2] Implement `code/main.py` (Stage 2): Orchestrate fitting, metric calculation, and Vuong test; ensure at least 3 models converge.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Heavy-Tail Diagnostics and Visualization (Priority: P3)

**Goal**: Perform Hill estimator stability analysis, Bootstrap GoF, and generate diagnostic plots

**Independent Test**: The system can generate the log-log survival plot, Hill estimator output, and tail KS test results for a provided dataset, producing a visual confirmation of linearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] **Unit test for Hill estimator variance minimization logic**: Implement a unit test in `tests/unit/test_diagnostics.py` that verifies the Hill estimator stability analysis correctly minimizes variance over a sliding window of size w=10, constrained to k/n <= 0.1. **This task uses mocks for the T033 implementation to allow parallel execution.** <!-- FAILED: unspecified -->
- [X] T031 [P] [US3] Unit test for Bootstrap GoF p-value calculation in `tests/unit/test_diagnostics.py`
- [X] T032 [P] [US3] Integration test for diagnostic plotting and validationin `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] **Implement Hill estimator stability analysis**: Implement `code/diagnostics.py` to compute the tail index using the Hill estimator on the top k records. **Algorithm**: Minimize the variance of alpha estimates over a sliding window of size w=10, constrained to k/n <= 0.1. **Input**: Use `x_min` from `data/results/x_min_estimate.json` (T026). **Output**: Save the full stability curve (variance vs k) to `data/results/stability_curve.csv` and the summary stats (min_k, max_k, variance_min, estimated_alpha, confidence_interval) to `data/results/tail_index_estimate.json`. **This task implements FR-005 and SC-009.** **Depends on: T026.**
- [ ] T034 [US3] **Implement Model Rejection Logic (R² and Hill Stability)**: Implement `code/diagnostics.py` to perform the primary model rejection check. **Algorithm**: Calculate the R² value for the log-log survival plot using OLS regression on the tail data. **Rejection Rule**: Per spec.md FR-015 and SC-004, REJECT the best AIC model if R² < 0.95 OR if the Hill index is unstable. **Supplementary**: Perform a Bootstrap Goodness-of-Fit test as a secondary diagnostic, but DO NOT use it as the primary gate for rejection. Save the R², Hill stability status, and Bootstrap p-value to `data/results/model_rejection.json`. **Update `model_comparison.json` with a "rejected" flag and reason if the best model fails the R² or Hill stability criteria.** **This task implements FR-015 and SC-004.**
- [X] T035 [US3] **Implement Log-Normal discrimination**: Implement `code/diagnostics.py` to calculate the curvature statistic of the Hill plot. **Algorithm**: Simulate multiple Log-Normal datasets with similar parameters, calculate the curvature for each, and compare the empirical curvature to the null distribution. **Rejection Rule**: If the empirical curvature is not significantly different from the Log-Normal null (p > 0.05), the hypothesis of a pure Power-Law is rejected in favor of a Log-Normal heavy tail. Save the result to `data/results/log_normal_test.json`. **This task implements FR-015 (Log-Normal discrimination aspect) and SC-003.**
- [X] T036 [US3] Implement `code/visualization.py`: Generate log-log survival plot (empirical vs. fitted) with R² calculation for visualization purposes only. **Note**: R² is calculated for visualization and as a gate per FR-015.
- [X] T037 [US3] Implement `code/visualization.py`: Generate QQ-plots for best-fit model.
- [ ] T038 [US3] **Implement Tail KS test**: Implement `code/diagnostics.py` to perform a standard Kolmogorov-Smirnov goodness-of-fit test on the tail subset (x >= x_min). **Algorithm**: Compute the KS statistic and p-value directly against the fitted distribution. **Note**: Do NOT use bootstrapped p-value correction; implement the standard KS test as required by FR-010 and SC-007. Save the p-value to `data/results/tail_ks.json`. **This task implements FR-010 and SC-011.**
- [ ] T039 [US3] Implement `code/main.py` (Stage 3): Orchestrate diagnostics; if the best model fails the R² < 0.95 or Hill stability check (T034 logic), flag the next best candidate and report the failure reason. **This task ensures the validation logic from FR-015 is applied.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Final Validation (Polish)

**Purpose**: Compile final results, validate success criteria, and frame findings

- [ ] T041 [US1] Implement `code/main.py` (Stage 4): Compile final `summary_report.json` including runtime, retention_rate, model_rankings, p-values, and causality_disclaimer.
- [X] T042 [US3] **Validate Success Criteria**: Implement assertions for SC-001 (retention rate *reported* AND >= 95%), SC-002 (3 models), SC-003 (Hill index), SC-005 (runtime <= 3600s), SC-006 (Vuong), SC-007 (Tail KS), SC-009 (stability), SC-010/SC-011 (p-values). **For SC-001: Validate that the retention rate was calculated and reported. If the reported rate is < 95%, the validation status for SC-001 must be marked as FAIL (as per spec SC-001), but the pipeline MUST NOT crash (graceful failure only on memory limits). Write `validation_status.json` with PASS/FAIL for each SC.** **Note**: The 3600s limit (SC-005) is the strict runtime gate, superseding the 6h FR-008 limit for success criteria.
- [X] T043 [P] Update `docs/data-model.md` and `docs/quickstart.md` with final entity definitions and execution instructions.
- [X] T044 [P] Create `.github/workflows/ci.yml` to run pytest and verify memory/time constraints; ensure build passes.

**Checkpoint**: Final validation complete; project ready for review.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable. **Requires T018 (US1) to complete before T026 (Phase 4 start).**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable. **Requires T029 (US2) to complete before T033/T034 (Phase 5 start).**

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
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Note**: Phase 7 (Mechanism Discovery & Regime Analysis) and tasks T045-T048 were explicitly REMOVED from this artifact as they constituted unapproved scope creep not anchored to any User Story in the spec. The 'regime segmentation' and 'cascade analysis' logic has been deleted to prevent consumer-before-producer risks. T016 was revised to remove hard pipeline halt. T034 was revised to use R²/Hill stability as primary gate. T026 iteration cap removed to ensure accuracy. T040 was merged into T006 to consolidate schema generation. T042 was revised to enforce SC-001's 95% threshold in validation output while maintaining graceful pipeline execution. T028 was moved to Phase 3 to align with plan.md Phase 1.
