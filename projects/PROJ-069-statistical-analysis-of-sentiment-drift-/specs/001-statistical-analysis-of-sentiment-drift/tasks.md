# Tasks: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Input**: Design documents from `/specs/001-sentiment-drift/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/`, `artifacts/` at repository root
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

- [ ] T001 [P] Initialize project directory structure (`code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `results/`, `tests/`, `artifacts/`, `docs/`)
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

**Goal**: Ingest historical sentiment and macroeconomic data, align to quarterly frequency, and handle missing data via documented interpolation.

**Independent Test**: Run `code/data_ingestion.py` and `code/preprocessing.py` to verify `data/processed/aligned_quarterly.csv` exists with quarterly timestamps, ≤5% missing rate (flagged otherwise), and valid sentiment polarity ratios.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Contract test for `aligned_quarterly.csv` schema in `tests/contract/test_timeseries_schema.py`
- [ ] T013 [P] [US1] Integration test for data alignment logic in `tests/integration/test_data_alignment.py`
- [ ] T021 [P] [US1] Unit tests for interpolation methods (forward-fill vs linear) in `tests/unit/test_interpolation.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement FRED data fetcher in `code/data_ingestion.py` to download GDP (`FRED/GDP`), UNRATE (`FRED/UNRATE`), and Consumer Confidence (`FRED/UMCSENT`); handle partial data with forward-fill and flag affected periods as per FR-008
- [ ] T015 [US1] Implement HuggingFace sentiment fetcher in `code/data_ingestion.py` to download `snap-cornell/twitter-roberta-base-sentiment-dataset` and aggregate to quarterly time series using `datasets.load_dataset`
- [ ] T016 [US1] Implement quarterly alignment logic in `code/preprocessing.py` (resample daily sentiment to quarterly averages; interpolate quarterly macro data)
- [ ] T017 [US1] Implement missing data rate calculation and flagging logic (exclude periods >5% missing) in `code/preprocessing.py`
- [ ] T018 [US1] Implement sentiment noise reduction (rolling average) in `code/preprocessing.py`
- [ ] T019 [US1] Implement low-confidence flagging (confidence <0.7 or sample size <100) in `code/preprocessing.py`
- [ ] T020 [US1] Generate `data/processed/aligned_quarterly.csv` and `data/processed/data_quality_log.json` (logging method and % affected per variable)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling, Stationarity Testing, Causal Inference & Validation (Priority: P2)

**Goal**: Execute stationarity tests, select optimal lags, run Granger causality tests, and perform robustness/out-of-sample validation.

**Independent Test**: Run `code/modeling.py` and `code/validation.py` to verify `results/model_stats.json`, `results/validation_stats.json`, and `results/holdout_validation.json` contain all required p-values, statistics, and verification metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Contract test for `model_stats.json` schema in `tests/contract/test_model_results_schema.py`
- [ ] T023 [P] [US2] Integration test for Granger causality logic in `tests/integration/test_granger_causality.py`
- [ ] T031 [P] [US2] Unit tests for ADF and Johansen test logic in `tests/unit/test_stationarity.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement Augmented Dickey-Fuller (ADF) test runner in `code/modeling.py` with fallback transformations (log/Box-Cox) for non-stationary series
- [ ] T025 [US2] Implement Johansen Cointegration Test and Model Selection in `code/modeling.py`. **Logic**: Run Johansen test; if Trace and Max-Eigenvalue statistics conflict (Trace suggests rank X, Max-Eigen suggests rank Y), prioritize the Trace statistic **UNLESS** the Max-Eigenvalue statistic exceeds its critical value by >10%. If a conflict occurs AND Max-Eigenvalue exceeds the threshold by >10%, **re-evaluate lag order by incrementally increasing lag (up to a predefined maximum lag) and re-run the test** until a consistent rank is found or max lag is reached. Select the model type (VAR if not cointegrated, VECM if cointegrated) **atomically** within the script without intermediate file writes. **Output**: Write test statistics, p-values, cointegration rank, selected model type, and any lag re-evaluation steps directly to `results/model_stats.json`. (As per Plan.md Phase 1 Step 1.3)
- [ ] T026 [US2] Implement VAR/VECM model fitting with AIC-based optimal lag selection in `code/modeling.py` (Uses model type determined in T025)
- [ ] T027 [US2] Implement Granger Causality F-test runner in `code/modeling.py` for Sentiment → GDP/Unemployment/ConsumerConfidence and reverse directions
- [ ] T028 [US2] Implement collinearity diagnostic (Variance Inflation Factor) for GDP vs Unemployment in `code/modeling.py`. **Action**: If high collinearity is detected (VIF > 10), log the VIF and explicitly **frame results as a joint relationship** rather than independent effects in the final output, as per spec Edge Cases.
- [ ] T030 [US2] Generate `results/model_stats.json` with p-values, F-statistics, and lag lengths (Updated by T025/T026)
- [ ] T034 [US2] Implement Moving Block Bootstrap (MBB) with block length = **1 quarter** in `code/validation.py`; **Logic**: Since the input data (`aligned_quarterly.csv`) is aggregated to quarterly frequency, the '4-week' requirement from FR-006/SC-004 is mapped to the data resolution as 1 data point (1 quarter). The MBB must use a block length of a quarter. to represent the 4-week window on the quarterly time scale. Calculate 95% CI; verify CI width ≤20% of original OLS coefficient and convergence (width stable <1% for 3 runs). **Output**: Generate `results/validation_stats.json` containing CI arrays, convergence flag, and verification status.
- [ ] T035 [US2] Implement sensitivity analysis scaffolding in `code/validation.py` (prepare logic for masking/re-interpolation)
- [ ] T050 [US2] Execute sensitivity analysis in `code/validation.py` using masking proportions **[deferred], [deferred], and [deferred]** (as defined in T052); re-interpolate masked data, re-run VAR/VECM for each proportion, and generate `results/validation_stats.json` reporting absolute p-value shifts for each specific proportion (must be <0.01)
- [ ] T036a [US2] Fetch/define recession periods for major economic downturns from NBER using the canonical URL `https://www.nber.org/business-cycle-dating/dates.csv`; if fetch fails, fallback to a hardcoded dataset of major recessions (e.g., the late 2000s); generate `data/metadata/recession_periods.json` with explicit start/end dates.
- [ ] T036 [US2] Implement out-of-sample validation using periods in `data/metadata/recession_periods.json`; hold out representative historical and recent quarters, re-fit model, forecast, and generate `results/holdout_validation.json` with RMSE and consistency metrics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, including all validation steps

---

## Phase 5: User Story 3 - Visualization, Robustness Validation, and Reporting (Priority: P3)

**Goal**: Visualize temporal relationships with recession shading and generate final report artifacts.

**Independent Test**: Generate `artifacts/figures/` and `analysis_notebook.ipynb` and verify recession shading, MBB confidence intervals, and sensitivity analysis report are included.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Contract test for `validation_stats.json` schema in `tests/contract/test_robustness_schema.py`
- [ ] T033 [P] [US3] Integration test for MBB and sensitivity analysis in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T038 [US3] Implement time-series visualization with NBER recession shading in `code/visualization.py` using `data/metadata/recession_periods.json`
- [ ] T039 [US3] Implement impulse response functions (IRFs) and cross-correlation heatmaps in `code/visualization.py`
- [ ] T040 [US3] Generate `artifacts/figures/` (PDF/PNG) with all required annotations and metadata
- [ ] T041 [US3] Assemble `analysis_notebook.ipynb` with embedded code, outputs, and narrative text (FR-007); include dataset URLs and DOIs in metadata
- [ ] T042 [US3] Update `state/projects/...yaml` via `update_state.py` with final artifact hashes
- [ ] T043b [US3] Implement concordance score calculation in `code/validation.py` to compute the **percentage of recessions where peak sentiment occurs ≤ 1 quarter before onset** (FR-014) and report in `results/validation_stats.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` (including dataset URLs and DOIs in metadata)
- [ ] T044 Code cleanup and refactoring for performance on CPU-only CI
- [ ] T045 Performance optimization (ensure full pipeline runs <4 hours on CPU/7GB RAM)
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

- **T025 -> T026**: T025 (Johansen Test) **atomically** determines the model type (VAR vs VECM) and writes it to `model_stats.json`. T026 (Model Fitting) reads this decision directly from the in-memory logic or the same artifact to fit the correct model. No intermediate temp files or manual steps.
- **T036a -> T036**: T036a must produce `recession_periods.json` containing BOTH 2008 and 2020 periods from the canonical CSV. T036 iterates over this list. **Dependency**: T036 explicitly depends on T036a completion.
- **T034**: Calculates CI width and verifies against the 20% threshold defined in SC-004.
- **T052 (Implicit)**: The masking proportions ([deferred], [deferred], [deferred]) are now defined in T052 description and T050 execution logic. T050 must iterate over these specific values.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for aligned_quarterly.csv schema in tests/contract/test_timeseries_schema.py"
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
- **Feasibility Note**: All tasks are designed for CPU-only execution (A minimal computational configuration (e.g., a few cores, several GB of RAM) will be used.). No GPU models or large-scale training are included.
- **Data Integrity**: All data sources are real (FRED API, HuggingFace datasets, NBER). No synthetic data generation is used for primary analysis.
- **Sensitivity Analysis**: T052 defines discrete masking proportions ([deferred], [deferred], [deferred]) to be iterated over by T050, ensuring SC-006 is met with specific p-value shift reports.
- **MBB Block Length Note**: Task T034 correctly maps the '4-week' spec requirement to the quarterly data frequency by using a block length of 1 quarter. This ensures statistical validity on the `aligned_quarterly.csv` input.