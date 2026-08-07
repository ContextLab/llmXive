# Tasks: Evaluating Robustness of Statistical Methods to Non-Independence

**Input**: Design documents from `/specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence/`
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

- [ ] T001 Create `src/` directory at repository root <!-- FAILED: unspecified -->
- [ ] T001b Create `tests/` directory at repository root
- [ ] T001c Create `data/`, `results/`, and `specs/` directories at repository root
- [ ] T001d Create `data/raw/` and `data/processed/` subdirectories
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (numpy, pandas, scipy, statsmodels, arch, yfinance, requests, matplotlib, seaborn, xarray, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/utils/config.py` with random seeds, alpha=0.05, and path constants
- [X] T005 [P] Implement `src/utils/logging.py` for structured warnings/errors
- [X] T006 [P] Create base data models (TimeSeries, SyntheticData) in `src/data/models.py`
- [ ] T007 [P] Setup `data/raw/`, `data/processed/`, `results/` directories with checksum validation logic AND implement logic to compute checksums and record them in `state/projects/PROJ-369-evaluating-the-robustness-of-statistical.yaml` to satisfy Constitution Principle III and V.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest diverse public time series, handle missing values, and ensure stationarity via ADF/DFA logic.

**Independent Test**: Run the pipeline against fixed public URLs; verify output is clean, stationary/detrended, with documented preprocessing path (ADF p-value, diff count, or detrend status).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T008 [P] [US1] Unit test for missing value interpolation in `tests/unit/test_preprocessing.py`
- [X] T009 [P] [US1] Unit test for ADF stationarity loop in `tests/unit/test_preprocessing.py`
- [X] T010 [P] [US1] Integration test for full ingestion pipeline on sample NOAA data in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `src/data/ingestion.py` to download/cache 5+ datasets (NOAA, Yahoo Finance, UK National Grid) with verified URLs. **Must fail loudly** if real fetch fails (no synthetic fallback).
- [X] T012 [P] [US1] Implement `src/data/preprocessing.py` missing value handler: linear interpolation for ALL missing values (no gap threshold) to ensure 0 missing values in output.
- [X] T013 [US1] Implement `src/data/preprocessing.py` stationarity logic: **Resample** the UK National Grid Load dataset to a consistent frequency (e.g., hourly) before stationarity testing. Run ADF test. If p < 0.05, difference until stationary. If p ≥ 0.05, detrend via linear regression residuals. Log all actions.
- [X] T014 [P] [US1] Implement `src/data/metrics.py` to compute ACF (lag 20), Hurst exponent (DFA), and spectral density peak ratio for **every REAL loaded series** (US1). **Do not** include synthetic series here (see T023).
- [X] T015 [US1] Implement edge case handling in `src/data/preprocessing.py`: Skip datasets < 25 points with warning; handle numerical instability in spectral density by falling back to variance metric.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Ground-Truth Generation and Autocorrelation Quantification (Priority: P2)

**Goal**: Generate synthetic data with known ground truth (H, mean=0) and create null distributions via shuffling.

**Independent Test**: {{claim:c_93adc3e0}}; verify shuffled versions have ACF lag-1 ≈ 0.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for fGn/ARFIMA generation accuracy in `tests/unit/test_synthesis.py`
- [X] T017 [P] [US2] Unit test for shuffling null distribution logic in `tests/unit/test_synthesis.py`
- [X] T018 [P] [US2] Validation test for H=0.5 baseline (10k trials) in `tests/unit/test_validation.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `src/synthesis/generators.py` to generate fractional Gaussian noise (fGn) and ARFIMA processes with H ∈ {0.5, 0.7, 0.8, 0.9} and **N ∈ {100, 500, 1k, 5k, 10k}** (N-variation grid). Lengths must be ≥ 1,000 for the 1k, 5k, 10k sets.
- [X] T020 [P] [US2] Implement `src/synthesis/generators.py` to compute theoretical VIF and N_eff for generated synthetic series.
- [X] T021 [US2] Implement `src/synthesis/generators.py` shuffling module: Generate [deferred] shuffled (permuted) versions of **every** series (real and synthetic) to create a specific null distribution.
- [X] T022 [US2] Implement `src/synthesis/validation.py` to verify baseline validity: {{claim:c_f3549a67}}. **Block further analysis if this fails.**
- [X] T023 [P] [US2] Implement `src/data/metrics.py` to compute ACF (lag 20), Hurst exponent (DFA), and spectral density peak ratio for **every SYNTHETIC series** generated in T019. (Dependency: T019).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hypothesis Testing and Error Rate Analysis (Priority: P3)

**Goal**: Apply t-tests/F-tests to synthetic/real data, calculate Type I error rates, and regress against Hurst exponent.

**Independent Test**: {{claim:c_b2dbb2ba}}.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for one-sample t-test application in `tests/unit/test_hypothesis.py`
- [X] T025 [P] [US3] Unit test for regression model constraints (exclude Max_ACF_Lag1) in `tests/unit/test_regression.py`

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `src/analysis/hypothesis_tests.py` one-sample t-test and F-test logic. **Explicitly exclude** two-sample t-test.
- [ ] T027 [US3] Implement `src/analysis/hypothesis_tests.py` Monte Carlo loop: Apply tests to synthetic series (H ∈ {, 0.7, 0.8, 0.9}, N ∈ {100, 500, 1k, 5k, 10k}) and real processed series. Calculate observed rejection rate at α=0.05.
- [ ] T028 [US3] Implement `src/analysis/regression.py` to regress observed error rates against **true/estimated Hurst exponent (H) AND log(N_eff)**, including an **interaction term**. **Must** calculate VIF and N_eff. **Must NOT** use Max_ACF_Lag1 or spectral density as predictors.
- [ ] T029 [US3] Implement logic in `src/analysis/hypothesis_tests.py` to compare observed test statistics on **both real and synthetic series** against the null distribution generated from [deferred] shuffled versions (T021) to isolate inflation.
- [ ] T030 [P] [US3] Implement `src/viz/plots.py` to generate: ACF plots, scatter plots (rejection rate vs. Hurst) **with regression lines and confidence intervals**, QQ-plots of test statistics, and **VIF curves**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031a [P] Update `README.md` with installation steps, project structure, and execution commands
- [ ] T031b [P] Update `docs/quickstart.md` with pipeline usage and examples
- [ ] T032 Code cleanup and refactoring across `src/`
- [ ] T033 Performance optimization: Ensure full pipeline (ingestion, 10k trials, regression) completes in ≤ 6 hours on GitHub Actions free tier. [UNRESOLVED-CLAIM: c_8ab7e524 — status=not_enough_info]
- [ ] T034 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
Task: "Unit test for missing value interpolation in tests/unit/test_preprocessing.py"
Task: "Unit test for ADF stationarity loop in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingestion.py to download/cache 5+ datasets"
Task: "Implement src/data/preprocessing.py missing value handler"
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