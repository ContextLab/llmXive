# Tasks: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

**Input**: Design documents from `/specs/001-social-exclusion-prosociality/`
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

- [ ] T001a [P] Create directory structure: `projects/PROJ-382-the-impact-of-simulated-social-exclusion/code/`, `data/raw/`, `data/processed/`, `tests/`, `state/`
- [ ] T001b [P] Create `projects/PROJ-382-the-impact-of-simulated-social-exclusion/code/requirements.txt` with pinned dependencies (pandas, numpy, scipy, statsmodels, matplotlib, pyyaml, requests, scikit-learn, memory_profiler, psutil)
- [ ] T002a [P] Create `.flake8` configuration file with explicit rules (e.g., `max-line-length=88`, `exclude=venv,.git,build,dist`)
- [ ] T002b [P] Create `pyproject.toml` configuration for `black` (e.g., `line-length=88`, `target-version=['py311']`)
- [ ] T002c [P] Create a verification script or Makefile target to run `flake8` and `black --check` to validate linting compliance
- [ ] T003 [P] Implement base configuration loader (`code/config.py`) to read OSF URLs from YAML
- [~] T004 [P] Setup logging infrastructure with deterministic logging format for `data/processed/mapping_log.json`
- [~] T005 Create base data validation schema (Pydantic or Pandas dtype checks) for `condition`, `prosocial_amount`, `randomized`
- [~] T006 Implement error handling wrapper for network requests (timeouts, 404s) to ensure pipeline continuity
- [~] T007 Setup environment configuration management for `PYTHONHASHSEED` and random seeds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Schema Validation, and Standardization (Priority: P1) 🎯 MVP

**Goal**: Locate, download, validate, and standardize raw data from OSF, ensuring schema compliance and handling missing values without imputing structural zeros.

**Independent Test**: Run ingestion script against a config with one valid OSF URL (with required columns) and one invalid URL (missing columns). Verify valid data is ingested, invalid is skipped with log, and pipeline halts if <3 valid datasets remain.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T008 [P] [US1] Unit test for schema validation logic in `tests/unit/test_ingest_schema.py`
- [~] T009 [P] [US1] Unit test for missing value imputation logic (median vs exclude) in `tests/unit/test_ingest_imputation.py`
- [~] T010 [P] [US1] Integration test for end-to-end ingestion with mock OSF responses in `tests/integration/test_ingest_flow.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement OSF downloader in `code/ingest.py` with retry logic and checksum verification
- [ ] T012 [US1] Implement schema validator in `code/ingest.py` to check for `condition`, `prosocial_amount`, `randomized` columns
- [ ] T013 [US1] Implement column normalizer in `code/ingest.py` to map variants (donation/allocation/transfer -> `prosocial_amount`) and condition strings (ignored/excluded -> 1)
- [ ] T014 [US1] Implement missing value handler in `code/preprocess.py`: median imputation (<5% NaN) or row exclusion (>=5% NaN), ensuring structural zeros (0) are preserved; **Output**: Write cleaned DataFrame to `data/processed/cleaned_data.parquet` and log imputation details to `data/processed/imputation_log.json`
- [ ] T015 [US1] Implement dataset merger in `code/ingest.py` to combine valid datasets into a single DataFrame
- [ ] T016 [US1] Implement "Insufficient Data" halt logic: check if valid dataset count <3 and exit with non-zero status
- [ ] T017 [US1] Implement keyword search fallback in `code/ingest.py`: **Trigger**: if the initial URL list yields **fewer than 3** valid datasets, perform a keyword-based search on OSF for "social exclusion" AND "prosocial" OR "donation"
- [ ] T018 [US1] Write mapping log to `data/processed/mapping_log.json` recording raw-to-binary condition mappings for Principle VI compliance

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Effect Size Estimation (Priority: P2)

**Goal**: Perform Zero-Inflated Gamma (ZIG) or Hurdle modeling for continuous outcomes (handling zeros natively) and Logistic Regression for binary outcomes, separated into Causal and Associational pools.

**Independent Test**: Feed a synthetic dataset with known zeros and a known negative correlation. Verify ZIG model is used (not standard Gamma), outputs two distinct coefficients, and correctly splits data into Causal (RCT) and Associational pools based on `randomized` flag.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for ZIG model fitting with synthetic data in `tests/unit/test_analysis_model.py`
- [ ] T020 [P] [US2] Unit test for pool splitting logic (RCT vs Non-RCT) in `tests/unit/test_analysis_pools.py`
- [ ] T021 [P] [US2] Integration test for meta-analysis aggregation in `tests/integration/test_analysis_meta.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement pool splitter in `code/preprocess.py` to separate data into `causal_pool` (randomized=true) and `associational_pool` (randomized=false/unknown)
- [ ] T024 [US2] Implement outcome type detector in `code/analysis.py` to identify binary (0/1) vs continuous `prosocial_amount`
- [ ] T025a [US2] Verify/Implement ZIG wrapper in `code/analysis.py`: Implement a custom Zero-Inflated Gamma likelihood function or verify `statsmodels` ZeroInflated compatibility with Gamma distribution (since native support is limited); **Output**: A reusable `fit_zig_model` function
- [ ] T025b [US2] Implement Zero-Inflated Gamma (ZIG) or Hurdle model wrapper in `code/analysis.py` using the verified wrapper for continuous outcomes
- [ ] T026 [US2] Implement Logistic Regression wrapper in `code/analysis.py` for binary outcomes
- [ ] T027 [US2] Implement coefficient extractor to output: (1) log-odds for zero-inflation, (2) log-scale for positive amounts (or log-odds ratio for binary)
- [ ] T028 [US2] Implement meta-analysis aggregator in `code/analysis.py` to perform Random-Effects meta-analysis separately for Causal and Associational pools
- [ ] T029 [US2] Implement "Insufficient Causal Data" flag: if Causal Pool <3 datasets, report status but continue with Associational Pool
- [ ] T030 [US2] Implement confidence interval calculator for both zero-inflation and positive components
- [ ] T031 [US2] Implement detailed statistical reporter: Generate a `data/processed/causal_pool_test_result.json` artifact containing the **exact coefficient values, 95% confidence intervals, p-values, and sample size** for the Causal Pool effect size against $\beta=0$ (SC-002). **Do not** use a binary Pass/Fail flag as the primary output.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis, Robustness Check, and Data Quality Filtering (Priority: P3)

