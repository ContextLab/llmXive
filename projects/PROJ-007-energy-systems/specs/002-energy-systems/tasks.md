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
- [X] T044a [P] Security hardening (Workflow): Create `.github/workflows/ci.yml` with a job `security-scan` that runs `detect-secrets scan --baseline.secrets.baseline` on `data/` and `src/`. The workflow must fail the build if PII is detected. This task defines the CI infrastructure. **Implementation**: The file content must match the `plan.md` Phase 0 specification exactly.
- [X] T044b [P] Security hardening (Baseline): Generate the initial `.secrets.baseline` file by running `detect-secrets scan --baseline.secrets.baseline` locally. This task must be completed after T044a to ensure the baseline file exists for the CI workflow to audit. **Implementation**: Execute the command locally and commit the resulting file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `src/models/schemas.py` with Pydantic models for `Household`, `MatchedPair`, and `AnalysisResult`
- [X] T006 [P] Create `src/utils/logging.py` with structured logging and seed setting (numpy, pandas, sklearn). **Note**: All random seeds MUST be pinned here to satisfy Constitution Principle I.
- [X] T007 [P] Implement `src/config.yaml` for seeds, paths, and thresholds (calipers: precise measurement capability, SMD limits: small effect sizes). **Note**: Only spec-defined thresholds are included. No scaling thresholds.
- [X] T008 [P] Create `src/data/ingest.py` with the following function signatures (stubs raising `NotImplementedError`):
 - `def fetch_eia_rec(url: str) -> pd.DataFrame:`
 - `def fetch_acs(tract_id: str) -> pd.DataFrame:`
 - **Docstring requirement**: Must describe expected columns (income, energy_cost, solar_installation, location) and error handling for missing data.
- [X] T009 [P] Create `src/data/preprocess.py` with the following function signatures (stubs raising `NotImplementedError`):
 - `def filter_low_income(df: pd.DataFrame, threshold: float) -> pd.DataFrame:`
 - `def winsorize(df: pd.DataFrame, lower: float, upper: float) -> pd.DataFrame:`
 - `def construct_treatment(df: pd.DataFrame) -> pd.DataFrame:`
 - **Docstring requirement**: Must describe outlier handling (1st/99th percentile) and treatment construction logic.
- [X] T010 [P] Create `src/analysis/psm.py` with the following function signatures (stubs raising `NotImplementedError`):
 - `def estimate_propensity(df: pd.DataFrame, covariates: list) -> pd.DataFrame:`
 - `def match_pairs(df: pd.DataFrame, caliper: float) -> pd.DataFrame:`
 - **Docstring requirement**: Must describe matching algorithm and caliper enforcement.
- [X] T011 [P] Create `src/analysis/balance.py` with the following function signatures (stubs raising `NotImplementedError`):
 - `def calculate_smd(df: pd.DataFrame) -> dict:`
 - `def plot_balance(smd_data: dict) -> matplotlib.figure.Figure:`
 - **Docstring requirement**: Must describe SMD calculation and balance visualization.
- [X] T012 [P] Create `src/analysis/causal.py` with the following function signatures (stubs raising `NotImplementedError`):
 - `def run_ols(df: pd.DataFrame, cluster_var: str) -> statsmodels.regression.linear_model.RegressionResults:`
 - `def run_did(df: pd.DataFrame) -> statsmodels.regression.linear_model.RegressionResults:`
 - **Docstring requirement**: Must describe OLS with cluster-robust SEs and DiD logic (noted as impossible in plan).
- [X] T013 [P] Create `src/analysis/sensitivity.py` with the following function signature (stub raising `NotImplementedError`):
 - `def sweep_caliper(df: pd.DataFrame, calipers: list) -> dict:`
 - **Docstring requirement**: Must describe the sensitivity sweep logic.

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

**Independent Test**: Can be fully tested by running the PSM algorithm on the ingested dataset, extracting the matched pairs, and calculating the standardized mean difference (SMD) for all covariates. A pass is achieved if all SMDs are <= 0.1. Additionally, a placebo test on a pre-treatment outcome must yield a non-significant difference between matched groups.

### Implementation for User Story 2

