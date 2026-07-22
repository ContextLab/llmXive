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

- [X] T060 [P] Implement `code/utils.py` function `verify_materials_project()` to verify Materials Project API URL accessibility and schema validity; **return status code (0=valid, 1=invalid) instead of raising error**. (Plan Phase 0)
- [X] T061 [P] Implement `code/utils.py` function `verify_nist()` to verify NIST Surface Metrology Repository URL accessibility and schema validity; **return status code (0=valid, 1=invalid) instead of raising error**. (Plan Phase 0)
- [ ] T060-REV [P] **Automated Verification Loop & Report**: Implement `code/utils.py` function `verify_all_sources()` that calls T060 and T061, aggregates results into `data/processed/data_source_verification_report.json` with status for each source. **This task MUST write the report artifact**. (Addressing Plan Phase 0 Blocker, Constitution Principle II, executability-b12067ba)
- [X] T062 [P] **Orchestration Gate**: Implement `code/main.py` logic to trigger T060, T061, and T060-REV. **Must run AFTER T060, T061, and T060-REV complete**. Aggregates status from T060-REV. If any source is invalid, write `state/HALT_SIGNAL.yaml` and exit with code 1. (Plan Phase 0)
- [ ] T021-LIT [P] **Literature Ingestion Config**: Implement `code/ingestion/literature_scraper.py`. **Logic**: Read `code/config.py` for keys `LIT_API_URL` and `LIT_API_KEY`. If source is a URL, use `requests` to fetch. If local file, load it. **If `code/config.py` is missing or keys invalid, raise `DataGapError` immediately**. (Addressing executability-00f01ea8)
- [ ] T093 [P] **External Data Source Provisioning**: **ACTION REQUIRED**: Implement `code/main.py` logic to check `data/processed/data_source_verification_report.json`. **If any source is invalid, write `state/HALT_SIGNAL.yaml` and exit**. (Plan Phase 0, Constitution Principle II)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001-DIR [P] **Create Data Directories**: Create `data/raw` and `data/processed` directory structure. (Plan Phase 1)
- [ ] T002-DIR [P] **Create Code Directories**: Create `code` and `tests` directory structure. (Plan Phase 1)
- [ ] T003-FILE [P] **Create Requirements File**: Create `requirements.txt` file at repository root. (Addressing executability-1961ab3f)
- [ ] T003-DEPS [P] **Pin Dependencies**: Add dependencies to `requirements.txt` (pandas, scikit-learn, shap, requests, numpy, pyyaml, pytest) with pinned versions. (Addressing executability-1961ab3f)
- [ ] T004-LINT [P] **Configure Linting**: Create `.ruff.toml` or `pyproject.toml` [tool.ruff] section and install ruff. (Addressing executability-c89ea581)
- [ ] T004-FMT [P] **Configure Formatting**: Create `pyproject.toml` [tool.black] section and install black. (Addressing executability-c89ea581)
- [ ] T003-CONFIG [P] **Configuration Setup**: Create `code/config.py` with keys: `MP_API_KEY`, `NIST_URL`, `LIT_API_URL`, `LIT_API_KEY`, `PROXY_R2_THRESHOLD` (USER MUST SET THIS VALUE, NO DEFAULT), `MAX_ROWS` (5000), `RAM_LIMIT_GB` (7), `TIMEOUT_HOURS` (4). (Addressing executability-00f01ea8, executability-f33d2786)

---

