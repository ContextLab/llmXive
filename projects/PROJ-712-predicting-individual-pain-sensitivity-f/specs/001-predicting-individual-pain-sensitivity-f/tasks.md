# Tasks: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Input**: Design documents from `/specs/001-pain-sensitivity-microstates/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 [P] Initialize project directory structure: create `data/raw/`, `data/processed/`, `artifacts/`, `state/`, `code/`, and `tests/` directories.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `statsmodels`, `joblib`, `pyyaml`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` with seed pinning, logging setup, `record_artifact_hash()`, and `compute_checksum()` functions for Constitution Principles V and III.
- [X] T004b [US1] Compute SHA-256 checksums for all raw data files upon ingestion into `data/raw/` and record them in `state/projects/PROJ-712-predicting-individual-pain-sensitivity-f.yaml` (Constitution Principle III).
- [X] T005 [P] Create `scripts/pre-run-validation.sh` to invoke `code/utils.py --validate-citations` (Constitution Principle II: Verified Accuracy)
- [ ] T007 Create `contracts/dataset.schema.yaml` and `contracts/features.schema.yaml` based on `plan.md` entities
- [X] T008 Implement `code/data_loader.py` with `DataChunk` logic using `numpy.memmap` to handle limited RAM constraints. Ensure the data loading and preparation logic supports the extraction of exactly 30 features as defined in FR-002.
- [X] T009 Setup `code/config.py` for environment variables and path management
- [X] T026a [P] Implement timing instrumentation in `code/utils.py` or `code/config.py`: function to record start/end times and an assertion `assert duration < 6 hours` to enforce SC-005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest OpenNeuro ds003XXX, preprocess EEG (re-reference, filter, ICA), and extract microstate features per participant.

**Independent Test**: The pipeline can be executed end-to-end on a sample of participants; the output must be a CSV file containing a fixed set of features per participant and heat-pain threshold labels, with no NaN values.

### Validation & Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [US1] Write unit test `test_ica_artifact_removal` in `tests/unit/test_preprocessing.py` that asserts `ica.n_components_ > 0` and `ica.fit()` completes without error on a dummy MNE Epochs object.
- [ ] T011 [US1] Write integration test `test_full_preprocessing_pipeline` in `tests/integration/test_pipeline.py` that asserts `len(output_df.columns) == 30` and `output_df.isna().sum().sum() == 0` after running the pipeline on 5 dummy participants. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T011a [US1] Implement `code/data_loader.py` function to verify the existence of the OpenNeuro dataset ID **resolved in `research.md`** and the presence of heat-pain threshold labels. If the dataset is missing or labels are absent, raise an explicit error to halt execution. <!-- FAILED: unspecified -->
- [X] T012 [US1] Implement `code/data_loader.py` function to fetch the OpenNeuro dataset ID **resolved in `research.md`** (using `mne.datasets` or direct URL) and save to `data/raw/`. <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement EEG preprocessing in `code/preprocessing.py`: re-reference to **average mastoids**, band-pass filter **1–40 Hz**, and apply ICA for ocular/muscle removal.
- [X] T014 [US1] Implement participant exclusion logic in `code/preprocessing.py`: exclude if < 4 minutes of valid EEG data remains after ICA artifact removal and bad channel interpolation, log warning.
- [X] T015 [US1] Implement microstate segmentation in `code/preprocessing.py` to extract canonical maps (A, B, C, D).
- [X] T016 [US1] Implement feature extraction in `code/preprocessing.py`: calculate **exactly 30 features** per participant: 4 mean durations, 4 occurrence rates, 16 transition probabilities (4x4 matrix flattened), and 6 spectral power features (delta, theta, alpha, beta, low-gamma, high-gamma). Ensure no NaN values are produced.
- [ ] T017 [US1] Implement `code/main.py` step to aggregate features into `data/processed/feature_matrix.csv` with a defined set of columns. Add explicit assertion: `assert len(df.columns) == 30` before saving. Ensure column order is: mean durations, occurrence rates, transition probabilities, and spectral power features.
- [X] T018 [US1] Add validation in `code/preprocessing.py` to ensure heat-pain threshold labels are present, numeric, and convert to °C if units differ (e.g., Kelvin or Fahrenheit) using a standard conversion factor.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train Elastic Net with nested 5-fold CV, perform a permutation test *globally* before the outer loop as per FR-004, and report Pearson r with bootstrap CI.