- [X] T022 [US2] Implement `src/analysis/psm.py` to estimate propensity scores using logistic regression with covariates (income, housing type, location) and perform nearest neighbor matching with a caliper
- [X] T052 [US2] Implement common support check in `src/analysis/psm.py` (after score calculation) to flag/exclude observations with extreme propensity scores (near the boundaries of the support)
- [X] T023 [US2] Implement `src/analysis/balance.py` to calculate SMD for all matching variables and generate balance plots (love plot)
- [X] T024 [US2] Implement balance failure logic in `src/analysis/psm.py`: if SMD > 0.1 or placebo test fails, raise `CausalIdentificationFailureError` with message "PSM Balance Not Achieved: Hard Halt". This task enforces the 'Graceful Degradation Protocol' (Hard Halt) as mandated by the plan.
- [X] T025 [US2] Implement placebo test logic in `src/analysis/balance.py` to check for significant differences in pre-treatment outcomes between matched groups
- [X] T046 [US2] Implement `src/analysis/balance.py` function `run_placebo_gate(df: pd.DataFrame) -> bool`: execute placebo test on pre-treatment outcome; return False if p-value < 0.05 (signaling unconfoundedness failure); this function gates causal estimation in the main pipeline and its result is integrated into the `balance_status` logic in T024.
- [X] T026 [US2] Create `tests/unit/test_psm.py` to verify matching logic, caliper enforcement, and SMD calculation
- [X] T027 [US2] Create `tests/unit/test_balance.py` to verify SMD thresholds, placebo test significance logic, and DiD trigger logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Causal Effect Estimation and Sensitivity Analysis (Priority: P3)

**Goal**: Estimate ATT using OLS (or DiD fallback), perform sensitivity analysis by sweeping calipers, and generate final results.

**Independent Test**: Can be fully tested by executing the regression (or DiD) and sensitivity sweep, then verifying that the output includes the ATT estimate, p-values, confidence intervals, and a table showing how the ATT changes across the different caliper values. The test passes if the system outputs a valid estimate regardless of statistical significance.

### Implementation for User Story 3

- [X] T054a [US3] Implement `src/analysis/did.py` function `check_longitudinal_data(df: pd.DataFrame) -> bool`: Verify presence of `pre_treatment_outcome` and `post_treatment_outcome` columns. If missing, raise `DataUnavailableError` with message "Longitudinal data missing; DiD fallback impossible. Halting pipeline." This task implements the data check required for the DiD fallback strategy.
- [X] T054b [US3] Implement `src/analysis/did.py` function `run_did(df: pd.DataFrame) -> statsmodels.regression.linear_model.RegressionResults`: Implement the DiD estimation algorithm. This function MUST be callable, but T054a will raise an error before it is reached if data is missing, satisfying the plan's 'Hard Halt' requirement while fulfilling FR-008's requirement to 'implement' the strategy.
- [X] T028 [US3] Implement `src/analysis/causal.py` to run OLS regression with cluster-robust standard errors (clustered by matched pair) on `log(energy_cost)` as the primary outcome. **Note**: Model covariates are strictly limited to those defined in FR-003 (income, housing, location).
- [ ] T053 [US3] Implement control flow logic in `src/main.py`: Add conditional block `if balance_status == FAIL: check_longitudinal_data(); if data missing: raise DataUnavailableError(); halt pipeline`. **Crucial**: The `else: run_did()` path is DEAD CODE and MUST NOT be implemented. The plan explicitly states DiD is impossible with cross-sectional data. This task ensures the pipeline halts with a clear error message ("Causal Identification Failure") rather than attempting an invalid DiD or falling back to OLS.
- [X] T030 [US3] Implement `src/analysis/sensitivity.py` to sweep calipers over a range of small values by calling reusable functions from T022 and T028; compile ATT estimates, p-values, and confidence intervals
- [X] T031 [US3] Implement result serialization in `src/models/output.py`: add method `AnalysisResult.to_json()` to save `AnalysisResult` objects (ATT, p-value, CI, methodology, sensitivity data) to `data/outputs/analysis_result.json`
- [X] T032 [US3] Create `tests/integration/test_pipeline.py` to verify end-to-end flow from ingestion to sensitivity report generation
- [X] T033 [US3] Create `tests/unit/test_causal.py` to verify OLS and DiD estimation logic and cluster-robust standard errors
- [X] T034 [US3] Create `tests/unit/test_did.py` to verify DiD estimation logic and the `DataUnavailableError` raised when longitudinal data is missing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response - Graceful Degradation Protocol (Priority: P1)

**Goal**: Address reviewer concerns regarding the fallback strategy for PSM failure. This phase documents and implements the 'Graceful Degradation Protocol' (Hard Halt) when DiD is impossible due to cross-sectional data.

**Independent Test**: Can be tested by forcing a PSM balance failure and verifying that the system halts with a clear error message indicating that DiD is impossible due to missing longitudinal data, rather than proceeding with OLS or attempting an invalid DiD.

### Implementation for Graceful Degradation Protocol

