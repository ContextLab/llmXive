# Tasks: The Influence of Metacognitive Awareness on Reality Testing

**Input**: Design documents from `/specs/001-influence-metacognitive-awareness-reality-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- **Dependencies**: Tasks must explicitly list `Depends on: T###` if they rely on prior task output.

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `projects/PROJ-179-the-influence-of-metacognitive-awareness/` root directory and `data/`, `code/`, `tests/` subdirectories
- [X] T001b [P] Create `projects/PROJ-179-the-influence-of-metacognitive-awareness/code/__init__.py` and `tests/__init__.py`
- [X] T001c [P] Create `projects/PROJ-179-the-influence-of-metacognitive-awareness/requirements.txt` with pinned dependencies (`pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `requests`, `pyyaml`, `pybids`)
- [X] T002 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T004 is a strict sequential gate.**

- [X] T004 [CRITICAL GATE] Implement `data/validate_data_availability.py` to check for the existence of a VALID behavioral dataset containing `confidence_rating` and `source_label`.
 - **Logic**: If {{claim:c_04c88315}} is detected as the only source, the script MUST exit with code 1 and log: "ERROR: Project blocked. {{claim:c_54ea9f66}}. Aborting."
 - **Logic**: If a valid behavioral dataset is found, log success and exit with code 0.
 - **Fallback**: If ds003386 is invalid, search for alternative datasets (e.g., from UCI, OpenNeuro behavioral datasets) and log results. If no valid dataset is found, the project remains blocked.
 - **Note**: This task overrides the contradictory claim in spec.md's Data Constraints section.
 - **Constraint**: This task MUST run BEFORE T005 and T012. No other tasks in this phase can proceed until T004 passes.
- [X] T005 [Depends on: T004] Implement `data/download.py` to fetch the VALID behavioral dataset identified by T004 (with checksum validation). <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Constraint**: This task assumes T004 has passed. Do NOT attempt to fetch OpenNeuro ds003386 as a "reference" if it is invalid.
 - **Deliverable**: Fetch the dataset. If fetch fails, exit with code 1.
- [X] T006 [Depends on: T005] Implement `data/validate_data.py` to check for required behavioral fields (`confidence_rating`, `source_label`) in the downloaded dataset. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Deliverable**: Output artifact `data/validation_report.json` with status "PASS" or "FAIL".
 - **Logic**: If `confidence_rating` or `source_label` columns are missing, raise `ValueError("Required fields missing: confidence_rating, source_label")` and exit with code 1.
- [X] T007 [P] Create base data models (Participant, Trial) in `src/models/data_models.py`
- [X] T008 [P] Configure error handling and logging infrastructure
- [X] T009 [P] Setup environment configuration management (`.env` for seeds, paths)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Primary Association Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute and visualize the correlation between metacognitive awareness (Type-2 AUC from training split) and reality testing accuracy (d' from test split) using a Hold-Out design to ensure independence.

**Independent Test**: Running the pipeline produces a Pearson correlation coefficient (r) with 95% bootstrapped CI, verifying that confidence (Type-2 AUC) and accuracy (d') are computed from disjoint trial sets.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T011 [P] [US1] Integration test for correlation pipeline in `tests/integration/test_correlation_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `data/preprocess.py` to extract trial-wise source labels and responses from the VALID dataset. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Output**: `data/derived/trial_data.csv` containing `participant_id`, `trial_id`, `stimulus_modality`, `source_label`, `participant_response`, `confidence_rating`.
 - **Constraint**: This task MUST succeed only if T006 passes.
- [X] T013 [US1] [Depends on: T012] Implement `src/utils/stats.py` for Signal Detection Theory (d', criterion) and Type-2 AUC (meta-d') calculation.
 - **Dependency**: Depends on T012 output schema.
 - **Output**: Functions to compute d' and criterion from trial data; function to compute Type-2 AUC (meta-d') from confidence ratings and accuracy on a training split.
