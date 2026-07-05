# Tasks: Assessing the Impact of Sample Size on Meta-Analytic Reliability

**Input**: Design documents from `/specs/001-assessing-the-impact-of-sample-size-on-t/`
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

- [X] T001a [P] Create `data/` directory structure (`raw/`, `processed/`, `output/`)
- [X] T001b [P] Create `code/` directory structure (`utils/`, `models/`, `tests/`)
- [X] T001c [P] Create `tests/` directory structure (`unit/`, `integration/`)
- [X] T001d [P] Create `specs/` directory structure and placeholder files
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, pygam, scikit-learn, requests, tqdm, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data utilities and configuration constants.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement data schema validation (Pydantic) for `MetaAnalysis`, `Subsample`, and `StabilityMetric` entities in `code/schemas.py`
- [X] T005 [P] Implement deterministic random seed management and logging utility in `code/utils/seeds.py` (logs `k`, `seed`, `estimator_type` per iteration)
- [ ] T006 [P] Implement chunked data processing framework in `code/utils/io.py` to handle >7GB potential corpus, ensuring memory safety for real-world data acquisition (FR-001).
- [X] T007 Create base model classes for `MetaAnalysis` and `Subsample` in `code/models.py`
- [X] T008 Configure error handling for zero-variance studies (SE=0), negative variance estimates, and boundary clamping in `code/utils/exceptions.py`
- [X] T009 [P] Setup environment configuration management for `DATA_SOURCE` (real vs simulation) in `code/config.py`
- [~] T009a [P] Define `nominal_coverage_target` and `stability_threshold` constants. in `code/config.py` to satisfy FR-007, SC-003, and enable executable threshold detection (T033/T034).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Subsampling Pipeline (Priority: P1) 🎯 MVP

**Goal**: Acquire real-world meta-analyses (or fallback to parameterized simulation) and generate bootstrap subsamples.

**Independent Test**: A script downloads a fixed set of meta-analyses (or generates simulation data), generates subsamples for specific `k`, and outputs a CSV of effect sizes/SEs without modeling.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for data schema validation in `tests/unit/test_schemas.py`
- [~] T011 [P] [US1] Integration test for subsampling logic (k=3, k=5, k=10) in `tests/integration/test_subsampling.py`

### Implementation for User Story 1

**Prerequisites**: T006 (Chunked Processing) and T008 (Zero-Variance/Negative Variance Handling) must be implemented first to support data acquisition.

- [~] T012 [US1] Implement `code/download.py` to fetch a substantial corpus of meta-analyses from Cochrane/Campbell. **Mandatory**: Use specific search parameters: `searchString="meta-analysis effect size"` for Cochrane Library API and `query="meta-analysis"` for Campbell Collaboration RSS. **Output**: Raw data files in `data/raw/`. If fetch fails (e.g., 404, rate limit) or returns no data, raise `DataAcquisitionError` to trigger fallback. <!-- FAILED: unspecified -->
- [~] T012a [US1] Validate the downloaded corpus count against SC-001 (>=50 real-world meta-analyses). **Logic**: If count < 50, log a **CRITICAL** warning: "Primary data requirement (FR-001) not met. Switching to Simulation Mode." Trigger the simulation fallback path (T019). If count >= 50, log success and proceed to T016. **Output**: Update `data/output/success_rate_report.json` with `mode: "real"` or `mode: "simulation"` and `count`. <!-- FAILED: unspecified -->
- [~] T019 [US1] Implement parameter generation and synthetic data generation in `code/download.py` as a fallback triggered ONLY if T012/T012a confirm failure. **Parameters**: Use values from Ioannidis et al. (2008): `tau^2 = 0.04`, `mean_effect = 0.3`, `bias = 0.1`, `study_count_range = [3, 50]`. **Output**: Write parameters to `data/raw/simulation_params.json` and synthetic data files to `data/raw/`.
- [~] T016 [US1] Implement `code/subsample.py` to generate up to 100 bootstrap subsamples for each `k` (3 to N), logging seeds and handling `k < 3` edge cases. **Must utilize** T006 (chunking) and T008 (zero-variance) logic. **Logging Requirement**: Log every subsample iteration (ID, k, seed, estimator type) to `data/processed/subsample_data.parquet` within this task.
- [~] T017 [US1] Create validation script `code/validate_data.py` to verify downloaded/generated data integrity, checksums, and **aggregate the success rate** of meta-analyses processed against the ≥50 target (SC-001), writing a summary to `data/output/success_rate_report.json`. **Output**: JSON report containing `total_target`, `actual_processed`, `success_rate`, `mode`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Stability and Coverage Metric Computation (Priority: P2)

**Goal**: Compute pooled effect sizes (FE/RE) for every subsample and derive stability/coverage metrics.

**Independent Test**: Feeding pre-generated subsamples produces a table of pooled effects, SDs, and coverage flags against the full-sample estimate.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US2] Unit test for REML vs DL estimator switching logic at k=10 in `tests/unit/test_models.py`
- [~] T022 [P] [US2] Integration test for coverage rate calculation in `tests/integration/test_metrics.py`

