# Tasks: Predicting Coating Adhesion Strength from Composition and Surface Features

**Input**: Design documents from `/specs/001-predicting-coating-adhesion/`
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

## Phase 0: Data Gap Analysis & Validation (BLOCKER)

**Purpose**: Verify availability of correct dataset URLs and assess alignment feasibility. **MUST PASS before Phase 1.**

**CRITICAL**: If verified URLs are missing, the pipeline MUST halt here and signal for manual intervention.
**NOTE**: There is a known conflict between Spec FR-007 (Heuristic Mapping) and Plan Phase 1.3 (Strict Alignment). The Plan's strict alignment requirement takes precedence. Heuristic mapping is implemented ONLY if unique identifiers are missing (T067).

- [X] T060 [P] Implement `code/utils.py` function to verify Materials Project API URL accessibility and schema validity; **if missing/invalid, write `state/HALT_SIGNAL.yaml` and exit with code 1** (Plan Phase 0)
- [X] T061 [P] Implement `code/utils.py` function to verify NIST Surface Metrology Repository URL accessibility and schema validity; **if missing/invalid, write `state/HALT_SIGNAL.yaml` and exit with code 1** (Plan Phase 0)
- [X] T060-REV [P] **Automated Verification Loop**: Implement `code/utils.py` function `verify_all_sources()` that attempts to verify all three sources (MP, NIST, Lit). If any fail after a configurable number of retries, write `state/HALT_SIGNAL.yaml` and exit. **Replaces T101**. (Addressing Plan Phase 0 Blocker, Constitution Principle II)
- [X] T062 [NOT P] Implement `code/main.py` logic to check for `state/HALT_SIGNAL.yaml` and halt execution immediately if found, logging "Data Gap: Missing Verified Sources - Manual Intervention Required". **This task orchestrates T060, T061, and T060-REV and must run after them.** (Plan Phase 0)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create `data/raw` and `data/processed` directory structure (Plan Phase 1)
- [X] T002 [P] Create `code` and `tests` directory structure (Plan Phase 1)
- [X] T003 [P] Initialize Python project with `requirements.txt` (pandas, scikit-learn, shap, requests, numpy, pyyaml, pytest) (Plan Phase 1)
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools (Plan Phase 1)

---

## Phase 2: Foundational (Blocking Prerequisites & Safety Gates)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, including immediate stopping gates and validation logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 [P] Implement `code/utils.py` with logging, exponential backoff retry logic for API calls, and memory monitoring helpers (Plan Phase 1)
- [X] T006 [P] Create `code/__init__.py` and define base configuration constants (MAX_ROWS=5000, RAM_LIMIT_GB=7, TIMEOUT_HOURS=4) (Plan Phase 1)
- [X] T007 [P] Setup `pytest` configuration and directory structure (`tests/unit`, `tests/integration`) (Plan Phase 1)
- [X] T008 [P] Implement logic to generate/update `state/` YAML file with checksums for raw data files (Constitution Principle III) (Plan Phase 1)
- [X] T009 [P] Implement `code/preprocessing.py` skeleton with **explicit interface definitions** (function signatures, argument types, return types) for one-hot encoding and standardization that T029/T030 must implement (Plan Phase 1)
- [X] T010 [P] Implement `code/utils.py` power analysis function to check sample size N ≥ 1,000 (Plan Phase 1.6)
- [X] T011 [P] Implement `code/utils.py` function to calculate exclusion ratio (missing targets / total valid) and enforce <10% threshold (Plan Phase 1.4, SC-005)
- [X] T012 [P] Implement `code/utils.py` function to calculate processing success rate and enforce ≥95% threshold (Plan Phase 1.5, SC-001)
- [X] T013 [P] Implement `code/modeling.py` skeleton with placeholder for nested CV and SHAP (Plan Phase 2)
- [X] T014 [P] Implement `code/evaluation.py` skeleton for statistical testing (Plan Phase 3)
- [X] T067 [P] Implement `code/utils.py` function to verify the presence of **unique, verified identifiers** in the raw data headers for all three sources. **If missing, write `state/heuristic_mode_required.yaml` (DO NOT HALT)**. (Plan Phase 1.3, Constitution Principle VII)
- [X] T067-REV [P] **Dynamic Verification Gate**: Implement `code/utils.py` to read `state/verified_sources.yaml` (from T060/T061) and validate that the *actual* URLs used in ingestion match the verified ones. **If mismatch, write `state/HALT_SIGNAL.yaml` and exit**. (Addressing coverage-f00892d8)
- [X] T075 [P] **Strict Alignment Enforcement**: Implement `code/ingestion.py` logic to perform **strict** record alignment using **only** unique, verified identifiers. Any record pair that cannot be linked via a verified unique identifier MUST be excluded and logged. **If `state/heuristic_mode_required.yaml` exists, SKIP strict exclusion and allow T023-REV to run**. (Addressing Plan Phase 1.3, Constitution Principle VII)
- [X] T023-DOC [P] **Mapping Protocol Documentation**: Implement `docs/decision_log.md` section "Mapping Protocol (FR-007)" documenting the **conditional** implementation of heuristic mapping. Explicitly state: "FR-007 is implemented ONLY if unique identifiers are missing (T067). If IDs exist, Strict Alignment (T075) is used." (Addressing coverage-f159bd80, coverage-d8d0f5db)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Curation and Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest, clean, and align data from verified sources into a single validated CSV.