- [X] T014 [US1] [Depends on: T012, T013] Implement `src/analysis/correlation.py`:
 - **Method**: Implement **Hold-Out Accuracy** design (70/30 train/test split) as per plan.md.
 - **Logic**: Split trials into a majority training set and a minority test set. Compute Metacognitive Score (Type-2 AUC) on the **training** split. Compute Reality Testing Accuracy (d') on the **held-out test** split. Rotate across participants if needed, but ensure no trial is used for both predictor and outcome.
 - **Constraint**: STRICTLY enforce Hold-Out design. **MUST NOT** use K-fold CV (FR-010 is superseded by plan.md).
- [X] T015 [US1] Implement `src/analysis/bootstrap.py` for 1,000 bootstrap resamples to generate 95% CI.
 - **Runtime Check**: Monitor cumulative wall-clock time of the bootstrap loop. Check periodically at regular resample intervals. If runtime > 5.5h, log warning "Runtime limit detected, reducing bootstrap count to 500", update `data/results/bootstrap_config.json` with `bootstrap_count: 500`, and exit with code 0 (success with warning).
 - **Constraint**: Default is a sufficient number of resamples. Reduction to a lower capacity is a staged fallback only if the 5.5h threshold is exceeded.
- [X] T016 [US1] Implement `src/report/generate.py` to render correlation magnitude, direction, p-value, and CI to `data/results/primary_analysis.json`. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T017 [US1] Add validation to ensure `data/derived/confidence_summary.csv` and `data/derived/accuracy_summary.csv` are derived from disjoint trials.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hierarchical Regression with Covariates (Priority: P2)

**Goal**: Test whether metacognitive awareness (Type-2 AUC) contributes unique variance to reality testing accuracy (d') after controlling for age, gender, and working memory capacity.

**Independent Test**: Running the regression produces incremental R² change (ΔR²) and F-change statistic, with assumption checks (normality, homoscedasticity, VIF).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for regression output schema in `tests/contract/test_regression_schema.py`
- [X] T019 [P] [US2] Integration test for hierarchical regression in `tests/integration/test_hierarchical_regression.py`

### Implementation for User Story 2

- [X] T020 [US2] [Depends on: T014] Implement `src/analysis/regression.py`:
 - **Data Check**: First, check for `working_memory` data in the dataset.
 - **Primary Flow Logic**:
 - **IF** `working_memory` is present: Execute Step 1A (Fit model with age, gender, working-memory) -> Step 2 (Add metacognitive score (Type-2 AUC)).
 - **ELSE** (IF `working_memory` is missing): Execute Step 1B (Fit model with age, gender only) -> Step 2 (Add metacognitive score (Type-2 AUC)). Set flag `n-1_model: true` in output and report adjusted R².
 - **Output**: Calculate ΔR² and F-change. Report adjusted R² if n-1 model is used.
 - **Dependency**: Depends on T014.
 - **Note**: This task assumes T004 passed and a valid dataset was used.
- [X] T021 [US2] [Depends on: T020] Implement `src/analysis/diagnostics.py`:
 - Check normality of residuals (Shapiro-Wilk)
 - Check homoscedasticity (Breusch-Pagan)
 - Calculate VIF for collinearity (flag if VIF ≥ 5)
- [X] T022 [US2] [Depends on: T021] Implement `src/report/generate.py` update to include regression coefficients, SE, t-stat, p-value, and diagnostic flags in `data/results/regression_analysis.json`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Modality-Specific Robustness Analysis (Priority: P3)

**Goal**: Replicate the primary analysis separately for ambiguous visual versus auditory stimuli to test modality-specificity.

**Independent Test**: Filtering the dataset by modality produces separate correlation coefficients (r_visual, r_auditory) with CIs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for modality filter logic in `tests/contract/test_modality_filter.py`
- [X] T025 [P] [US3] Integration test for modality-specific correlation in `tests/integration/test_modality_analysis.py` <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/analysis/filter.py` to split data by `stimulus_modality` (visual vs. auditory). <!-- FAILED: unspecified -->
 - **Output**: `data/derived/visual_trials.csv`, `data/derived/auditory_trials.csv`.
- [X] T027 [US3] [Depends on: T026, T014] Implement `src/analysis/robustness.py` to run the Phase 3 correlation pipeline on each subset independently.
 - **Constraint**: Do not run in parallel with T026. Must wait for T026 to complete.
- [ ] T028 [US3] [Depends on: T027] Implement `src/report/generate.py` update to apply Bonferroni or Benjamini-Hochberg correction for multiple comparisons (family-wise error) and report corrected p-values in `data/results/robustness_analysis.json`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] Update `README.md` with project overview, setup instructions, and data availability warning.
- [X] T029b [P] Update `docs/` with API documentation for `src/analysis/` and `data/` modules.
- [X] T030 [P] Code cleanup and refactoring (remove unused imports, optimize loops)
- [X] T031 [P] Performance optimization (ensure bootstrap and regression complete within 6h on 2 CPU/7GB RAM)
- [X] T032 [P] Additional unit tests for statistical helper functions in `tests/unit/`
- [X] T033 [P] Security hardening (sanitize inputs, secure random seeds)
- [X] T034 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **CRITICAL**: T004 (Data Validation Gate) MUST pass before T005 (Download) and T012 (Preprocessing) can proceed.
 - **Sequential Order**: T004 -> T005/T006 -> T012.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **Internal Order**: T012 -> T013 -> T014 -> T015 -> T016 -> T017
- **User Story 2 (P2)**: Depends on T014 (Metacognitive Score)
 - **Internal Order**: T020 (depends on T014) -> T021 -> T022
- **User Story 3 (P3)**: Depends on T014 and T026
 - **Internal Order**: T026 -> T027 (depends on T026, T014) -> T028

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T004 which is sequential).
- All Foundational tasks marked [P] (T005, T006) can run in parallel **AFTER** T004 passes.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for correlation pipeline in tests/integration/test_correlation_pipeline.py"

# Launch implementation tasks sequentially:
Task: "Implement data/preprocess.py (T012)"
Task: "Implement src/utils/stats.py (T013) - depends on T012"
Task: "Implement src/analysis/correlation.py (T014) - depends on T012, T013"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Run T004**: If it fails (invalid data), STOP. Project is blocked.
 - If T004 passes, proceed to T005, T006, T012.
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (with T004 gate)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational (T004 first) together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (unless explicitly stated otherwise)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Constraint**: If `data/validate_data_availability.py` (T004) detects that {{claim:c_fcdd3c23}}, the pipeline MUST exit with a clear error message and NOT proceed to analysis tasks.
- **Methodology**: T014 MUST implement the **Hold-Out Accuracy** design (70/30 split) as per plan.md. **FR-010 (K-fold CV) is superseded** and must NOT be used.
- **Fallbacks**: T020 MUST handle missing working-memory data by switching to an n-1 model and reporting adjusted R². T015 MUST implement a staged fallback for bootstrap count if runtime exceeds 5.5h.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T035 Reconcile run-book vs implementation for `code/analysis.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/analysis.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist. <!-- ATOMIZE: requested -->
