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
**NOTE**: There is a known conflict between Spec FR-007 (Heuristic Mapping) and Plan Phase 1.3 (Strict Alignment). The Plan's strict alignment requirement takes precedence. Heuristic mapping is NOT implemented.

- [X] T060 [P] Implement `code/utils.py` function to verify Materials Project API URL accessibility and schema validity; **if missing/invalid, write `state/HALT_SIGNAL.yaml` and exit with code 1** (Plan Phase 0)
- [X] T061 [P] Implement `code/utils.py` function to verify NIST Surface Metrology Repository URL accessibility and schema validity; **if missing/invalid, write `state/HALT_SIGNAL.yaml` and exit with code 1** (Plan Phase 0)
- [X] T062 [P] Implement `code/main.py` logic to check for `state/HALT_SIGNAL.yaml` and halt execution immediately if found, logging "Data Gap: Missing Verified Sources - Manual Intervention Required" (Plan Phase 0)

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
- [X] T015 [P] Implement `code/preprocessing.py` function to perform **Construct Validity Assessment** on derived proxies: compare proxy correlation against target; **EXCLUDE** any proxy where |r| < 0.3 or R² < 0.05. **Output**: `data/processed/proxy_validation_report.csv` with columns: `proxy_name, correlation, r_squared, status (PASS/EXCLUDED)`. If any proxy is EXCLUDED, **HALT** the pipeline. (Plan Phase 1.8, Constitution Principle VII)
- [X] T067 [P] Implement `code/utils.py` function to verify the presence of **unique, verified identifiers** in the raw data headers for all three sources. **If missing, write `state/HALT_SIGNAL.yaml` and exit with code 1** (Plan Phase 1.3, Constitution Principle VII).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Curation and Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest, clean, and align data from verified sources into a single validated CSV.

**Independent Test**: Run ingestion on mock files to verify output schema, duplicate handling, and null-value exclusion logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Do NOT mark [P] for these; they are prerequisites.**

- [X] T016 [US1] Unit test for ASTM D4541 filter logic in `tests/unit/test_ingestion.py` (Prerequisite for T022)
- [X] T017 [US1] Unit test for duplicate resolution (most recent date vs sample count) in `tests/unit/test_ingestion.py` (Prerequisite for T025)
- [X] T018 [US1] Integration test for full ingestion pipeline on small mock dataset in `tests/integration/test_pipeline.py` (Prerequisite for T031)

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `code/ingestion.py` to fetch data from Materials Project API with rate-limit handling (FR-001)
- [X] T020 [P] [US1] Implement `code/ingestion.py` to fetch data from NIST Surface Metrology Repository with error handling for 404/schema changes (FR-001)
- [X] T021 [P] [US1] Implement `code/ingestion.py` to fetch data from open-access literature sources (FR-001)
- [X] T022 [US1] Implement `code/ingestion.py` logic to filter records strictly to ASTM D4541 pull-off test results (FR-009)
- [X] T023 [US1] **REMOVED**: Heuristic mapping is forbidden by Plan Phase 1.3. This task has been deleted. Alignment is performed strictly via unique identifiers verified in T067.
- [X] T024 [US1] Implement `code/ingestion.py` logic to exclude records with missing target variables and log counts (US-1, SC-005)
- [X] T025 [US1] Implement `code/ingestion.py` logic to resolve duplicates (most recent date or highest sample count) (US-1)
- [X] T026 [US1] Implement `code/ingestion.py` logic to sample dataset to ≤ 5,000 rows if raw volume exceeds memory (FR-006) (Plan Phase 1.1)
- [X] T027 [US1] Implement `code/ingestion.py` logic to exclude records with missing surface roughness data (impute median or exclude) (US-1)
- [X] T028 [US1] **Validation Gate**: Implement `code/main.py` logic to **calculate processing success rate and exclusion ratio** BEFORE ingestion tasks (T019-T027) begin. **Call T011/T012 functions** to calculate metrics. **Trigger a HALT** if thresholds are missed. (Plan Phase 1.4/1.5, SC-001, SC-005).
- [X] T029 [US1] Implement `code/preprocessing.py` to encode compositional data (one-hot, atomic radius variance, crosslinker density proxy) adhering to T009 interface (FR-002)
- [X] T030 [US1] Implement `code/preprocessing.py` to standardize surface metrics (RMS, skewness, kurtosis) adhering to T009 interface (FR-002)
- [X] T031 [US1] Implement `code/main.py` orchestration to save unified `coating_adhesion_dataset.csv` to `data/processed/` **only if T028 passes**

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
- [X] T041 [US2] Implement `code/modeling.py` sensitivity analysis for 'crosslinker density' proxy (multiple definitions) and explicitly output a report of the **variance in model performance** across the three definitions to `data/processed/crosslinker_sensitivity_report.csv` with columns: `definition, model_r2, model_rmse, variance` (FR-008)
- [X] T042 [US2] **REMOVED**: Construct Validity check moved to Phase 2 (T015). This task has been deleted.

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
- [X] T050 [US3] Implement `code/main.py` to output final statistical comparison report (US-3)

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
- [X] T056 [P] **Data Gap Enforcement**: Implement `code/main.py` logic to check for verified sources for **ALL three** inputs (API, NIST, Literature). If **ANY** are missing after Phase 0, write `state/HALT_SIGNAL.yaml` and exit. **Do not implement streaming logic**. (Addressing constraint_preservation-d85fa750)
- [X] T057 [P] **Stability Verification**: Implement unit test in `tests/unit/test_modeling.py` with `assert spearman_corr >= 0.8`. Update `.github/workflows/pipeline.yml` to enforce this test as a required check. (Addressing coverage-52e9c757)
- [X] T058 [P] **Statistical Rigor**: Implement `code/evaluation.py` logic to log the number of hypothesis tests and Bonferroni-adjusted alpha to `state/statistical_test_log.json` before drawing conclusions. (Addressing coverage-8dc248b4)
- [X] T059 [P] **Spec Update**: Flag Spec FR-007 for external amendment due to conflict with Plan Phase 1.3 (Reject Heuristic Mapping). Document the conflict in `docs/decision_log.md`. (Addressing constraint_preservation-ccefb06e)

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
- **CRITICAL**: Construct Validity (T015) must pass before model training; invalid proxies are EXCLUDED and pipeline halts.
- **CRITICAL**: Task T023 (Heuristic Mapping) has been REMOVED to align with Plan Phase 1.3 (Strict Alignment). Spec FR-007 is flagged for amendment.
- **CRITICAL**: Task T042 (Final Construct Validity) has been REMOVED; logic moved to T015 (Phase 2).
- **CRITICAL**: Tasks T068-T073 (Data Gap Resolution) have been REMOVED. The pipeline halts if data is missing or too large; no fallback is implemented.
- **CRITICAL**: Runtime target is 4 hours (SC-004); Plan mentions 6h limit, but tasks enforce 4h safety margin.
- **CRITICAL**: Task T041 explicitly outputs `data/processed/crosslinker_sensitivity_report.csv` as required by FR-008.
- **CRITICAL**: Test tasks T016-T018 are NOT marked [P] and are prerequisites for implementation tasks T019-T031.