**Independent Test**: Run ingestion on mock files to verify output schema, duplicate handling, and null-value exclusion logic.

### PREREQUISITE: Tests for User Story 1 (MUST RUN FIRST) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Do NOT mark [P] for these; they are prerequisites.

- [X] T016 [US1] Unit test for ASTM D4541 filter logic in `tests/unit/test_ingestion.py` (Prerequisite for T022)
- [X] T017 [US1] Unit test for duplicate resolution (most recent date vs sample count) in `tests/unit/test_ingestion.py` (Prerequisite for T025)
- [X] T018 [US1] Integration test for full ingestion pipeline on small mock dataset in `tests/integration/test_pipeline.py` (Prerequisite for T031)

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `code/ingestion.py` to fetch data from Materials Project API with rate-limit handling (FR-001)
- [X] T020 [P] [US1] Implement `code/ingestion.py` to fetch data from NIST Surface Metrology Repository with error handling for 404/schema changes (FR-001)
- [X] T021-LIT [P] [US1] **Literature Ingestion**: Implement `code/ingestion/literature_scraper.py`. **Logic**: Read `state/verified_sources.yaml`. If source is a URL, use `requests` to fetch from arXiv/ScienceDirect API (config defined in `code/config.py`). If source is a local file, load it. **If `state/verified_sources.yaml` is missing or source invalid, raise `DataGapError` immediately**. (Addressing coverage-6f9d90ce, coverage-369d7b9c, executability-270b9174)
- [X] T022 [US1] Implement `code/ingestion.py` logic to filter records strictly to ASTM D4541 pull-off test results (FR-009)
- [X] T023-REV [P] [US1] **Heuristic Mapping Protocol**: Implement `code/ingestion.py` logic to link records using heuristic proxies (e.g., chemical formula + surface roughness range) **ONLY IF** `state/heuristic_mode_required.yaml` exists. **If IDs exist, skip this task**. (Addressing coverage-1b003112, constraint_preservation-d8d0f5db)
- [X] T024 [US1] Implement `code/ingestion.py` logic to exclude records with missing target variables and log counts (US-1, SC-005)
- [X] T025 [US1] Implement `code/ingestion.py` logic to resolve duplicates (most recent date or highest sample count) (US-1)
- [X] T026 [US1] Implement `code/ingestion.py` logic to sample dataset to ≤ 5,000 rows if raw volume exceeds memory (FR-006) (Plan Phase 1.1)
- [X] T027 [US1] Implement `code/ingestion.py` logic to exclude records with missing surface roughness data (impute median or exclude) (US-1)
- [X] T031 [US1] Implement `code/main.py` orchestration to save unified `coating_adhesion_dataset.csv` to `data/processed/` **only if T028 passes**
- [X] T028 [US1] **Validation Gate**: Implement `code/main.py` logic to **calculate processing success rate and exclusion ratio** AFTER ingestion tasks (T019-T031) complete. **Call T011/T012 functions** to calculate metrics on the *output* dataset. **Trigger a HALT** if thresholds are missed. (Plan Phase 1.4/1.5, SC-001, SC-005).
- [X] T029 [US1] Implement `code/preprocessing.py` to encode compositional data (one-hot, atomic radius variance, crosslinker density proxy) adhering to T009 interface (FR-002)
- [X] T030 [US1] Implement `code/preprocessing.py` to standardize surface metrics (RMS, skewness, kurtosis) adhering to T009 interface (FR-002)
- [X] T015 [US1] Implement `code/preprocessing.py` function to perform **Construct Validity Assessment** on derived proxies: compare proxy correlation against target using **thresholds from `code/config.py` (default r=0.3, R²=0.05)**. **Output**: `data/processed/proxy_validation_report.csv`. **If proxy is EXCLUDED and Strict Alignment is active, HALT**. **If Heuristic Mode is active, log warning but allow proxy for ranking only**. (Addressing executability-5e3108c4, constraint_preservation-6dfbf864)
- [X] T076 [US1] **Proxy Validation Gate**: Implement `code/main.py` logic to read `data/processed/proxy_validation_report.csv` (from T015) and halt execution if any proxy is marked as `EXCLUDED` AND Strict Alignment is active. Log the specific proxy names and reasons for exclusion. (Addressing Plan Phase 1.8, Constitution Principle VII)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Feature Importance (Priority: P2)