**Independent Test**: Running the training script produces a cross-validated Pearson r, a bootstrap confidence interval, and an empirical p-value from the global permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for nested CV loop structure in `tests/unit/test_modeling.py`
- [X] T020 [P] [US2] Integration test for global permutation test logic in `tests/integration/test_permutation.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/modeling.py` function for Elastic Net (α=0.5) with nested k-fold cross-validation.
- [ ] T022 [US2] Implement **global** permutation test in `code/modeling.py`: **Iterate a sufficient number of times to ensure convergence.**: shuffle labels globally (once per iteration), then run the nested CV loop on the shuffled labels to generate a null distribution, ensuring valid null hypothesis per FR-004. Use random seed = `global_seed` for reproducibility.
- [ ] T023 [US2] Implement bootstrap resampling (a sufficient number of iterations) to calculate a confidence interval for Pearson r.
- [ ] T024 [US2] Implement calculation of empirical p-value comparing observed r against null distribution from global permutations.
- [ ] T025 [US2] Implement convergence check in `code/modeling.py`: if Elastic Net fails to converge, increase `max_iter` to a sufficiently large value to ensure convergence.; if still failing, raise explicit error.
- [ ] T026 [US2] Implement `code/main.py` step to train model, generate `artifacts/model_result.json` (r, p-value, MAE, CI), log execution time using T026a, and verify total time < 6 hours (GitHub Actions free-tier limit per SC-005).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Rigor and Sensitivity Analysis (Priority: P3)

**Goal**: Perform FDR correction on **permutation importance** scores, VIF diagnostics, and dual sensitivity analysis (median-split + regularization sweep).

**Independent Test**: The analysis report includes FDR-adjusted p-values, VIF flags, and sensitivity analysis results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for FDR correction logic on permutation scores in `tests/unit/test_diagnostics.py`
- [ ] T028 [P] [US3] Unit test for VIF calculation in `tests/unit/test_diagnostics.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/diagnostics.py` function to calculate **permutation importance scores** for all features (shuffling each feature individually).
- [ ] T030 [US3] Implement FDR correction in `code/diagnostics.py`: apply Benjamini-Hochberg to the **p-values derived from permutation importance** (T029).
- [ ] T031 [US3] Implement VIF calculation in `code/diagnostics.py` using `statsmodels`; flag any predictors with VIF > 10 in the diagnostic output, but do NOT exclude them or re-run the model.
- [ ] T032 [US3] Implement median-split sensitivity analysis in `code/diagnostics.py`: sweep the median-split threshold on the **observed heat-pain threshold labels** (ground truth) by testing the specific set **[median-0.1, median-0.05, median, median+0.05, median+0.1]**, calculate **Cohen's d** as the effect size for each step, and report the variation in effect size estimates.
- [ ] T033 [US3] Implement regularization sensitivity analysis in `code/diagnostics.py`: sweep α from a low value to the upper bound of the parameter range with a step size and report R-squared stability.
- [ ] T034 [US3] Generate `artifacts/diagnostics_report.md` containing FDR table, VIF flags, and sensitivity analysis plots/tables.
- [ ] T035 [US3] Update `code/main.py` to orchestrate diagnostics, record all artifact hashes, and verify total execution time < 6 hours.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update `README.md` with installation instructions and usage examples
- [ ] T036b [P] Create `docs/api.md` with function signatures for `code/` modules
- [ ] T036c [P] Create `docs/analysis.md` explaining the statistical methodology (global permutation, FDR on importance, dual sensitivity)
- [ ] T037a [P] Extract validation logic into separate module `code/validation.py`
- [ ] T037b [P] Remove dead code and unused imports in `code/`
- [ ] T038a [P] Profile pipeline to identify performance bottlenecks
- [ ] T038b [P] Implement caching for feature extraction to optimize runtime
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 Run `scripts/pre-run-validation.sh` to verify citations and project state
- [ ] T041 Final validation: Ensure `data/processed/feature_matrix.csv` has exactly 30 columns, no NaNs, and `artifacts/` contains all required reports.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 feature matrix
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model results

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
Task: "Write unit test test_ica_artifact_removal in tests/unit/test_preprocessing.py"
Task: "Write integration test test_full_preprocessing_pipeline in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement EEG preprocessing in code/preprocessing.py"
Task: "Implement microstate segmentation in code/preprocessing.py"
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