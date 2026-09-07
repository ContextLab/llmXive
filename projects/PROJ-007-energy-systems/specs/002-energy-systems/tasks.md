# Tasks: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

**Input**: Design documents from `/specs/001-gene-regulation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, statsmodels, censusdata, matplotlib, seaborn, pyyaml, pydantic)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Set up `pytest` configuration and `.gitignore` for data artifacts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `src/models/schemas.py` with Pydantic models for `Household`, `MatchedPair`, and `AnalysisResult`
- [X] T006 [P] Create `src/utils/logging.py` with structured logging and seed setting (numpy, pandas, sklearn)
- [X] T007 [P] Implement `src/config.yaml` for seeds, paths, and thresholds (calipers, SMD limits)
- [X] T008 [P] Create `src/data/ingest.py` with function signatures `fetch_eia_rec(url: str) -> pd.DataFrame` and `fetch_acs(tract_id: str) -> pd.DataFrame`; implement stubs that raise `NotImplementedError` with clear docstrings
- [X] T009 [P] Create `src/data/preprocess.py` with function signatures `filter_low_income(df: pd.DataFrame) -> pd.DataFrame`, `winsorize(df: pd.DataFrame, lower: float, upper: float) -> pd.DataFrame`, and `construct_treatment(df: pd.DataFrame) -> pd.DataFrame`; implement stubs that raise `NotImplementedError`
- [X] T010 [P] Create `src/analysis/psm.py` with function signatures `estimate_propensity(df: pd.DataFrame) -> pd.DataFrame` and `match_pairs(df: pd.DataFrame, caliper: float) -> pd.DataFrame`; implement stubs that raise `NotImplementedError`
- [X] T011 [P] Create `src/analysis/balance.py` with function signatures `calculate_smd(df: pd.DataFrame) -> dict` and `plot_balance(smd_data: dict) -> matplotlib.figure.Figure`; implement stubs that raise `NotImplementedError`
- [X] T012 [P] Create `src/analysis/causal.py` with function signatures `run_ols(df: pd.DataFrame) -> statsmodels.regression.linear_model.RegressionResults` and `run_did(df: pd.DataFrame) -> statsmodels.regression.linear_model.RegressionResults`; implement stubs that raise `NotImplementedError`
- [X] T013 [P] Create `src/analysis/sensitivity.py` with function signature `sweep_caliper(df: pd.DataFrame, calipers: list) -> dict`; implement stubs that raise `NotImplementedError`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Definition (Priority: P1) 🎯 MVP

**Goal**: Ingest public microdata (EIA RECS and ACS), filter for low-income census tracts, and construct treatment/outcome variables.

**Independent Test**: Can be fully tested by running the data pipeline on a sample subset and verifying that the resulting dataset contains exactly the required columns (including socioeconomic proxies), correct binary treatment flags, and that low-income filtering criteria are applied as defined (income < 150% of federal poverty line).

### Implementation for User Story 1

- [X] T015 [US1] Implement `src/data/ingest.py` to fetch EIA RECS from official URL and ACS data via `censusdata` API; fail loudly if required columns (income, energy_cost, solar_installation, location) are missing
- [X] T016 [US1] Implement `src/data/preprocess.py` to filter households in census tracts with median income < 150% of FPL, construct binary `treatment` variable (1 if solar/microgrid, 0 otherwise), and calculate `energy_cost_burden` (cost/income) and `home_value_change`
- [X] T017 [US1] Implement winsorization logic in `src/data/preprocess.py` to handle zero energy costs and outliers (1st/99th percentile) before regression
- [X] T018 [US1] Implement power check in `src/data/preprocess.py` to halt and report if < 50 adopters remain after filtering; raise `PowerError: Insufficient adopters (<50)` if threshold not met
- [X] T050 [US1] Implement missing value handling in `src/data/preprocess.py`: use Median Imputation for continuous variables (income, cost) and a 'Missing' flag category for categorical variables; verify no silent data loss
- [X] T020 [US1] Create `tests/integration/test_ingestion.py` to verify schema validation, column presence, and low-income filtering logic
- [X] T021 [US1] Create `tests/unit/test_preprocess.py` to verify treatment construction, winsorization, and missing value handling logic

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Propensity Score Matching and Balance Validation (Priority: P2)

**Goal**: Implement PSM to create a balanced control group, validate covariate balance (SMD <= 0.1), and perform a placebo test.

**Independent Test**: Can be fully tested by running the PSM algorithm on the ingested dataset, extracting the matched pairs, and calculating the standardized mean difference (SMD) for all covariates. A pass is achieved if all SMDs are <= 0.1. Additionally, a placebo test on a pre-treatment outcome must yield a non-significant difference between treatment and control groups.

### Implementation for User Story 2

- [X] T022 [US2] Implement `src/analysis/psm.py` to estimate propensity scores using logistic regression with covariates (income, housing type, location) and perform nearest neighbor matching with a caliper
- [X] T052 [US2] Implement common support check in `src/analysis/psm.py` (after score calculation) to flag/exclude observations with extreme propensity scores (near 0 or 1)
- [X] T023 [US2] Implement `src/analysis/balance.py` to calculate SMD for all matching variables and generate balance plots (love plot)
- [X] T024 [US2] Implement iterative adjustment loop in `src/analysis/psm.py`: if SMD > 0.1, reduce caliper by 0.01 per iteration; if caliper < 0.01, remove lowest-weight covariate and retry; terminate after a maximum of a limited number of attempts; if still failing, set `balance_status` flag to trigger DiD fallback
- [X] T025 [US2] Implement placebo test logic in `src/analysis/balance.py` to check for significant differences in pre-treatment outcomes between matched groups
- [ ] T046 [US2] Implement pipeline execution for placebo test: execute test in main flow, report p-value and pass/fail status, and gate causal estimation (trigger fallback/halt if significant)
- [X] T026 [US2] Create `tests/unit/test_psm.py` to verify matching logic, caliper enforcement, and SMD calculation
- [X] T027 [US2] Create `tests/unit/test_balance.py` to verify SMD thresholds, placebo test significance logic, and DiD trigger logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Causal Effect Estimation and Sensitivity Analysis (Priority: P3)

**Goal**: Estimate ATT using OLS (or DiD fallback), perform sensitivity analysis by sweeping calipers, and generate final results.

**Independent Test**: Can be fully tested by executing the regression (or DiD) and sensitivity sweep, then verifying that the output includes the ATT estimate, p-values, confidence intervals, and a table showing how the ATT changes across the different caliper values. The test passes if the system outputs a valid estimate regardless of statistical significance.

### Implementation for User Story 3

- [X] T054 [US3] Implement DiD fallback logic in `src/analysis/causal.py`: FIRST perform 'Longitudinal Data Availability Check' by verifying presence of `pre_treatment_outcome` and `post_treatment_outcome` columns; if missing, raise `DataUnavailableError: Longitudinal data required for DiD but columns missing`; if present AND PSM balance failed, execute DiD; otherwise skip
- [X] T028 [US3] Implement `src/analysis/causal.py` to run OLS regression with cluster-robust standard errors (clustered by matched pair) on `log(energy_cost)` as the primary outcome
- [ ] T053 [US3] Implement control flow logic to consume `balance_status` flag from Phase 4 and conditionally trigger T054 (DiD) or proceed to T028 (OLS); if DiD is triggered but data is missing, trigger the specific error path defined in T054
- [X] T030 [US3] Implement `src/analysis/sensitivity.py` to sweep calipers over a range of small values by calling reusable functions from T022 and T028; compile ATT estimates, p-values, and confidence intervals
- [ ] T031 [US3] Implement result serialization in `src/models/output.py` to save `AnalysisResult` objects (ATT, p-value, CI, methodology, sensitivity data) to JSON/Parquet
- [X] T032 [US3] Create `tests/integration/test_pipeline.py` to verify end-to-end flow from ingestion to sensitivity report generation
- [ ] T033 [US3] Create `tests/unit/test_causal.py` to verify OLS and DiD estimation logic and cluster-robust standard errors

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Scaling Law Analysis (Reviewer: Geoffrey West)

**Goal**: Address reviewer concerns by implementing a descriptive scaling law module to investigate how energy consumption scales with population in low-income communities, explicitly excluded from causal claims. This addresses the specific critique that "a theory without a scaling law is just a story" and "find the exponent" to locate inequity.

**Independent Test**: Can be tested by running the scaling analysis on tract-level aggregates and verifying that the output includes the scaling exponent (beta) and its confidence interval, and that it is clearly labeled as descriptive (not causal).

### Implementation for Scaling Analysis

- [X] T014 [P] Create `src/scaling/scaling.py` with function signatures `aggregate_tract(df: pd.DataFrame) -> pd.DataFrame` and `fit_scaling_law(df: pd.DataFrame) -> float`; implement stubs that raise `NotImplementedError`
- [X] T034 [P] Implement `src/scaling/scaling.py` to aggregate household data to census tract level (consuming final validated output of T016), calculating total energy consumption and population size
- [X] T035 [P] Implement power-law regression in `src/scaling/scaling.py` to estimate the scaling exponent (beta) for energy consumption vs. population (log-log regression)
- [X] T036 [P] Implement logic in `src/scaling/scaling.py` to compare the estimated beta against the universal sublinear scaling exponent observed in cities (Bettencourt et al.)
- [X] T037 [P] Generate a descriptive report in `src/scaling/scaling.py` that explicitly states the scaling law is for descriptive purposes only and does not support causal claims about energy inequity; strictly forbid any language framing scaling gaps as "inequity signals" or causal impacts
- [ ] T051 [P] Implement report generator logic to enforce strict structural separation: create distinct functions for causal vs. descriptive sections; ensure scaling results are generated separately and excluded from the causal claims block in the final report
- [ ] T038 [P] Create `tests/unit/test_scaling.py` to verify power-law regression logic and exponent calculation
- [ ] T039 [P] Add a section to the final report (via `main.py` or a dedicated reporter) that presents the scaling law findings separately from the causal inference results, with clear disclaimers
- [ ] T060 [P] Implement `src/scaling/inequity_gap.py` to calculate the "scaling gap": the difference between observed energy consumption in low-income tracts and the consumption predicted by the universal scaling law (beta), explicitly framing this as a descriptive metric of deviation, not a causal treatment effect
- [ ] T061 [P] Create `tests/unit/test_inequity_gap.py` to verify the calculation of the scaling gap and ensure it is mathematically distinct from the causal ATT estimate
- [ ] T062 [P] Update `src/scaling/scaling.py` to generate a visualization (log-log plot) showing the universal scaling line vs. the low-income community data points, with the gap highlighted, ensuring the visual clearly distinguishes between the "law" and the "deviation"

**Checkpoint**: Scaling law analysis is complete and integrated, addressing reviewer concerns without compromising causal rigor.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates: Update `quickstart.md` with instructions for running the full pipeline, including the scaling law module
- [ ] T041 [P] Code cleanup: Move seed setting logic from `src/utils/logging.py` to `src/utils/seed.py`; verify `src/utils/seed.py` exists and is imported in `main.py`
- [ ] T043 [P] Run `quickstart.md` validation to ensure all steps execute successfully
- [ ] T044 [P] Security hardening: Integrate PII scanner script into CI pipeline; verify CI job fails if PII is detected in `data/processed/`
- [ ] T045 [P] Final report generation: Create a comprehensive report that includes causal inference results, sensitivity analysis, and the descriptive scaling law findings, with clear separation of methodologies
- [ ] T063 [P] Update `README.md` and `docs/architecture.md` to explicitly document the separation between the causal inference pipeline (US1-3) and the descriptive scaling law pipeline (Phase 6), citing the Geoffrey West review as the rationale for this architectural separation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Scaling Analysis (Phase 6)**: Depends on Foundational phase completion (can run in parallel with US1-3)
- **Polish (Phase 7)**: Depends on all desired user stories and scaling analysis being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 matched data output
- **Scaling Analysis (Phase 6)**: Can start after Foundational (Phase 2) - Depends on US1 data output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories and scaling analysis can start in parallel (if team capacity allows)
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
5. Add Scaling Analysis → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Scaling Analysis
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
- **Crucial**: The scaling law module (Phase 6) is strictly descriptive and must not be conflated with the causal inference results in the final report. The module explicitly avoids framing scaling gaps as causal 'inequity signals'.
- **Critical**: If PSM fails and longitudinal data is missing, the system must halt with a clear error message rather than attempting an impossible DiD calculation.
- **Reviewer Response (Geoffrey West)**: The new tasks in Phase 6 (T060, T061, T062, T063) specifically address the critique that "a theory without a scaling law is just a story." They implement the "find the exponent" directive by calculating the scaling gap as a descriptive metric, strictly separated from the causal ATT estimate.