**Goal**: Train Gradient Boosting and Random Forest models with nested CV and generate SHAP rankings.

**Independent Test**: Run on a small subset to verify non-empty feature list and plausible R² scores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US2] Unit test for nested cross-validation loop (no data leakage) in `tests/unit/test_modeling.py`
- [X] T033 [P] [US2] Unit test for SHAP value calculation and ranking stability in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [X] T034 [US2] Implement `code/modeling.py` to train Gradient Boosting Regressor with nested k-fold CV (FR-003)
- [X] T035 [US2] Implement `code/modeling.py` to train Random Forest Regressor with nested k-fold CV (FR-003)
- [X] T036 [US2] Implement `code/modeling.py` to compute SHAP values for top features (FR-004)
- [X] T037 [US2] Implement `code/modeling.py` to compute permutation importance for top features (FR-004)
- [X] T038 [US2] Implement `code/modeling.py` to rank top features distinguishing compositional vs. surface categories (FR-004)
- [X] T039 [US2] Implement `code/modeling.py` to calculate Spearman correlation between SHAP and permutation rankings (SC-003)
- [X] T040 [US2] Implement `code/main.py` to output JSON report with mean R², RMSE, MAE for both models (US-2)
- [X] T041 [US2] Implement `code/modeling.py` sensitivity analysis for 'crosslinker density' proxy. **Definitions to test**: 1) C/H atomic ratio, 2) O/C atomic ratio, 3) (C+O)/H ratio. Output `data/processed/crosslinker_sensitivity_report.csv` with columns: `definition, model_r2, model_rmse, variance` (FR-008)
- [X] T041-SHIFT [US2] **Sensitivity Validation Gate**: Implement `code/main.py` logic to validate `data/processed/crosslinker_sensitivity_report.csv` (from T041). If variance > threshold, flag "Unstable Proxy" and halt. (Addressing ordering-195d1213)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Baseline Benchmarking (Priority: P3)

**Goal**: Compare full-feature model against baselines using corrected t-tests.

