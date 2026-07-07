# Tasks: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Input**: Design documents from `/specs/001-sentiment-drift/`
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

- [ ] T001a Create `code/` directory
- [ ] T001b Create `data/raw/` directory
- [ ] T001c Create `data/processed/` directory
- [ ] T001d Create `data/metadata/` directory
- [ ] T001e Create `tests/` directory
- [ ] T001f Create `artifacts/` directory
- [ ] T001g Initialize configuration files (`.gitignore`, `pyproject.toml` scaffolding)
- [ ] T002 Create `code/requirements.txt` with pinned dependencies (pandas, numpy, statsmodels, scikit-learn, matplotlib, seaborn, requests, huggingface_hub, fredapi, responses, pytest, nbval)
- [ ] T002b Initialize Python 3.11 virtualenv and install dependencies
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T005 [P] Create base schema definitions in `code/contracts/` for `TimeSeries`, `ModelResult`, and `RecessionPeriod`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/update_state.py` to automatically update `state/projects/...yaml` with artifact hashes for `data/raw/`, `data/processed/`, `data/metadata/`, and `code/` using SHA-256
- [ ] T006 [P] Setup environment configuration management (`.env` handling for FRED API keys, HF token)
- [ ] T007 Create `code/data_ingestion.py` skeleton with FRED and HuggingFace client wrappers
- [ ] T008 Create `code/preprocessing.py` skeleton for interpolation logic and stationarity checks
- [ ] T009 Create `code/modeling.py` skeleton for ADF, Johansen, VAR, and Granger tests
- [ ] T010 [P] Create `code/validation.py` skeleton for MBB and sensitivity analysis
- [ ] T011 [P] Create `code/visualization.py` skeleton for NBER-shaded plots

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Alignment, and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest historical sentiment and macroeconomic data, align to weekly frequency, and handle missing data via documented interpolation.

**Independent Test**: Run `code/data_ingestion.py` and `code/preprocessing.py` to verify `data/processed/merged_timeseries.csv` exists with weekly timestamps, ≤5% missing rate (flagged otherwise), and valid sentiment polarity ratios.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Contract test for `merged_timeseries.csv` schema in `tests/contract/test_timeseries_schema.py`
- [ ] T013 [P] [US1] Integration test for data alignment logic in `tests/integration/test_data_alignment.py`
- [ ] T021 [P] [US1] Unit tests for interpolation methods (forward-fill vs linear) in `tests/unit/test_interpolation.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement FRED data fetcher in `code/data_ingestion.py` to download GDP, UNRATE, VIXCLS (handle partial data with forward-fill with lag awareness AND flag affected periods as per FR-008)
- [ ] T015 [US1] Implement HuggingFace sentiment fetcher in `code/data_ingestion.py` to download `cardiffnlp/twitter-roberta-base-sentiment` data and aggregate to weekly time series
- [ ] T016 [US1] Implement weekly alignment logic in `code/preprocessing.py` (forward-fill for quarterly GDP/Unemployment, linear interpolation for sentiment)
- [ ] T017 [US1] Implement missing data rate calculation and flagging logic (exclude periods >5% missing) in `code/preprocessing.py`
- [ ] T018 [US1] Implement 7-day rolling average for sentiment noise reduction in `code/preprocessing.py`
- [ ] T019 [US1] Implement low-confidence flagging (confidence <0.7 or sample size <100) in `code/preprocessing.py`
- [ ] T020 [US1] Generate `data/processed/merged_timeseries.csv` and `data/processed/imputation_log.json` (logging method and % affected per variable)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling, Stationarity Testing, Causal Inference & Validation (Priority: P2)

**Goal**: Execute stationarity tests, select optimal lags, run Granger causality tests, and perform robustness/out-of-sample validation.