**Goal**: Perform sensitivity analysis on model assumptions, filter underpowered datasets (n<5), and calculate meta-analytic power.

**Independent Test**: Run analysis on same data with modified link functions (logit vs probit) and verify effect size coefficient variance is reported. Verify datasets with exclusion group n<5 are excluded from primary pool.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for sensitivity analysis loop (link function + distribution sweep) in `tests/unit/test_sensitivity.py`
- [ ] T033 [P] [US3] Unit test for power calculation logic in `tests/unit/test_power_analysis.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement sensitivity analysis runner in `code/analysis.py` to sweep **both** link functions (logit, probit, cloglog) **AND** distributional assumptions (Gamma, Log-Normal)
- [ ] T035 [US3] Implement stability checker to calculate variance of effect size coefficients across sensitivity sweep (target variance < 10%)
- [ ] T036 [US3] Implement outlier detector (statistical deviation from mean) and robustness re-run logic excluding outliers
- [ ] T037 [US3] Implement heterogeneity calculator ($I^2$) for the meta-analysis pool
- [ ] T038 [US3] Implement formal meta-analytic power assessment in `code/analysis.py` to estimate power for Cohen's d = 0.3 **using observed heterogeneity ($I^2$) and number of studies**; **Output**: Write power assessment report to `data/processed/power_analysis.json`
- [ ] T040 [US3] Implement small-sample bias correction logic for the meta-analysis
- [ ] T042a [US3] Implement data quality filter in `code/preprocess.py` to exclude datasets where exclusion group sample size < 5 **before** meta-analysis; **Output**: Write filtered dataset list to `data/processed/filtered_datasets.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates: `quickstart.md` with run instructions
- [ ] T042b [P] Extract ZIG model logic into `code/models/zig.py`
- [ ] T042c [P] Add type hints to `code/analysis.py`
- [ ] T042d [P] Refactor meta-analysis loop into `code/models/meta.py`
- [ ] T043 Performance optimization: Use `memory_profiler` and `psutil` to verify memory usage < 6GB and CPU < 2 cores during a full dataset run stress test
- [ ] T044 [P] Additional unit tests for edge cases (network timeout, empty CSVs) in `tests/unit/`
- [ ] T045 Run quickstart.md validation to ensure reproducibility
- [ ] T046 Update `state/` file with content hashes of `code/` and `data/` artifacts

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires analysis results from US2

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
Task: "Unit test for schema validation logic in tests/unit/test_ingest_schema.py"
Task: "Unit test for missing value imputation logic in tests/unit/test_ingest_imputation.py"
Task: "Integration test for end-to-end ingestion with mock OSF responses in tests/integration/test_ingest_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement OSF downloader in code/ingest.py with retry logic and checksum verification"
Task: "Implement schema validator in code/ingest.py to check for condition, prosocial_amount, randomized columns"
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
 - Developer B: User Story 2 (Statistical Analysis)
 - Developer C: User Story 3 (Sensitivity & Quality)
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
- **Feasibility Check**: All statistical models (ZIG, Meta-analysis) are CPU-tractable on standard datasets; no GPU required.
- **Data Integrity**: Structural zeros (0) must never be imputed; they are critical for the ZIG model's zero-inflation component.
- **Constraint Compliance**: The system reports **two distinct coefficients** (log-odds for zero-inflation, log-scale for positive amounts) as per FR-003. **No Average Marginal Effect (AME)** is calculated or aggregated.
- **Data Source Verification**: All dataset URLs must be real, reachable, and sourced from OSF or verified repositories (e.g., UCI, NAB); no synthetic data generation tasks are permitted for input data.
- **Temporal Validation**: Ensure tasks verify temporal separation between exclusion task and prosocial outcome if timestamps are available in raw data.
- **Scope Boundary**: E-values for unmeasured confounding are **not** implemented as they are not required by FR-005 or FR-009.
- **Plan Note**: The Plan Summary mentions AME, but this contradicts FR-003. The implementation follows FR-003 (ZIG coefficients). The Plan/Spec Summary should be updated in a future iteration to align with FR-003.