**Independent Test**: Feed mock RMSE scores into test function to verify p-value output and pass/fail logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US3] Unit test for Nadeau & Bengio corrected t-test implementation in `tests/unit/test_evaluation.py`
- [X] T044 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_evaluation.py`

### Implementation for User Story 3

- [X] T045 [US3] Implement `code/evaluation.py` to train composition-only baseline model (US-3)
- [X] T046 [US3] Implement `code/evaluation.py` to train surface-only baseline model (US-3)
- [X] T047 [US3] Implement `code/evaluation.py` to execute Nadeau & Bengio corrected t-test comparing full vs. baselines (FR-005)
- [X] T048 [US3] Implement `code/evaluation.py` to apply Bonferroni correction to p-values (FR-005)
- [X] T049 [US3] Implement `code/evaluation.py` to flag "Informative Null" if full model does not outperform baselines (US-3)
- [X] T050-REP [US3] Implement `code/main.py` to output final statistical comparison report. **Specific Artifact**: `state/statistical_comparison_report.json`. **Schema**: `{ "p_values": {...}, "method": "Nadeau-Bengio", "conclusion": "Significant" | "Informative Null", "bonferroni_adjusted": true }` (US-3, FR-005, SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T063 [P] Implement `code/utils.py` profiling function to run a benchmark on SHAP/CV and save `state/profile_report.json` with runtime metrics. (SC-004)
- [X] T064 [P] Implement optimization logic in `code/modeling.py` based on `state/profile_report.json` to reduce runtime by target <10% (Addressing executability-47a63c0d)
- [X] T052 [P] Refactor: Remove duplicate logging calls and clean up `code/utils.py` (Addressing logging redundancy)
- [X] T065 [P] Create `docs/quickstart.md` with sections: [Install, Run, Config, Data Sources] (Addressing executability-62623e25)
- [X] T066 [P] Update `docs/data-model.md` with [Schema Definitions, Feature Descriptions] (Addressing executability-62623e25)
- [X] T054 [P] Create `.github/workflows/pipeline.yml` to run full pipeline integration test and verify "Pipeline Complete" in logs (Addressing executability-1fa5b421)
- [X] T055 [P] Implement input validation in `code/ingestion.py` for API URL parameters and add `tests/unit/test_security.py` (Addressing executability-f39d2bd6)
- [X] T057 [P] **Stability Verification**: Implement unit test in `tests/unit/test_modeling.py` with `assert spearman_corr >= 0.8`. Update `.github/workflows/pipeline.yml` to enforce this test as a required check. (Addressing coverage-52e9c757)
- [X] T058 [P] **Statistical Rigor**: Implement `code/evaluation.py` logic to log the number of hypothesis tests and Bonferroni-adjusted alpha to `state/statistical_test_log.json` before drawing conclusions. (Addressing coverage-8dc248b4)
- [X] T059 [P] **Spec Update**: Flag Spec FR-007 for external amendment due to conflict with Plan Phase 1.3 (Reject Heuristic Mapping). Document the conflict in `docs/decision_log.md`. (Addressing constraint_preservation-ccefb06e)
- [X] T080 [P] **Runtime Safety Margin**: Implement `code/main.py` logic to monitor total pipeline runtime. If runtime exceeds a predefined safety threshold, write `state/HALT_SIGNAL.yaml` and exit with a message indicating the safety margin was exceeded. (SC-004). (Addressing SC-004)
- [X] T081 [P] **Data Gap Documentation**: Update `docs/decision_log.md` to explicitly document the removal of heuristic mapping (FR-007) and the enforcement of strict unique identifier alignment. Include the rationale from Plan Phase 1.3. (Addressing Plan Phase 1.3, Constitution Principle VII)
- [X] T082 [P] **Proxy Sensitivity Report**: Ensure `code/modeling.py` (T041) explicitly outputs `data/processed/crosslinker_sensitivity_report.csv` with the required columns (`definition, model_r2, model_rmse, variance`) and that `code/main.py` validates the presence of this file before proceeding to reporting. (Addressing FR-008)
- [X] T083 [P] **Statistical Test Logging**: Ensure `code/evaluation.py` (T047-T049) logs the number of hypothesis tests performed and the Bonferroni-adjusted alpha threshold to `state/statistical_test_log.json` before drawing conclusions. (Addressing FR-005, SC-002)
- [X] T084 [P] **Construct Validity Report**: Ensure `code/preprocessing.py` (T015) outputs `data/processed/proxy_validation_report.csv` with the required columns (`proxy_name, correlation, r_squared, status`) and that `code/main.py` validates this file before proceeding to modeling. (Addressing Plan Phase 1.8, Constitution Principle VII)
- [X] T085 [P] **Data Source Verification Report**: Ensure `code/utils.py` (T060, T061, T067) generates a `data/processed/data_source_verification_report.json` detailing the status of each data source (URL, schema validation, unique identifier presence) and that `code/main.py` validates this report before proceeding. (Addressing Plan Phase 0, Plan Phase 1.3)
- [X] T086-P0 [P] **Phase 0 Gate**: Implement `code/main.py` logic to verify `state/phase_0_complete.yaml` exists before proceeding. (Addressing Plan Phase 0)
- [X] T086-P1 [P] **Phase 1 Gate**: Implement `code/main.py` logic to verify `state/phase_1_complete.yaml` exists before proceeding. (Addressing Plan Phase 1)
- [X] T086-P2 [P] **Phase 2 Gate**: Implement `code/main.py` logic to verify `state/phase_2_complete.yaml` exists before proceeding. (Addressing Plan Phase 2)
- [X] T086-P3 [P] **Phase 3 Gate**: Implement `code/main.py` logic to verify `state/phase_3_complete.yaml` exists before proceeding. (Addressing Plan Phase 3)
- [X] T086-P4 [P] **Phase 4 Gate**: Implement `code/main.py` logic to verify `state/phase_4_complete.yaml` exists before proceeding. (Addressing Plan Phase 4)
- [X] T086-P5 [P] **Phase 5 Gate**: Implement `code/main.py` logic to verify `state/phase_5_complete.yaml` exists before reporting. (Addressing Plan Phase 5)
- [X] T087 [P] **Error Handling Enhancement**: Update `code/utils.py` to ensure all API errors (404, rate limits, connection errors) trigger a `DataGapError` or `APIError` with a clear, actionable message, preventing silent failures. (Addressing Plan Risk Mitigation 2)
- [X] T088 [P] **Memory Safety Enforcement**: Update `code/utils.py` to ensure memory monitoring (T005) actively checks RAM usage and triggers a `MemoryError` if the 7 GB limit is approached, preventing OOM crashes. (Addressing Plan Risk Mitigation 3, FR-006)
- [X] T089 [P] **Runtime Monitoring**: Update `code/utils.py` to implement a runtime monitor that checks elapsed time against the 4-hour limit and triggers a `RuntimeError` if exceeded. (Addressing Plan Risk Mitigation 4, SC-004)
- [X] T090 [P] **Documentation Update**: Update `docs/quickstart.md` to reflect the new strict data source requirements and the mandatory Phase 0 data gap check. Include instructions for providing verified data sources. (Addressing Plan Phase 0, SC-004)
- [X] T091 [P] **Test Coverage Update**: Update `tests/unit/test_ingestion.py` to include tests for the new strict alignment logic, proxy validation, and data source verification gates. (Addressing Plan Phase 1.3, Plan Phase 1.8)
- [X] T092-TEST-SUITE [P] **Integration Test Suite**: Implement `tests/integration/test_pipeline.py` with a comprehensive suite covering all Phase 0-5 halt scenarios (data gap, proxy validation, power analysis, exclusion ratio, success rate, runtime limit). (Addressing executability-3beb2e61)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Gap Analysis)**: No dependencies - MUST run first. Halts if URLs missing.
- **Setup (Phase 1)**: No dependencies - can start immediately after Phase 0 passes.
- **Foundational (Phase 2)**: Depends on Phase 0 & 1 - BLOCKS all user stories. Includes safety gates.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2/US1 data output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (T016-T018 before T019-T031)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Gap Analysis (MUST PASS)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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
- **CRITICAL**: Pipeline MUST halt at Phase 0 if verified data URLs are not provided (Plan Phase 0).
- **CRITICAL**: All models must run CPU-only; no CUDA/GPU dependencies.
- **CRITICAL**: Safety gates (Power Analysis, Exclusion Ratio, Success Rate) are enforced in Phase 2 and Phase 3 before any modeling.
- **CRITICAL**: Construct Validity (T015) must pass before model training; invalid proxies are EXCLUDED and pipeline halts (unless Heuristic Mode is active).
- **CRITICAL**: Task T023-REV (Heuristic Mapping) is implemented ONLY if `state/heuristic_mode_required.yaml` exists (T067).
- **CRITICAL**: Task T075 enforces Strict Alignment by default; skips heuristic logic if IDs exist.
- **CRITICAL**: Task T021-LIT raises `DataGapError` if `state/verified_sources.yaml` is missing.
- **CRITICAL**: Task T041-SHIFT is now in Phase 4 to validate sensitivity report immediately.
- **CRITICAL**: T067 sets a flag instead of halting if IDs are missing, allowing T023-REV to run.
- **CRITICAL**: T086-P0 through T086-P5 explicitly check for specific phase completion files.
- **CRITICAL**: T092-TEST-SUITE groups all integration tests into a single task.
- **CRITICAL**: The project is currently in a **Data Gap Analysis** state (Plan.md). The pipeline is blocked until verified URLs for Materials Project, NIST, and Literature sources are provided.