## Phase 2: Foundational (Blocking Prerequisites & Safety Gates)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, including immediate stopping gates and validation logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005-LOG [P] **Logging Setup**: Implement `code/utils.py` logging configuration (format, level, file handler). (Addressing executability-69796c23)
- [ ] T005-RETRY [P] **Retry Logic**: Implement `code/utils.py` exponential backoff retry logic for API calls. (Addressing executability-69796c23)
- [ ] T005-MEM [P] **Memory Monitoring**: Implement `code/utils.py` memory monitoring helpers. (Addressing executability-69796c23)
- [X] T006 [P] Create `code/__init__.py` and define base configuration constants (MAX_ROWS=5000, RAM_LIMIT_GB=7, TIMEOUT_HOURS=4) (Plan Phase 1)
- [ ] T007-PYTEST [P] **Setup Pytest Config**: Create `pytest.ini` or `pyproject.toml` [tool.pytest] section and `tests/unit`, `tests/integration` directories. (Addressing executability-1961ab3f)
- [ ] T008-SCHEMA [P] **State Checksums Schema**: Implement `code/utils.py` function to generate/update `state/checksums.yaml` with schema: `file_path: str, sha256: str`. (Addressing executability-296fbf94)
- [X] T009 [P] Implement `code/preprocessing.py` skeleton with **explicit interface definitions** (function signatures, argument types, return types) for one-hot encoding and standardization that T029/T030 must implement (Plan Phase 1)
- [ ] T067-STRICT [P] **Strict ID Verification**: Implement `code/utils.py` function to verify the presence of **unique, verified identifiers** in the raw data headers for all three sources. **If missing, write `state/HALT_SIGNAL.yaml` and exit**. (Plan Phase 1.3, Constitution Principle VII, constraint_preservation-466f3d8c)
- [X] T075 [P] **Strict Alignment Enforcement**: Implement `code/ingestion.py` logic to perform **strict** record alignment using **only** unique, verified identifiers. Any record pair that cannot be linked via a verified unique identifier MUST be excluded and logged. **Pipeline halts if alignment fails to produce valid pairs**. (Addressing Plan Phase 1.3, Constitution Principle VII, constraint_preservation-fcb9c1b6, constraint_preservation-9e65055c)
- [ ] T015 [P] **Construct Validity Assessment**: Implement `code/preprocessing.py` function to validate derived proxies against **linear regression against literature-derived correlation** as per Plan Phase 1.8. **Logic**: Compare against literature correlation R². **Output**: `data/processed/proxy_validation_report.csv`. **If proxy is UNVERIFIED (R² < configurable threshold), flag for review but DO NOT HALT automatically**. (Addressing constraint_preservation-1a8b239c, executability-f33d2786, ordering-a0f70fb9, executability-258d547a, executability-9da1acfc, constraint_preservation-bb8e5539) <!-- FAILED: unspecified -->
- [X] T084 [P] **Proxy Validation Gate**: Implement `code/main.py` logic to read `data/processed/proxy_validation_report.csv` (from T015) and halt execution if any proxy is marked as `EXCLUDED`. Log the specific proxy names and reasons. **This task is a HARD BLOCKER for Phase 3**. (Addressing Plan Phase 1.8, Constitution Principle VII, missing_artifact_T084, ordering-e002ea0c)
- [X] T010 [P] Implement `code/utils.py` power analysis function to check sample size N ≥ 1,000 (Plan Phase 1.6)
- [X] T011 [P] Implement `code/utils.py` function to calculate exclusion ratio (missing targets / total valid) and enforce <10% threshold (Plan Phase 1.4, SC-005)
- [X] T012 [P] Implement `code/utils.py` function to calculate processing success rate and enforce ≥95% threshold (Plan Phase 1.5, SC-001)
- [X] T013 [P] Implement `code/modeling.py` skeleton with placeholder for nested CV and SHAP (Plan Phase 2)
- [X] T014 [P] Implement `code/evaluation.py` skeleton for statistical testing (Plan Phase 3)
- [ ] T086-PHASE-GATES [P] **Unified Phase Gate Logic**: Implement `code/main.py` function `verify_phase_completion(phase_id)` that checks for `state/phase_<id>_complete.yaml`. This single function is called by all subsequent phase gates. (Addressing executability-e6864739, coverage-8173206f)
- [ ] T041 [P] **Sensitivity Analysis**: Implement `code/modeling.py` sensitivity analysis for 'crosslinker density' proxy. **Definitions**: Read from `code/config.py` (list of at least 3 ratio definitions). **Input**: Atomic counts normalized to **atomic fraction**. **Output**: `data/processed/crosslinker_sensitivity_report.csv` with columns: `definition, model_r2, model_rmse, variance`. (FR-008, executability-f3eb2394, F001, executability-5c7bf136, executability-87d349db)
- [ ] T085 [P] **Generate Sensitivity Report**: Implement `code/modeling.py` logic to ensure `data/processed/crosslinker_sensitivity_report.csv` is written and validated. **Explicitly generates the artifact required by T041**. (Addressing coverage-b0aa6a62, F001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (ONLY IF T084 passes)

---

## Phase 3: User Story 1 - Dataset Curation and Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest, clean, and align data from verified sources into a single validated CSV.

**Independent Test**: Run ingestion on mock files to verify output schema, duplicate handling, and null-value exclusion logic.

### PREREQUISITES: Tests for User Story 1 (Not Yet Implemented) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Do NOT mark [P] for these; they are prerequisites.

- [X] T016 [US1] Unit test for ASTM D4541 filter logic in `tests/unit/test_ingestion.py` (Prerequisite for T022)
- [X] T017 [US1] Unit test for duplicate resolution (most recent date vs sample count) in `tests/unit/test_ingestion.py` (Prerequisite for T025)
- [X] T018 [US1] Integration test for full ingestion pipeline on small mock dataset in `tests/integration/test_pipeline.py` (Prerequisite for T031)

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `code/ingestion.py` to fetch data from Materials Project API with rate-limit handling (FR-001)
- [X] T020 [P] [US1] Implement `code/ingestion.py` to fetch data from NIST Surface Metrology Repository with error handling for 404/schema changes (FR-001)
- [X] T022 [US1] Implement `code/ingestion.py` logic to filter records strictly to ASTM D4541 pull-off test results (FR-009)
- [X] T024 [US1] Implement `code/ingestion.py` logic to exclude records with missing target variables and log counts (US-1, SC-005)
- [X] T025 [US1] Implement `code/ingestion.py` logic to resolve duplicates (most recent date or highest sample count) (US-1)
- [X] T026 [US1] Implement `code/ingestion.py` logic to sample dataset to ≤ 5,000 rows if raw volume exceeds memory (FR-006) (Plan Phase 1.1)
- [ ] T027 [US1] Implement `code/ingestion.py` logic to handle missing surface roughness: **impute using median of same `substrate_id` group if missing, else exclude. If the group median is undefined (empty group), exclude the record**. Log counts. (US-1, constraint_preservation-ce2f2ecd, executability-ed46e04d, executability-d301878f, constraint_preservation-b6ed4377)
- [ ] T031 [US1] Implement `code/main.py` orchestration to save unified `coating_adhesion_dataset.csv` to `data/processed/`. (Plan Phase 1.1)
- [ ] T028 [US1] **Validation Gate**: Implement `code/main.py` logic to **calculate processing success rate and exclusion ratio** AFTER T031 completes. **Read the saved CSV** and call T011/T012 functions. **Trigger a HALT** if thresholds are missed. **Must run immediately after T031, before T029/T030**. (Plan Phase 1.4/1.5, SC-001, SC-005, ordering-a7ea4436, ordering-988d31ad)
- [ ] T029 [US1] Implement `code/preprocessing.py` to encode compositional data (one-hot, atomic radius variance, crosslinker density proxy) adhering to T009 interface (FR-002)
- [ ] T030 [US1] Implement `code/preprocessing.py` to standardize surface metrics (RMS, skewness, kurtosis) adhering to T009 interface (FR-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Feature Importance (Priority: P2)

**Goal**: Train Gradient Boosting and Random Forest models with nested CV and generate SHAP rankings.

**Independent Test**: Run on a small subset to verify non-empty feature list and plausible R² scores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US2] Unit test for nested cross-validation loop (no data leakage) in `tests/unit/test_modeling.py`
- [ ] T033 [P] [US2] Unit test for SHAP value calculation and ranking stability in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [ ] T034 [US2] Implement `code/modeling.py` to train Gradient Boosting Regressor with nested k-fold CV (FR-003)
- [ ] T035 [US2] Implement `code/modeling.py` to train Random Forest Regressor with nested k-fold CV (FR-003)
- [ ] T036 [US2] Implement `code/modeling.py` to compute SHAP values for top features (FR-004)
- [ ] T037 [US2] Implement `code/modeling.py` to compute permutation importance for top features (FR-004)
- [ ] T038 [US2] Implement `code/modeling.py` to rank top features distinguishing compositional vs. surface categories (FR-004)
- [ ] T039 [US2] Implement `code/modeling.py` to calculate Spearman correlation between SHAP and permutation rankings (SC-003)
- [ ] T041-SHIFT [US2] **Sensitivity Validation Gate**: Implement `code/main.py` logic to validate `data/processed/crosslinker_sensitivity_report.csv` (from T041/T085). If **variance in R² > 0.05**, flag "Unstable Proxy" and halt. **Must run AFTER T085 and BEFORE T040**. (Addressing ordering-6acc0359, coverage-8c138b8a, ordering-6f71e1f4, constraint_preservation-0f3e8eda)
- [ ] T040 [US2] **Output Final Report**: Implement `code/main.py` to output JSON report with mean R², RMSE, MAE for both models. **RUN ONLY IF T041-SHIFT PASSES**. (US-2, ordering-6f71e1f4)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Baseline Benchmarking (Priority: P3)

**Goal**: Compare full-feature model against baselines using corrected t-tests.

**Independent Test**: Feed mock RMSE scores into test function to verify p-value output and pass/fail logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T043 [P] [US3] Unit test for Nadeau & Bengio corrected t-test implementation in `tests/unit/test_evaluation.py`
- [ ] T044 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_evaluation.py`

### Implementation for User Story 3

- [ ] T045 [US3] Implement `code/evaluation.py` to train composition-only baseline model (US-3)
- [ ] T046 [US3] Implement `code/evaluation.py` to train surface-only baseline model (US-3)
- [ ] T047 [US3] Implement `code/evaluation.py` to execute Nadeau & Bengio corrected t-test comparing full vs. baselines (FR-005)
- [ ] T048 [US3] Implement `code/evaluation.py` to apply Bonferroni correction to p-values (FR-005)
- [ ] T049 [US3] Implement `code/evaluation.py` to flag "Informative Null" if full model does not outperform baselines (US-3)
- [ ] T050-REP [US3] Implement `code/main.py` to output final statistical comparison report. **Specific Artifact**: `state/statistical_comparison_report.json`. **Schema**: `{ "p_values": {...}, "method": "Nadeau-Bengio", "conclusion": "Significant" | "Informative Null", "bonferroni_adjusted": true }` (US-3, FR-005, SC-002, ordering-9c54c950)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T063 [P] Implement `code/utils.py` profiling function to run a benchmark on SHAP/CV and save `state/profile_report.json` with runtime metrics. (SC-004)
- [ ] T064 [P] Implement optimization logic in `code/modeling.py` based on `state/profile_report.json` to reduce runtime by target <10% (Addressing executability-47a63c0d)
- [ ] T052 [P] Refactor: Remove duplicate logging calls and clean up `code/utils.py` (Addressing logging redundancy)
- [ ] T065 [P] Create `docs/quickstart.md` with sections: [Install, Run, Config, Data Sources] (Addressing executability-62623e25)
- [ ] T066 [P] Update `docs/data-model.md` with [Schema Definitions, Feature Descriptions] (Addressing executability-62623e25)
- [ ] T054 [P] Create `.github/workflows/pipeline.yml` to run full pipeline integration test and verify "Pipeline Complete" in logs (Addressing executability-1fa5b421)
- [ ] T055 [P] Implement input validation in `code/ingestion.py` for API URL parameters and add `tests/unit/test_security.py` (Addressing executability-f39d2bd6)
- [ ] T057 [P] **Stability Verification**: Implement unit test in `tests/unit/test_modeling.py` with `assert spearman_corr >= 0.8`. Update `.github/workflows/pipeline.yml` to enforce this test as a required check. (Addressing coverage-52e9c757)
- [ ] T058 [P] **Statistical Rigor**: Implement `code/evaluation.py` logic to log the number of hypothesis tests and Bonferroni-adjusted alpha to `state/statistical_test_log.json` before drawing conclusions. (Addressing coverage-8dc248b4)
- [ ] T059-AMEND-SPEC-EXEC [P] **Spec Update**: **Task to amend spec.md**: Update `spec.md` to **remove FR-007** and replace it with: "System MUST enforce strict alignment using unique, verified identifiers. Heuristic mapping is prohibited." **Edit the file `projects/PROJ-419-predicting-coating-adhesion-strength-fro/specs/001-predicting-coating-adhesion-strength-fro/spec.md` directly to remove the FR-007 text and insert the new requirement.** Document the change in `docs/decision_log.md`. (Addressing constraint_preservation-ccefb06e, coverage-fec71073, coverage-e838bc4f, constraint_preservation-9ae16296, F001)
- [ ] T080 [P] **Runtime Safety Margin**: Implement `code/main.py` logic to monitor total pipeline runtime. If runtime exceeds **4 hours** (SC-004), write `state/HALT_SIGNAL.yaml` and exit with a message indicating the safety margin was exceeded. (SC-004, ordering-af537616)
- [ ] T081 [P] **Data Gap Documentation**: Update `docs/decision_log.md` to explicitly document the removal of heuristic mapping (FR-007) and the enforcement of strict unique identifier alignment. Include the rationale from Plan Phase 1.3. (Addressing Plan Phase 1.3, Constitution Principle VII)
- [ ] T083 [P] **Statistical Test Logging**: Ensure `code/evaluation.py` (T047-T049) logs the number of hypothesis tests performed and the Bonferroni-adjusted alpha threshold to `state/statistical_test_log.json` before drawing conclusions. (Addressing FR-005, SC-002)
- [ ] T087 [P] **Error Handling Enhancement**: Update `code/utils.py` to ensure all API errors (404, rate limits, connection errors) trigger a `DataGapError` or `APIError` with a clear, actionable message, preventing silent failures. (Addressing Plan Risk Mitigation 2)
- [ ] T088 [P] **Memory Safety Enforcement**: Update `code/utils.py` to ensure memory monitoring (T005) actively checks RAM usage and triggers a `MemoryError` if the GB limit is approached, preventing OOM crashes. (Addressing Plan Risk Mitigation 3, FR-006)
- [ ] T089 [P] **Runtime Monitoring**: Update `code/utils.py` to implement a runtime monitor that checks elapsed time against the prescribed time limit and triggers a `RuntimeError` if exceeded. (Addressing Plan Risk Mitigation 4, SC-004)
- [ ] T090 [P] **Documentation Update**: Update `docs/quickstart.md` to reflect the new strict data source requirements and the mandatory Phase 0 data gap check. Include instructions for providing verified data sources. (Addressing Plan Phase 0, SC-004)
- [ ] T091 [P] **Test Coverage Update**: Update `tests/unit/test_ingestion.py` to include tests for the new strict alignment logic, proxy validation, and data source verification gates. (Addressing Plan Phase 1.3, Plan Phase 1.8)
- [ ] T092-TEST-SUITE [P] **Integration Test Suite**: Implement `tests/integration/test_pipeline.py` with a comprehensive suite covering all Phase 0-5 halt scenarios (data gap, proxy validation, power analysis, exclusion ratio, success rate, runtime limit). (Addressing executability-3beb2e61)
- [ ] T096 [P] **Runtime Validation Report**: Implement `code/main.py` logic to measure total runtime at the end of the pipeline and write `state/runtime_validation_report.json` confirming SC-004 compliance (runtime < 4h). **Distinct from safety gate T080**. (Addressing coverage-05bc8713)
- [ ] T096-AMEND-SC004 [P] **Spec Text Amendment (Manual)**: **Task to amend spec.md**: Update `spec.md` to fix `SC-004` placeholder typo '-hour' to '6-hour' and clarify '4-hour' success criterion. **Edit the file `projects/PROJ-419-predicting-coating-adhesion-strength-fro/specs/001-predicting-coating-adhesion-strength-fro/spec.md` directly to replace the text 'the -hour GitHub Actions free-tier limit' with 'the 6-hour GitHub Actions free-tier limit' and clarify the 4-hour success criterion.** (Addressing constraint_preservation-a6f0480a, executability-0e85a309)

---

## Phase 6: Data Gap Resolution & Manual Intervention (Current State)

**Purpose**: Address the critical blocking issue where verified data sources are missing. This phase contains tasks that **MUST** be resolved by human intervention or external data provisioning before the pipeline can proceed.

**Status**: **BLOCKED**. All downstream tasks are suspended until this phase is cleared.

- [ ] T093-CONFIG [P] **Codify Verified URLs**: **ACTION REQUIRED**: Once T093 is resolved, update `code/config.py` and `docs/data-model.md` with the verified URLs to ensure **reproducibility** (Constitution Principle I). (Addressing executability-2a395002, constraint_preservation-c38adc3e)
- [ ] T094 [P] **Unique Identifier Verification**: **ACTION REQUIRED**: Confirm that the provided datasets contain **unique, verified identifiers** that can be used to strictly align coating-substrate pairs across all three sources. If identifiers are missing, a new data collection strategy must be defined. (Plan Phase 1.3, Constitution Principle VII)
- [ ] T095 [P] **Data Gap Resolution Report**: **ACTION REQUIRED**: Once T093, T093-CONFIG, and T094 are resolved, update `docs/decision_log.md` with the final data source URLs, access methods, and confirmation of unique identifier alignment. This document serves as the "Go/No-Go" decision for resuming the pipeline. (Addressing Plan Phase 0, SC-001)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Gap Analysis)**: No dependencies - MUST run first. Halts if URLs missing.
- **Setup (Phase 1)**: No dependencies - can start immediately after Phase 0 passes.
- **Foundational (Phase 2)**: Depends on Phase 0 & 1 - BLOCKS all user stories. Includes safety gates.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 6 (Data Gap Resolution)**: **BLOCKER**. Must be resolved before Phase 0 can pass.
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
- **CRITICAL**: Construct Validity (T015) must pass before model training; invalid proxies are EXCLUDED and pipeline halts.
- **CRITICAL**: Task T023-REV (Heuristic Mapping) has been REMOVED. Strict alignment is the only path.
- **CRITICAL**: Task T041-SHIFT is now in Phase 4 to validate sensitivity report immediately.
- **CRITICAL**: T086-PHASE-GATES enforces all phase gates via a single parameterized function.
- **CRITICAL**: T092-TEST-SUITE groups all integration tests into a single task.
- **CRITICAL**: The project is currently in a **Data Gap Analysis** state (Plan.md). The pipeline is blocked until verified URLs for Materials Project, NIST, and Literature sources are provided.
- **CRITICAL**: Phase 6 tasks (T093, T093-CONFIG, T094, T095) are **mandatory** for unblocking the project. Human intervention is required.
- **CRITICAL**: T096-AMEND-SC004 flags the Spec text for external amendment to fix the '-hour' typo and now mandates the direct edit of the spec file.
- **CRITICAL**: T059-AMEND-SPEC-EXEC tasks the formal amendment of spec.md to remove FR-007 and now mandates the direct edit of the spec file.