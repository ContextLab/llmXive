# Tasks: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Input**: Design documents from `/specs/001-pain-sensitivity-microstates/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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
- [X] T007 [P] Create `contracts/dataset.schema.yaml` and `contracts/features.schema.yaml` based on `plan.md` entities and validate them against the data model.
- [X] T008 Implement `code/data_loader.py` with `DataChunk` logic using `numpy.memmap` to handle limited RAM constraints. Ensure the data loading and preparation logic supports the extraction of exactly 30 features as defined in FR-002.
- [X] T009 Setup `code/config.py` for environment variables, path management, and define the constant `EXPECTED_FEATURE_COLUMNS` (list of 30 strings) matching FR-002.
- [X] T026a [P] Implement timing instrumentation in `code/utils.py`: function to measure duration of a specific step and **return the duration value** for aggregation. Do NOT assert global limit here.
- [X] T026b [P] Implement global timing wrapper in `code/main.py`: wrap the entire pipeline execution, sum durations from T026a, and assert `total_duration < 6 hours` at the end of the pipeline to enforce SC-005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest OpenNeuro ds003XXX, preprocess EEG (re-reference, filter, ICA), and extract microstate features per participant.

**Independent Test**: The pipeline can be executed end-to-end on a sample of participants; the output must be a CSV file containing a fixed set of features per participant and heat-pain threshold labels, with no NaN values.

### Validation & Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [US1] Write unit test `test_ica_artifact_removal` in `tests/unit/test_preprocessing.py` that asserts `ica.n_components_ > 0` and `ica.fit()` completes without error on a dummy MNE Epochs object.
- [X] T011 [US1] Write integration test `test_full_preprocessing_pipeline` in `tests/integration/test_pipeline.py` that asserts `len(output_df.columns) == 30` and `output_df.isna().sum().sum() == 0` after running the pipeline on a set of dummy participants. **Sub-task**: Generate dummy data in `data/dummy/` if it does not exist (e.g., random EEG signals with known structure).
- [X] T011b [US1] Write unit test `test_spectral_band_definitions` in `tests/unit/test_preprocessing.py` that asserts the calculated spectral power features match the exact frequency bands defined in FR-002 (Delta: 1-4Hz, Theta: 4-8Hz, Alpha: 8-13Hz, Beta: 13-30Hz, Low-Gamma: 30-50Hz, High-Gamma: 50-70Hz) and that the column names in the output match the expected set of 30 features.

### Implementation for User Story 1

- [X] T011a [US1] Implement `code/data_loader.py` function to verify the existence of the OpenNeuro dataset ID **resolved in `research.md`** and the presence of heat-pain threshold labels. If the dataset is missing or labels are absent, raise an explicit error to halt execution.
- [X] T012 [US1] Implement `code/data_loader.py` function to fetch the OpenNeuro dataset ID **resolved in `research.md`** (using `mne.datasets` or direct URL) and save to `data/raw/`.
- [X] T013 [US1] Implement EEG preprocessing in `code/preprocessing.py`: re-reference to **average mastoids**, band-pass filter **1–40 Hz**, and apply ICA for ocular/muscle removal.
- [X] T014 [US1] Implement participant exclusion logic in `code/preprocessing.py`: exclude if < 4 minutes of valid EEG data remains after ICA artifact removal and bad channel interpolation, log warning.
- [X] T015 [US1] Implement microstate segmentation in `code/preprocessing.py` to extract canonical maps (A, B, C, D).
- [X] T016 [US1] Implement feature extraction in `code/preprocessing.py`: calculate **exactly 30 features** per participant: 4 mean durations, 4 occurrence rates, 16 transition probabilities (4x4 matrix flattened), and 6 spectral power features (delta, theta, alpha, beta, low-gamma, high-gamma). **Explicitly define frequency bands**: Delta (1-4Hz), Theta (4-8Hz), Alpha (8-13Hz), Beta (13-30Hz), Low-Gamma (30-50Hz), High-Gamma (50-70Hz). Ensure no NaN values are produced.
- [X] T017 [US1] Implement `code/main.py` step to aggregate features into `data/processed/feature_matrix.csv`. Add explicit assertion: `assert set(df.columns) == config.EXPECTED_FEATURE_COLUMNS` (imported from `code.config`) AND `assert df.isna().sum().sum() == 0`. Ensure column order is: mean durations, occurrence rates, transition probabilities, and spectral power features.
- [X] T018 [US1] Add validation in `code/preprocessing.py` to ensure heat-pain threshold labels are present, numeric, and convert to °C if units differ (e.g., Kelvin or Fahrenheit) using a standard conversion factor.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train Elastic Net with nested 5-fold CV, perform a permutation test *within* the nested CV loop as per FR-004, and report Pearson r with bootstrap CI.

**Independent Test**: Running the training script produces a cross-validated Pearson r, a bootstrap confidence interval, and an empirical p-value from the permutation test performed within the CV structure.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for nested CV loop structure in `tests/unit/test_modeling.py`
- [X] T020 [P] [US2] Integration test for permutation test logic in `tests/integration/test_permutation.py`

### Implementation for User Story 2

