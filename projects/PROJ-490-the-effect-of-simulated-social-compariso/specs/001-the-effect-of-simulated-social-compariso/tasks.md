# Tasks: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Input**: Design documents from `/specs/001-simulated-social-comparison-self-esteem/`
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

- [ ] T001 [P] Initialize project structure: Create root directory `projects/PROJ-490-the-effect-of-simulated-social-compariso/` and subdirectories `code/`, `data/`, `tests/`, `docs/`, `state/`, `data/raw`, `data/processed`, `tests/contract`, `tests/unit`. Create `requirements.txt`, `README.md`, and configure linting (flake8/pylint) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create schema contracts in `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/` (dataset.schema.yaml, output.schema.yaml, results.schema.yaml)
- [ ] T003 [P] Implement schema validation utilities in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/utils/validators.py`
- [X] T004 [P] Setup logging infrastructure in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/utils/logger.py`
- [X] T005 [P] Create configuration manager for seeds and paths in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Discovery and Validation (Priority: P1) 🎯 MVP

**Goal**: Locate valid real-world datasets (RSES, INCOM, pre/post) or initialize synthetic data generator with ground truth.

**Independent Test**: Can be fully tested by successfully querying HuggingFace Datasets, OpenML, and Open Science Framework repositories and documenting either: (a) at least one real dataset with N ≥ 100 participants containing RSES, INCOM, and pre/post scores, OR (b) a successful initialization of the synthetic data generator with defined ground-truth parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T006 [P] [US1] Contract test for dataset schema validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/contract/test_dataset_schema.py`
- [ ] T007 [P] [US1] Unit test for synthetic data generator parameter recovery in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_synthetic_gen.py`

### Implementation for User Story 1

- [ ] T008 [P] [US1] Implement dataset discovery script in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` to query HuggingFace, OpenML, and OSF for RSES/INCOM/PrePost variables.
- [X] T009 [US1] Implement IRB/Consent verification logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` (DEPENDS ON T008 output): Verify metadata for IRB approval by checking HuggingFace/OSF metadata fields for 'license' containing 'IRB' or specific consent tags. If missing, log specific missing fields (e.g., 'license', 'consent_form_url'), record the dataset source as blocked, and trigger synthetic fallback (Constitution Principle VI, FR-011, FR-014).
- [X] T010 [US1] Implement synthetic data generator in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` with N ≥ 100, interaction β = 0.2, and "Pipeline Validation Only" labeling (FR-011).
- [~] T011 [US1] Implement fallback logic: if real data not found, trigger synthetic generation and set `data_source_type` flag (FR-009).
- [ ] T012 [US1] Create `data/raw` loader that saves downloaded CSVs or synthetic outputs and writes checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` under `artifact_hashes` (Constitution Principle III, V).
- [~] T013 [US1] Add validation to ensure `data/raw` contains ALL required variables (avatar_condition, pre_self_esteem, post_self_esteem, comparison_tendency) before proceeding (FR-009).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data path selected and validated).

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Preprocess data (MICE), fit ANCOVA regression, and validate model assumptions.

**Independent Test**: Can be fully tested by running the complete analysis pipeline on a sample dataset (real or synthetic) and producing reproducible output artifacts (a CSV file containing regression coefficients and a JSON file containing diagnostic metrics) within ≤6 hours on CPU-only hardware.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test for regression output schema in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/contract/test_results_schema.py`
- [X] T015 [P] [US2] Unit test for MICE imputation on missing < 20% vs > 20% exclusion logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_preprocess.py`

### Implementation for User Story 2

- [X] T016 [US2] Implement missing data handling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` using `miceforest` (primary) for < 20% missingness; fallback to `sklearn.impute.IterativeImputer` if `miceforest` unavailable; exclude rows with > 20% (FR-002, FR-013).
- [X] T017 [US2] Implement variable normalization (avatar_condition to 0/1 if binary) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py`. Note: Do NOT calculate change scores; ANCOVA uses pre_self_esteem as covariate.
- [X] T018 [US2] Implement ANCOVA regression model in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py` (outcome: post_self_esteem, covariate: pre_self_esteem, predictors: avatar_condition, comparison_tendency, interaction).
- [X] T019 [US2] Implement assumption validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py`: Shapiro-Wilk (normality), Breusch-Pagan (homoscedasticity), VIF (collinearity) (FR-004).
- [ ] T020 [US2] Implement dynamic interpretation logic: "Empirical Association" for real data vs "Simulated Causal Effect" for synthetic data (FR-010).
- [ ] T021 [US2] Export regression coefficients to CSV and diagnostics (p-values, VIF, CI) to JSON in `data/processed/` (FR-008).
- [ ] T022 [US2] Handle collinearity (VIF ≥ 5) by flagging and framing results descriptively without claiming independent effects (Assumptions).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data loaded, model fitted, assumptions checked).

---

## Phase 5: User Story 3 - Methodological Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Conduct bootstrap resampling with a sufficient number of iterations to ensure robust estimation. and sensitivity sweeps to validate stability.

**Independent Test**: Can be fully tested by executing bootstrap resampling and threshold sensitivity sweeps on the fitted model and documenting how parameter recovery error (for synthetic data) or significance stability (for real data) varies across different cutoff values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for bootstrap stability calculation (CI width variance < 0.01) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_bootstrap.py`
- [ ] T024 [P] [US3] Unit test for parameter recovery bias calculation (|beta_hat - beta_true|) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement bootstrap resampling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/bootstrap.py` with a sufficient number of iterations to estimate interaction effect stability (FR-005).
- [ ] T026 [US3] Calculate CI width variance from bootstrap results; flag if variance ≥ 0.01 (SC-004).
- [ ] T027 [US3] Implement parameter recovery analysis in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for synthetic data: compare estimated coefficients to ground truth (FR-011, SC-005).
- [ ] T028 [US3] Implement threshold sensitivity sweep in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for p-value thresholds representing conventional significance levels and imputation limits {low, moderate, high, very high} (FR-007).
- [ ] T029 [US3] Apply family-wise error correction (Bonferroni/Holm) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` (FR-006): Apply correction to the set of tests generated by sensitivity sweeps (thresholds + imputation limits) and model assumption tests (Shapiro, Breusch-Pagan, VIF) if any are significant.
- [ ] T030 [US3] Generate final report JSON containing: data path used, model results, bootstrap stability, parameter recovery (if synthetic), and sensitivity findings (FR-012).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/analysis_plan.md` and `README.md`
- [ ] T032a [P] Run `flake8` on `code/` and fix all errors/warnings (errors required)
- [ ] T032b [P] Run `black` on `code/` and `tests/` and fix all formatting violations
- [ ] T033 [P] Run `pytest` on all unit and contract tests in `tests/`
- [ ] T034 Verify reproducibility by running `main.py` twice with fixed seeds and comparing output hashes
- [ ] T035 Run quickstart.md validation if available

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model from US2

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for synthetic data generator parameter recovery in tests/unit/test_synthetic_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset discovery script in code/data/download.py"
Task: "Implement synthetic data generator in code/data/download.py"
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