**Independent Test**: Run `code/modeling.py` and `code/validation.py` to verify `data/processed/model_results.json`, `data/processed/robustness_report.json`, and `data/processed/holdout_validation.json` contain all required p-values, statistics, and verification metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Contract test for `model_results.json` schema in `tests/contract/test_model_results_schema.py`
- [ ] T023 [P] [US2] Integration test for Granger causality logic in `tests/integration/test_granger_causality.py`
- [ ] T031 [P] [US2] Unit tests for ADF and Johansen test logic in `tests/unit/test_stationarity.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement Augmented Dickey-Fuller (ADF) test runner in `code/modeling.py` with fallback transformations (log/Box-Cox) for non-stationary series
- [ ] T025 [US2] Implement Johansen Cointegration Test in `code/modeling.py` to determine VAR vs VECM path; **Output**: Write test statistics, p-values, and cointegration rank to a temporary artifact `data/processed/johansen_temp.json` for downstream decision logic. (As per Plan.md Phase 1)
- [ ] T029 [US2] Generate `data/processed/model_spec.json` by reading `data/processed/johansen_temp.json` from T025; explicitly write decision logic (VAR if not cointegrated, VECM if cointegrated, default to VAR if inconclusive) to the artifact, including the specific test statistics and p-values that drove the decision
- [ ] T026 [US2] Implement VAR/VECM model fitting with AIC-based optimal lag selection in `code/modeling.py` (Conditional on T029 model_spec.json)
- [ ] T027 [US2] Implement Granger Causality F-test runner in `code/modeling.py` for Sentiment → GDP/Unemployment and vice versa
- [ ] T028 [US2] Implement collinearity diagnostic (Variance Inflation Factor) for GDP vs Unemployment in `code/modeling.py`
- [ ] T030 [US2] Generate `data/processed/model_results.json` with p-values, F-statistics, and lag lengths
- [ ] T034 [US2] Implement Moving Block Bootstrap (MBB) with data-driven block length (Politis & White) in `code/validation.py`; **Logic**: Read `data_source` flag from `data/metadata/data_source.json`. If 'synthetic', skip strict CI width threshold verification or log a warning. If 'real', calculate CI width ratio and verify it is ≤20% of the original OLS coefficient. **Output**: Generate `data/processed/mbb_metrics.json` containing CI width, OLS coefficient, ratio, and verification status. (Merged verification logic from T051)
- [ ] T052 [US2] Define masking proportion for sensitivity analysis in `data/metadata/sensitivity_config.json` by resolving '[deferred]' placeholders to a concrete percentage range (default a low to moderate percentage) and logging the exact value used.
- [ ] T035 [US2] Implement sensitivity analysis scaffolding in `code/validation.py` (Scaffolding only: no execution, prepare logic for masking/re-interpolation)
- [ ] T050 [US2] Execute sensitivity analysis in `code/validation.py` using T052 proportion; generate `data/processed/sensitivity_shift_log.json` reporting p-value shifts
- [ ] T036a [US2] Fetch/define recession periods for major economic downturns from the NBER API (or verified static list if API unavailable); generate `data/metadata/recession_periods.json` with explicit start/end dates for both 2008 and 2020 periods in a schema-compliant format
- [ ] T036 [US2] Implement out-of-sample validation using the periods defined in `data/metadata/recession_periods.json`; iterate over each period; verify period correspondence; generate `data/processed/holdout_validation.json` with p-value comparison against training set

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, including all validation steps

---

## Phase 5: User Story 3 - Visualization, Robustness Validation, and Reporting (Priority: P3)

**Goal**: Visualize temporal relationships with recession shading and generate final report artifacts.

**Independent Test**: Generate `artifacts/figures/` and `analysis_notebook.ipynb` and verify recession shading, MBB confidence intervals, and sensitivity analysis report are included.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Contract test for `robustness_report.json` schema in `tests/contract/test_robustness_schema.py`
- [ ] T033 [P] [US3] Integration test for MBB and sensitivity analysis in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T038 [US3] Implement time-series visualization with NBER recession shading in `code/visualization.py`
- [ ] T039 [US3] Implement impulse response functions and cross-correlation heatmaps in `code/visualization.py`
- [ ] T040 [US3] Generate `artifacts/figures/` (PDF/PNG) with all required annotations
- [ ] T041 [US3] Assemble `analysis_notebook.ipynb` with embedded code, outputs, and narrative text (FR-007)
- [ ] T042 [US3] Update `state/projects/...yaml` via `update_state.py` with final artifact hashes

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` (including dataset URLs and DOIs in metadata)
- [ ] T044 Code cleanup and refactoring for performance on CPU-only CI
- [ ] T045 Performance optimization (ensure full pipeline runs <4 hours on 2 CPU/7GB RAM)
- [ ] T046 [P] Additional unit tests for edge cases (API failures, non-stationary fallbacks) in `tests/unit/`
- [ ] T047 Run `quickstart.md` validation to ensure reproducibility from scratch

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: 
  - **Phase 3 (US1)**: Depends on Foundational (Phase 2)
  - **Phase 4 (US2)**: Depends on **Phase 3 (US1) completion** and Foundational (Phase 2) - Data must be clean before modeling
  - **Phase 5 (US3)**: Depends on Phase 4 (US2) completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetching before alignment
- Alignment before modeling
- Modeling before validation/visualization
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Conditional Flows & Decision Gates

- **T025 -> T029 -> T026**: T025 (Johansen Test) results are written to `data/processed/johansen_temp.json`. T029 reads this file and writes the decision (VAR vs VECM) to `model_spec.json`. T026 (Model Fitting) is **conditional** on T029's output; it must check `model_spec.json` to determine which model to fit.
- **T036a -> T036**: T036a must produce `recession_periods.json` containing BOTH 2008 and 2020 periods. T036 iterates over this list. **Dependency**: T036 explicitly depends on T036a completion.
- **T034**: Reads `data/metadata/data_source.json` to determine if robustness checks should be strict (real data) or lenient (synthetic data).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for merged_timeseries.csv schema in tests/contract/test_timeseries_schema.py"
Task: "Integration test for data alignment logic in tests/integration/test_data_alignment.py"
Task: "Unit tests for interpolation methods in tests/unit/test_interpolation.py"

# Launch all models for User Story 1 together:
Task: "Implement FRED data fetcher in code/data_ingestion.py"
Task: "Implement HuggingFace sentiment fetcher in code/data_ingestion.py"
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
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Modeling & Validation)
   - Developer C: User Story 3 (Visualization)
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