- [X] T021 [US2] Create function `train_nested_cv` in `code/modeling.py` that: 1) Implements **nested k-fold cross-validation** (outer loop for testing, inner loop for hyperparameter tuning if needed), 2) Trains an **Elastic Net regression model** (α=0.5) on each training split, 3) Predicts on the test split, 4) Calculates the **Pearson correlation coefficient (r)** between predicted and observed heat-pain thresholds for each fold, and 5) Aggregates to a mean r. This task covers FR-003 and SC-001.
- [X] T022 [US2] Implement **nested permutation test** in `code/modeling.py`: Perform **exactly 1,000 permutations** to ensure statistical robustness as per FR-004. For each permutation: 1) **Shuffle the target labels Y within the current training split of the outer CV loop** (do NOT shuffle globally before the loop; the shuffle must happen inside the outer loop to test the full model structure including inner optimization). 2) Run the **full nested CV loop** on the shuffled data to get one correlation value. **Repeat this [deferred] times** to generate a null distribution of correlation values. **Do not dynamically reduce the number of permutations**; the 1,000 count is a hard requirement. This generates the null distribution artifact required for T024.
- [X] T023 [US2] Implement bootstrap resampling with **200 iterations** to calculate a 95% confidence interval for Pearson r. **Include logic**: If estimated runtime (based on dataset size) exceeds a substantial duration, reduce the number of bootstrap iterations to a sufficient level (but not lower). Record the CI in `artifacts/model_result.json`.
- [X] T024 [US2] Implement calculation of empirical p-value comparing observed r against the null distribution generated by T022. **Output**: Record the p-value in `artifacts/model_result.json` alongside r and MAE.
- [X] T025 [US2] Implement convergence check in `code/modeling.py`: if Elastic Net fails to converge, increase `max_iter` to 5000; if still failing, raise explicit error.
- [X] T026 [US2] Implement `code/main.py` step to train model, generate `artifacts/model_result.json` (r, p-value, MAE, CI), log execution time using T026a, and verify total time < 6 hours (GitHub Actions free-tier limit per SC-005) via T026b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Rigor and Sensitivity Analysis (Priority: P3)

**Goal**: Perform FDR correction on **permutation importance** scores, VIF diagnostics, and dual sensitivity analysis (median-split + regularization sweep).

**Independent Test**: The analysis report includes FDR-adjusted p-values, VIF flags, and sensitivity analysis results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for FDR correction logic on permutation scores in `tests/unit/test_diagnostics.py`
- [X] T028 [P] [US3] Unit test for VIF calculation in `tests/unit/test_diagnostics.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/diagnostics.py` function to calculate **permutation importance scores** for all features. For each feature: 1) Train the model on the full data, 2) Shuffle **only that feature's column** in the test set (or use a leave-one-out approach if appropriate for the metric), 3) Measure the drop in model performance (e.g., reduction in Pearson r) compared to the unshuffled baseline. Repeat the procedure multiple times to ensure a stable score. **Note**: This differs from shuffling the target Y; this measures feature contribution.
- [X] T030 [US3] Implement FDR correction in `code/diagnostics.py`: Calculate p-values for the **30 feature coefficients** by generating a null distribution for each coefficient (e.g., by permuting the feature against the target multiple times and comparing the observed coefficient to the null). Apply Benjamini-Hochberg to these **30 coefficient p-values** to control for multiplicity (FR-005). **Do not** apply FDR to permutation importance scores directly; apply it to the p-values derived from the coefficient null distributions.
- [X] T031 [US3] Implement VIF calculation in `code/diagnostics.py` using `statsmodels.stats.outliers_influence.variance_inflation_factor`; calculate VIF for all predictors and report any with VIF > 10 in the diagnostic output, but do NOT exclude them or re-run the model.
- [X] T032 [US3] Implement **median-split sensitivity analysis** in `code/diagnostics.py`:
 1. Calculate the median of the observed heat-pain threshold labels.
 2. Define a set of thresholds: `[median-0.1, median-0.05, median, median+0.05, median+0.1]`.
 3. For each threshold:
 - Split participants into "High Pain" (threshold < x) and "Low Pain" (threshold >= x) groups.
 - Perform a group comparison (e.g., t-test or effect size calculation like Cohen's d) on the top predictive features between these two groups.
 - Record the effect size and statistical significance.
 4. Report the variation in effect size estimates across the sweep to assess robustness against arbitrary cutoffs.
- [X] T033 [US3] Implement regularization sensitivity analysis in `code/diagnostics.py`: sweep α from **0.0 to 1.0** in steps of 0.05 and report R-squared stability. (Required by plan.md Complexity Tracking table and FR-003).
- [X] T034 [US3] Generate `artifacts/diagnostics_report.md` containing: 1) A **Markdown table** of FDR-adjusted p-values for the selected features, 2) A **JSON block** or table of VIF flags, 3) Tables/plots for the median-split and regularization sensitivity analyses. Ensure the report structure allows verification of SC-002, SC-003, and SC-004.
- [X] T035 [US3] Update `code/main.py` to orchestrate diagnostics, record all artifact hashes, and verify total execution time < 6 hours (via T026b).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update `README.md` with installation instructions and usage examples
- [X] T036b [P] Create `docs/api.md` with function signatures for `code/` modules
- [ ] T036c [P] Create `docs/analysis.md` explaining the statistical methodology (nested permutation, FDR on importance, dual sensitivity)
- [ ] T037a [P] Extract validation logic into separate module `code/validation.py`
- [ ] T037b [P] Remove dead code and unused imports in `code/`
- [ ] T038a [P] Profile pipeline to identify performance bottlenecks
- [ ] T038b [P] Implement caching for feature extraction to optimize runtime
- [ ] T039 [P] Additional unit tests in `tests/unit/`
- [ ] T040 Run `scripts/pre-run-validation.sh` to verify citations and project state
- [ ] T041 Final validation: Ensure `data/processed/feature_matrix.csv` has the expected number of columns corresponding to the selected feature set, with no missing values., and `artifacts/` contains all required reports.

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