- [X] T070 [US3] Update `src/analysis/did.py` to include a clear docstring explaining that DiD is methodologically impossible with cross-sectional EIA RECS/ACS data and that the `check_longitudinal_data` function will always raise `DataUnavailableError` for this dataset.
- [ ] T071 [US3] Update `src/main.py` to catch `DataUnavailableError` and log a clear message: "Causal Identification Failure: PSM Balance Not Achieved and DiD Fallback Impossible (Cross-Sectional Data). Pipeline Halted."
- [X] T072 [US3] Update `src/models/schemas.py` to include `GracefulDegradationStatus` schema containing `halt_reason`, `methodology_attempted`, and `data_availability_check`.
- [X] T073 [US3] Integrate `GracefulDegradationStatus` into `AnalysisResult` in `src/models/schemas.py` and `src/models/output.py` to ensure the final JSON output includes the degradation status.
- [X] T074 [US3] Create `tests/unit/test_graceful_degradation.py` to verify the `DataUnavailableError` is raised and the pipeline halts correctly when PSM fails.

**Checkpoint**: Graceful Degradation Protocol is integrated and ensures the pipeline halts correctly when causal identification fails.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates: Update `quickstart.md` with exact commands for running the full causal pipeline (ingest -> match -> estimate -> report) and expected output format. Must document: `python src/main.py --config src/config.yaml` and the expected JSON structure of `data/outputs/analysis_result.json`.
- [X] T043 [P] Run `quickstart.md` validation: Execute the commands documented in T040 and verify that the pipeline completes successfully and produces `data/outputs/analysis_result.json` with valid JSON structure (verified via `python -m json.tool`).
- [X] T045 [P] Final report generation: Create a comprehensive report in `src/reporting/generate_final_report.py` that includes causal inference results and sensitivity analysis, strictly adhering to FR-001 through FR-009.
- [X] T065 [P] Update `README.md` and `docs/architecture.md` to explicitly document the causal inference pipeline (US1-3) and its adherence to FR-001 through FR-009. **Note**: Do NOT include any scaling law sections.
- [X] T076 [P] Update `README.md` and `docs/architecture.md` to document the 'Graceful Degradation Protocol' (Hard Halt) for DiD fallback, explaining why DiD is impossible with cross-sectional data and how the system handles PSM failure.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (T044a, T044b must complete before data tasks).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Graceful Degradation (Phase 6)**: Depends on Foundational phase and US3 data output. Can run in parallel with US3 implementation.
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 matched data output
- **Graceful Degradation (P1)**: Can start after Foundational (Phase 2) and US3 data aggregation. Independent of PSM/DiD logic.
- **Polish (Phase 8)**: Can start after Foundational (Phase 2) and US1 data aggregation. Independent of PSM/DiD logic.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T044a/T044b which are prerequisites for data tasks).
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Graceful Degradation (Phase 6)** can run in parallel with US3 as it only requires US3 data output.

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

1. Complete Phase 1: Setup (including T044a/T044b Security)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Graceful Degradation (Phase 6) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (PSM/Balance)
 - Developer C: User Story 3 (Causal Estimation)
 - Developer D: Graceful Degradation (Phase 6)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: If PSM fails and longitudinal data is missing, the system must halt with a clear error message (Graceful Degradation Protocol) rather than proceeding with OLS, ensuring the pipeline completes with a valid failure state.
- **Scope Clarification**: This project strictly adheres to the Functional Requirements in `spec.md` (FR-001 to FR-009) and the Constitution's Causal Identification Rigor (Principle VI). The scope is limited to PSM/DiD causal inference on US EIA RECS/ACS data. **Phase 6 (Graceful Degradation Protocol)** has been added to address the specific requirement for a fallback strategy (FR-008) while acknowledging the data limitations (Plan: DiD impossible).
- **Reviewer Action**: Tasks T080-T085 (Scaling Law Analysis) and Task T086 (Scaling Law Documentation) have been REMOVED entirely as they were out of scope and violated Constitution Principle VI. Tasks T070-T074 (Graceful Degradation) have been added to document and implement the 'Hard Halt' protocol. Task T044 has been split into T044a and T044b. Task T054 has been split into T054a and T054b to separate the data check from the algorithm implementation. Task T024 has been updated to enforce a 'Hard Halt' on balance failure. Task T053 has been updated to explicitly forbid the `else: run_did()` path. **Phase 7 (Scaling Law Analysis) has been removed entirely** as it was not in scope and violated the plan.
- **Scaling Law Note**: Scaling Law Analysis is out of scope per Constitution Principle VI and the current spec (FR-001 to FR-009). No tasks related to this methodology exist in the current scope.
