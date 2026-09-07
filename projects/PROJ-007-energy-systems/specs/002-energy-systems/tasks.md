# Tasks: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

**Input**: Design documents from `/specs/002-energy-systems/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and security enforcement.

- [X] T001 Create project structure: `mkdir -p src/data src/analysis src/utils src/models tests/unit tests/integration data/raw data/processed data/outputs specs/`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Add `pyproject.toml` sections for ruff/black and create `.ruff.toml`
- [X] T004 [P] Set up `pytest` configuration: Create `pytest.ini` and `.gitignore` entries for `data/` and `__pycache__/`
- [X] T044 [P] Security hardening: **Deliverable**: Create `.github/workflows/ci.yml` with a job `security-scan` that runs `detect-secrets scan --baseline .secrets.baseline` on `data/` and `src/`, AND generate the initial `.secrets.baseline` file. The workflow must fail the build if PII is detected. This task MUST be completed before any data ingestion tasks to satisfy Constitution Principle III.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `src/models/schemas.py` with Pydantic models for `Household`, `MatchedPair`, and `AnalysisResult`
- [X] T006 [P] Create `src/utils/logging.py` with structured logging and seed setting (numpy, pandas, sklearn). **Note**: All random seeds MUST be pinned here to satisfy Constitution Principle I.
- [X] T007 [P] Implement `src/config.yaml` for seeds, paths, and thresholds (calipers: precise measurement capability, SMD limits: small effect sizes). **Note**: Only spec-defined thresholds are included. No scaling thresholds.
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

- [X] T015 [US1] Implement `src/data/ingest.py` to fetch EIA RECS from official URL and ACS data via `censusdata` API; fail loudly if required columns (income, energy_cost, solar_installation, location) are missing. Ensure API calls target US-specific endpoints.
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
- [X] T024a [US2] Implement Caliper Reduction Logic in `src/analysis/psm.py`: if SMD > 0.1, reduce caliper by a small, fixed increment per iteration and retry matching.
- [X] T024b [US2] Implement Covariate Pruning Logic in `src/analysis/psm.py`: if caliper < 0.01 and SMD > 0.1, remove the lowest-weight covariate and retry.
- [X] T024c [US2] Implement Status Flagging in `src/analysis/psm.py`: set `balance_status` flag to `FAIL` if max attempts exceeded, otherwise `PASS`. This flag is consumed by T053.
- [X] T025 [US2] Implement placebo test logic in `src/analysis/balance.py` to check for significant differences in pre-treatment outcomes between matched groups
- [X] T046 [US2] Implement `src/analysis/balance.py` function `run_placebo_gate(df: pd.DataFrame) -> bool`: execute placebo test on pre-treatment outcome; return False if p-value < 0.05 (signaling unconfoundedness failure); this function gates causal estimation in the main pipeline and its result is integrated into the `balance_status` logic in T024a-T024c.
- [X] T026 [US2] Create `tests/unit/test_psm.py` to verify matching logic, caliper enforcement, and SMD calculation
- [X] T027 [US2] Create `tests/unit/test_balance.py` to verify SMD thresholds, placebo test significance logic, and DiD trigger logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Causal Effect Estimation and Sensitivity Analysis (Priority: P3)

**Goal**: Estimate ATT using OLS (or DiD fallback), perform sensitivity analysis by sweeping calipers, and generate final results.

**Independent Test**: Can be fully tested by executing the regression (or DiD) and sensitivity sweep, then verifying that the output includes the ATT estimate, p-values, confidence intervals, and a table showing how the ATT changes across the different caliper values. The test passes if the system outputs a valid estimate regardless of statistical significance.

### Implementation for User Story 3

- [X] T054 [US3] Implement DiD fallback logic in `src/analysis/causal.py`: FIRST perform 'Longitudinal Data Availability Check' by verifying presence of `pre_treatment_outcome` and `post_treatment_outcome` columns. If present AND PSM balance failed, execute DiD; if missing, log a warning `Longitudinal data missing; falling back to OLS` and proceed with OLS estimation (per FR-005) to avoid halting the pipeline.
- [X] T028 [US3] Implement `src/analysis/causal.py` to run OLS regression with cluster-robust standard errors (clustered by matched pair) on `log(energy_cost)` as the primary outcome. **Note**: Model covariates are strictly limited to those defined in FR-003 (income, housing, location).
- [X] T053 [US3] Implement control flow logic in `src/main.py`: add conditional block `if balance_status == FAIL and longitudinal_data_available: run_did(); else: run_ols()`. This task consumes the `balance_status` flag produced by T024a-T024c (which incorporates T046's gate result) to route execution to the `run_did()` function (implemented in T054) or `run_ols()` (implemented in T028).
- [X] T030 [US3] Implement `src/analysis/sensitivity.py` to sweep calipers over a range of small values by calling reusable functions from T022 and T028; compile ATT estimates, p-values, and confidence intervals
- [X] T031 [US3] Implement result serialization in `src/models/output.py`: add method `AnalysisResult.to_json()` to save `AnalysisResult` objects (ATT, p-value, CI, methodology, sensitivity data) to `data/outputs/analysis_result.json`
- [X] T032 [US3] Create `tests/integration/test_pipeline.py` to verify end-to-end flow from ingestion to sensitivity report generation
- [X] T033 [US3] Create `tests/unit/test_causal.py` to verify OLS and DiD estimation logic and cluster-robust standard errors

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates: Update `quickstart.md` with exact commands for running the full causal pipeline (ingest -> match -> estimate -> report) and expected output format. Must document: `python src/main.py --config src/config.yaml` and the expected JSON structure of `data/outputs/analysis_result.json`.
- [X] T043 [P] Run `quickstart.md` validation: Execute the commands documented in T040 and verify that the pipeline completes successfully and produces `data/outputs/analysis_result.json` with valid JSON structure (verified via `python -m json.tool`).
- [X] T045 [P] Final report generation: Create a comprehensive report in `src/reporting/generate_final_report.py` that includes causal inference results and sensitivity analysis, strictly adhering to FR-001 through FR-009.
- [X] T065 [P] Update `README.md` and `docs/architecture.md` to explicitly document the causal inference pipeline (US1-3) and its adherence to FR-001 through FR-009. **Note**: Do NOT include any scaling law sections.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (T044 must complete before data tasks).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 matched data output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T044 which is a prerequisite for data tasks).
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

1. Complete Phase 1: Setup (including T044 Security)
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
- **Critical**: If PSM fails and longitudinal data is missing, the system must log a warning and proceed with OLS (per FR-005) rather than halting, ensuring the pipeline completes.
- **Scope Clarification**: This project strictly adheres to the Functional Requirements in `spec.md` (FR-001 to FR-009) and the Constitution's Causal Identification Rigor (Principle VI). The scope is limited to PSM/DiD causal inference on US EIA RECS/ACS data. Scaling law analysis is explicitly OUT OF SCOPE.
- **Reviewer Action**: Tasks T060, T061, T062, T064, T065 (old), and T066 related to scaling laws have been removed to align with the spec. Task T041 (seed refactoring) has been removed as it was cosmetic. Task T024 has been atomized into T024a, T024b, T024c. Tasks T040, T043, T044 have been made concrete and executable. Task T065 (new) has been updated to strictly document the PSM/DiD pipeline. **Phase 6 (Scaling Law Analysis) has been removed entirely.**