### Implementation for User Story 2

**Prerequisites**: Error handling for negative variance must be in place before model fitting (T008).

- [~] T023 [US2] Implement `code/models.py` to fit Fixed Effects and Random Effects models. **Primary Output**: Use DL for k≥10, REML for k<10 per FR-003. Explicitly tag this output as the "primary" deliverable in `data/processed/stability_metrics.csv`.
- [~] T024 [US2] Implement parallel sensitivity run in `code/models.py` using REML for all `k` to check for boundary artifacts (Estimator Continuity Check). **Output**: Write results to `data/processed/sensitivity_check.csv` (distinct artifact).
- [ ] T025 [P] [US2] Implement `code/metrics.py` to calculate standard deviation of pooled effects (stability) across subsamples for each `k`.
- [ ] T026 [P] [US2] Implement `code/metrics.py` to calculate CI coverage rates (proportion of subsample CIs containing full-sample estimate) for each `k`.
- [ ] T027 [US2] Implement sensitivity analysis in `code/metrics.py` by perturbing the reference value (full-sample estimate) by its SE (FR-009). **Requirement**: Write perturbation results to `data/processed/sensitivity_analysis_results.csv`, compute the variation against the primary coverage rate, and output the result to satisfy SC-006.
- [ ] T028 [US2] Aggregate primary metrics into `data/processed/stability_metrics.csv` with columns: `meta_id`, `k`, `model_type`, `sd_effects`, `coverage_rate`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Detection and Visualization (Priority: P3)

**Goal**: Fit GAM/Parametric models to detect diminishing returns threshold and generate diagnostic plots.

**Independent Test**: Providing stability metrics CSV outputs a changepoint estimate and PNG plots showing stability curves with confidence bands.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for GAM vs Linear model comparison (p-value check) in `tests/unit/test_analysis.py`
- [ ] T030 [P] [US3] Integration test for threshold detection logic in `tests/integration/test_thresholds.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/analysis.py` to fit a **Generalized Additive Model (GAM)** (Primary Method per FR-006) to stability metrics. **Target Variable**: `stability SD` (y-axis) vs `study count k` (x-axis). **Parameters**: Use cubic basis with `k=3` smoothing. **Fallback**: If GAM fails (convergence error), automatically switch to segmented regression with a minimum of 2 segments. **Output**: Save changepoint estimate to `data/output/threshold_estimate.json`.
- [ ] T032 [US3] Implement `code/analysis.py` to detect inflection point where derivative < 0.05 (unit: change in SD per unit k) and model fit (p < 0.05) is significantly better than linear. **Output**: Save changepoint estimate to `data/output/threshold_estimate.json`.
- [ ] T033 [US3] Implement `code/analysis.py` to fit a **Parametric 1/sqrt(k) model** (Secondary/Validation Method) to stability metrics for comparison with the GAM result.
- [ ] T034 [US3] Implement `code/analysis.py` to identify minimum `k` where coverage rate stabilizes within ±2% of the **nominal target read from `code/config.py` (T009a)** (SC-003, FR-007).
- [ ] T035 [US3] Implement `code/viz.py` to generate stability curve plots with confidence bands.
- [ ] T036 [US3] Implement `code/viz.py` to generate coverage plots by study count.
- [ ] T037 [US3] Save all diagnostic plots to `data/output/` and update `research.md` with threshold findings.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `README.md`
- [ ] T039 Code cleanup and refactoring (remove unused imports, optimize loops)
- [ ] T040 Performance optimization: Ensure full bootstrap analysis runs within 6 hours on 2 CPU cores
- [ ] T041 [P] Additional unit tests for edge cases (N<3, zero variance) in `tests/unit/`
- [ ] T042 Security hardening: Verify no PII leaks in logs or outputs
- [ ] T043 Run quickstart.md validation and final CI check

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metrics output

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
Task: "Contract test for data schema validation in tests/unit/test_schemas.py"
Task: "Integration test for subsampling logic (k=3, k=5, k=10) in tests/integration/test_subsampling.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py in code/download.py"
Task: "Implement subsample.py in code/subsample.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Data acquisition + Subsampling)
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
 - Developer A: User Story 1 (Data & Subsampling)
 - Developer B: User Story 2 (Metrics & Modeling)
 - Developer C: User Story 3 (Analysis & Viz)
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
- **Feasibility Check**: All modeling tasks (REML/DL) must run on CPU-only CI (no CUDA, no 8-bit quantization).
- **Data Integrity**: No fake data generation; use real URLs or cite simulation parameters from literature.
- **Configuration**: All thresholds (e.g., coverage target) must be read from `config.py` (defined in T009a) to allow for deferred decisions.
- **Primary Method**: GAM is the primary method for threshold detection (FR-006); Parametric 1/sqrt(k) is secondary/validation.
- **Ordering**: All data utilities (chunking, error handling) are in Phase 2 to ensure they are available before Phase 3 data acquisition.