# Tasks: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `tests/`, `state/`)
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` (pandas, scikit-learn, numpy, requests, pyyaml, memory-profiler, seaborn, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with paths, `GITHUB_ACTIONS_TIMEOUT=5h`, and hyperparameter grids
- [ ] T005 [P] Implement `code/main.py` orchestration entry point with hard timeout enforcement (signal/alarm or `signal` module) and runner verification (check `ubuntu-latest`, no GPU, CPU count)
- [ ] T006 [P] Create `code/__init__.py` and `tests/__init__.py`
- [~] T007 Setup `state/projects/PROJ-386...yaml` schema for artifact hashing and checksums
- [X] T008 Implement `code/data/__init__.py` and `code/modeling/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Variable Verification (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and validate availability of rolling temperature, alloy composition, and grain size data from public sources. Halt with clear error if data is missing.

**Independent Test**: Execute `code/data/ingestion.py` and verify output CSV has non-empty columns for temperature, Mg/Si/Cu, and grain size, OR system halts with Exit Code 1 and specific "Data Missing" log.

### Tests for User Story 1

- [~] T009 [P] [US1] Contract test for schema pre-check logic in `tests/contract/test_ingestion_schema.py` (verify skip logic for missing fields)
- [X] T010 [P] [US1] Unit test for filtering logic in `tests/unit/test_filtering.py` (verify rows with missing temp/grain_size are excluded)
- [X] T011 [P] [US1] Integration test for "Data Missing" halt scenario in `tests/integration/test_data_halt.py` (verify Exit Code 1 when all sources fail)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/ingestion.py` schema pre-check function (check OpenML, NOMAD, Citrination for 'rolling temperature', 'composition', 'grain size' fields; **aggregate list of missing variables across all skipped sources** to support error logging)
- [X] T013 [US1] Implement `code/data/ingestion.py` download and parsing logic (fetch real data from verified URLs; handle CSV/JSON formats)
- [X] T014 [US1] Implement `code/data/ingestion.py` filtering and validation logic (exclude rows with null critical variables; report final dataset size)
- [ ] T015 [US1] Implement `code/data/ingestion.py` "Critical Variables Missing" halt logic (**Raise SystemExit(1) after logging to stderr** with message: "Critical variables missing from all sources: [list of missing variables]")
- [ ] T016 [P] [US1] Create `data/raw/` storage logic with SHA-256 checksum generation in `code/data/ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Interaction Feature Engineering and Baseline Modeling (Priority: P2)

**Goal**: Generate interaction features (Temp × Element), normalize data, and train a baseline linear regression model on residuals to establish main effects.

**Independent Test**: Run `code/data/preprocessing.py` and `code/modeling/baseline.py` on a small sample; verify output includes interaction columns and a model object with coefficients for main effects and interactions.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for interaction feature generation in `tests/unit/test_feature_engineering.py` (verify `Temp × Mg` column creation)
- [ ] T018 [P] [US2] Unit test for residualization logic in `tests/unit/test_residualization.py` (verify residuals against Alloy Series and Composition)
- [ ] T019 [P] [US2] Contract test for baseline model output schema in `tests/contract/test_baseline_output.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/data/preprocessing.py` interaction feature generation (`Temperature × %Mg`, `Temperature × %Si`, etc.) with verification step to confirm columns exist.
- [ ] T021 [P] [US2] Implement `code/data/preprocessing.py` normalization (StandardScaler) for all numeric features with verification step to confirm scaling.
- [ ] T022 [US2] Implement `code/data/preprocessing.py` residualization logic (Regress Grain Size vs. Alloy Series + Composition; store residuals) with verification step to confirm residuals are uncorrelated with Alloy Series.
- [ ] T023 [US2] Implement `code/data/preprocessing.py` collinearity detection (Correlation > 0.8) and JSON report generation (`data/artifacts/collinearity_report.json`) **with schema requiring `flagged_pairs` list of tuples/strings of correlated feature names**.
- [ ] T024 [US2] Implement `code/modeling/baseline.py` Linear Regression training on residuals with interaction terms
- [ ] T025 [US2] Implement `code/modeling/baseline.py` coefficient extraction and logging (R², MAE, coefficients for Temp, Composition, Interactions) **AND** logic to check `collinearity_report.json` to suppress independent interpretation for flagged pairs, framing them descriptively as joint effects.
- [ ] T026 [US2] Implement `code/modeling/baseline.py` "Limited Interaction Effects" flagging logic (if interaction coefficients ~0)
- [ ] T022b [US2] Implement `code/modeling/baseline.py` **Stratified Group K-Fold** cross-validation logic, explicitly **consuming 'Alloy Series' grouping variable from preprocessed data** to prevent leakage as per Constitution Principle VII.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Non-Linear Interaction Modeling and Sensitivity Analysis (Priority: P3)

**Goal**: Train a Random Forest model with grid search to capture non-linear interactions, perform sensitivity analysis on thresholds, and generate partial dependence plots.

**Independent Test**: Run `code/modeling/rf_model.py` with grid search; verify best hyperparameters selected, R² recorded, and sensitivity report generated showing stability of top-5 terms across thresholds.

### Tests for User Story 3

- [ ] T027 [P] [US3] Unit test for grid search timeout fallback in `tests/unit/test_rf_timeout.py` (verify fallback to single-pass if >4h simulated)
- [ ] T028 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_sensitivity.py` (verify threshold sweep across a range of low-magnitude values)
- [ ] T029 [P] [US3] Integration test for full RF pipeline in `tests/integration/test_rf_pipeline.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/modeling/rf_model.py` Random Forest training with GridSearchCV (n_estimators: -200, max_depth: -20) **AND** hard timeout enforcement: **detect -hour elapsed time, interrupt GridSearchCV, and re-run with n_estimators=100, max_depth=10** if timeout occurs. **Consume residuals from T022 and collinearity report from T023.**
- [ ] T032 [US3] Implement `code/analysis/diagnostics.py` **Unified Sensitivity Analysis**: (1) **Threshold Sweep**: identify **top-k significant interaction terms by Feature Importance**, sweep thresholds {, 0.05, 0.1}, calculate **stability percentage** (>80% required); (2) **Confounder Check**: attempt to refit model with proxy variables (e.g., strain rate) if present, calculate and report **R² delta**; if missing, log "No proxy variables available". **Generate `data/artifacts/sensitivity_report.json` with schema: `{threshold, top_5_terms, stability_pct, confounder_r2_delta}`.**
- [ ] T033 [US3] Implement `code/analysis/reporting.py` partial dependence plot generation (visualize Grain Size vs. Temp for specific compositions)
- [ ] T034 [US3] Implement `code/analysis/reporting.py` **Permutation Test** for R² improvement significance (p < 0.05) as required by SC-001, generating `data/artifacts/permutation_test_results.json` with `p_value` field.
- [ ] T035 [US3] Implement `code/analysis/reporting.py` final metrics aggregation (R², MAE, **p-value from T034**, stability scores from T032) **AND** logic to consume `collinearity_report.json` from T023 to enforce descriptive framing in final report.
- [ ] T036 [US3] Implement `code/analysis/reporting.py` "Associational Nature" disclaimer injection in final report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T037 [P] [Polish] Generate final JSON report with all metrics, collinearity flags, and sensitivity results in `data/artifacts/final_report.json`
- [ ] T038 [P] [Polish] Update `state/projects/PROJ-386...yaml` with final artifact hashes and checksums
- [ ] T039 [Polish] Run end-to-end integration test on `ubuntu-latest` runner with memory profiling (`memory-profiler`) to verify ≤6.5 GB RAM usage
- [ ] T040 [Polish] Verify pipeline completion time ≤5 hours in CI simulation
- [ ] T041 [P] [Polish] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T042 [P] [Polish] Code cleanup and refactoring (remove debug prints, optimize imports)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (Data) must complete before US2 (Preprocessing) and US3 (Modeling) can run effectively, though code for US2/US3 can be written in parallel.
 - US2 (Baseline) must complete before US3 (RF) to establish the baseline comparison.
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (Code only)
- **User Story 2 (P2)**: Depends on US1 data output (Runtime dependency); Code can start after Foundational.
- **User Story 3 (P3)**: Depends on US2 baseline output (Runtime dependency); Code can start after Foundational.

### Within Each User Story

- Tests (T009-T011, T017-T019, T027-T029) MUST be written and FAIL before implementation
- Models/Preprocessing (T020-T022) before Modeling (T024-T026)
- Core implementation before integration
- Story complete before moving to next priority (for execution order)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, code for US1, US2, US3 can be written in parallel by different team members
- All tests for a user story marked [P] can run in parallel
- Implementation tasks within a story marked [P] (e.g., T012, T017, T020) can run in parallel if file conflicts are avoided
- **Note on Execution Order**: While T012, T013, T014 can be developed in parallel, their **runtime execution** is strictly sequential: T012 (Pre-check) -> T013 (Download) -> T014 (Filter). T013 and T014 are NOT marked [P] to prevent execution parallelism.

### Critical Runtime Execution Order

- **T012 (Pre-check) -> T013 (Download) -> T014 (Filter)**: Strict sequential execution required for data ingestion.
- **T022 (Residualization)** MUST complete and produce residuals **before** T024 (Baseline Training) can consume them.
- **T023 (Collinearity Report)** MUST be generated before T025 (Coefficient Extraction) and T035 (Reporting) can consume it to enforce framing.
- **T030 (Model Training)** MUST complete and produce model artifact **before** T032 (Sensitivity Analysis) and T034 (Permutation Test) can load it.
- **T032 (Sensitivity Analysis)** AND **T034 (Permutation Test)** MUST complete before T035 (Final Metrics) can aggregate results.
- **T035b (Permutation Test)** (now T034) MUST be implemented and run before T035 (Final Metrics) can aggregate the p-value.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
pytest tests/contract/test_ingestion_schema.py
pytest tests/unit/test_filtering.py
pytest tests/integration/test_data_halt.py

# Launch implementation tasks in parallel (different files/functions):
# Task: "Implement schema pre-check function in code/data/ingestion.py"
# Task: "Implement download and parsing logic in code/data/ingestion.py"
# Task: "Implement filtering and validation logic in code/data/ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Validation)
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify data availability or "Data Missing" halt)
5. Deploy/demo if ready (as a data validation tool)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (Data Validation MVP)
3. Add User Story 2 → Test independently → Demo (Baseline Modeling)
4. Add User Story 3 → Test independently → Demo (Full Pipeline)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Preprocessing & Baseline)
 - Developer C: User Story 3 (RF & Analysis)
3. Stories complete and integrate independently (Data flows from A → B → C)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be executable on GitHub Actions free-tier (CPU-only, cores, ~7GB RAM, ≤6h). No GPU, no 8-bit quantization, no large models.
- **Critical Constraint**: No fabricated data. All data must come from real, verified public sources (NOMAD, OpenML, etc.) as per `plan.md`.
- **Execution Flow**: Runtime dependencies (e.g., T022 -> T024) are strict; implementation tasks (e.g., T020, T021) can be developed in parallel.