# Tasks: Neural Correlates of Error Monitoring During Simulated Navigation

**Input**: Design documents from `/specs/001-neural-correlates-error-monitoring/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `android/src/`
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

- [X] T001 [P] Create root directory `projects/PROJ-530-neural-correlates-of-error-monitoring-du/`
- [ ] T002 [P] Create data directories: `projects/PROJ-530-neural-correlates-of-error-monitoring-du/data/raw/`, `projects/PROJ-530-neural-correlates-of-error-monitoring-du/data/processed/` <!-- ATOMIZE: requested -->
- [X] T003 [P] Create results and code directories: `projects/PROJ-530-neural-correlates-of-error-monitoring-du/results/models/`, `projects/PROJ-530-neural-correlates-of-error-monitoring-du/results/figures/`, `projects/PROJ-530-neural-correlates-of-error-monitoring-du/results/diagnostics/`, `projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/`, `projects/PROJ-530-neural-correlates-of-error-monitoring-du/tests/`
- [X] T004 [P] Initialize Python 3.11 project with dependencies: `mne`, `pandas`, `numpy`, `scipy`, `statsmodels`, `pymer4`, `pingouin`, `matplotlib`, `seaborn`, `pyyaml`, `psutil`, `pytest`, `pygam`
- [X] T005 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create `code/__init__.py` and base configuration loader
- [~] T007 [P] Implement random seed pinning utility in `code/utils.py` (global seed for numpy, python random, torch if used)
- [~] T008 Create `state/projects/PROJ-530-neural-correlates-of-error-monitoring-du.yaml` for artifact tracking
- [~] T009 Setup logging infrastructure to `data/preprocessing.yaml` and console

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Primary Analysis: MFN Amplitude vs. Error Magnitude (Priority: P1) 🎯 MVP

**Goal**: Ingest the Navigation Error Corpus, preprocess EEG (filtering, ICA), extract MFN features, calculate error magnitude, and fit the primary mixed-effects model.

**Independent Test**: Run the pipeline on a subset (N=5) and verify a valid model summary (coefficients, p-values) is outputted without runtime errors.

### Implementation for User Story 1

- [~] T010 [US1] Implement `code/download.py` (FR-001): Fetch Navigation Error Corpus from Zenodo URL. **CRITICAL**: If the Zenodo URL is missing or invalid, generate a synthetic EEG/trajectory dataset for local testing purposes only, log a clear warning, and proceed. Do NOT halt the pipeline. Verify checksum and cache in `data/raw/` if real data is available.
- [~] T011 [US1] Implement `code/preprocess.py` (FR-002): Apply bandpass and line-frequency notch filters to raw EEG data.
- [~] T012 [US1] Implement `code/preprocess.py` (FR-002): Run ICA to remove ocular/muscular artifacts; log components removed to `data/preprocessing.yaml`.
- [~] T013 [US1] Implement `code/preprocess.py` (FR-003): Calculate directional error magnitude (angular deviation in degrees) for each error event using heading vs. optimal path vectors.
- [~] T014 [US1] Implement `code/preprocess.py` (FR-004): Extract MFN epochs (-200ms to 800ms), baseline-correct (-200ms to 0ms), and compute **MEAN Amplitude** (average of samples in 200-400ms window) at FCz, Cz, Fz as the PRIMARY metric per plan.md. Compute Peak (most negative) amplitude as a secondary metric only.
- [~] T015 [US1] Implement `code/analysis.py` (FR-005): Fit Linear Mixed-Effects Model (MFN ~ error_magnitude + (1|participant)) using `statsmodels`.
- [~] T016 [US1] Implement `code/analysis.py` (FR-005): Add GAM fallback logic (test linearity; if non-linearity rejected, fit GAM using `pygam` and compare via AIC).
- [~] T017 [US1] Implement `code/viz.py`: Generate scatter plot (MFN amplitude vs. error magnitude) with regression line overlay.
- [~] T018 [US1] Implement `code/analysis.py`: Save model summary to `results/models/`. **Ensure** `results/diagnostics/feasibility_report.json` is generated with runtime/memory metrics *after* model fitting completes. If `runtime_seconds > 21600` or `peak_memory_mb > 7168`, raise a `FeasibilityError` and halt, satisfying SC-005 measurement requirements.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation tasks are complete**

- [~] T019 [P] [US1] Unit test `tests/test_preprocess.py::test_angular_deviation_handles_zero_vectors`: Verify that `calculate_angular_deviation` logs a warning and returns `None` when input vectors are zero-length.
- [~] T020 [P] [US1] Unit test `tests/test_preprocess.py::test_mfn_extraction_mean_vs_peak`: Verify that `extract_mfn_features` returns a `mean_amplitude` value that is the average of the window and a `peak_amplitude` value that is the minimum, ensuring both are calculated correctly.
- [~] T021 [P] [US1] Integration test `tests/test_integration.py::test_full_preprocessing_pipeline_subset`: Run the full preprocessing pipeline on a synthetic subset (N=5) and verify that `data/processed/` contains epoch files and `data/preprocessing.yaml` is populated with filter/ICA parameters.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Methodological Robustness: Sensitivity Analysis on Thresholds (Priority: P2)

**Goal**: Perform a sensitivity sweep on the minimum error magnitude threshold to ensure the primary finding is not an artifact of a single arbitrary cutoff.

**Independent Test**: Run the sensitivity sweep script and verify it produces a table/plot showing correlation coefficients and p-values across thresholds representing a range of values.

### Implementation for User Story 2

- [~] T022 [US2] Implement `code/analysis.py` (FR-006): Create sensitivity sweep function iterating over thresholds across a range of values.
- [~] T023 [US2] Implement `code/analysis.py` (FR-006): For each threshold, filter error events, refit the primary model, and record correlation coefficient and p-value.
- [~] T024 [US2] Implement `code/viz.py`: Generate sensitivity analysis summary table and plot (threshold vs. significance/correlation).
- [~] T025 [US2] Implement `code/analysis.py`: Write sensitivity results to `results/diagnostics/sensitivity_summary.csv` **unconditionally**. **CRITICAL**: Do NOT raise an error or halt the pipeline if the correlation is not significant across the majority of thresholds. The analysis must complete and output the data regardless of the statistical outcome to satisfy SC-002 measurement requirements.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T026 [P] [US2] Unit test `tests/test_analysis.py::test_threshold_filtering_logic`: Verify that filtering events with `threshold=10` correctly excludes events with `error_magnitude < 10`.
- [~] T027 [P] [US2] Integration test `tests/test_integration.py::test_sensitivity_sweep_output_format`: Run the sensitivity sweep on a subset and verify that `results/diagnostics/sensitivity_summary.csv` contains exactly 4 rows (one per threshold) with valid columns for `threshold`, `correlation`, and `p_value`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation: Collinearity and Multiplicity Checks (Priority: P3)

**Goal**: Validate statistical assumptions (collinearity) and correct for multiple comparisons to ensure valid inference framing.

**Independent Test**: Verify VIF < 5 for all predictors and that adjusted p-values are correctly computed for multiple electrodes.

### Implementation for User Story 3

- [~] T028 [US3] Implement `code/analysis.py` (FR-007): Calculate Variance Inflation Factors (VIF) for all behavioral predictors; flag if VIF ≥ 5.
- [ ] T029 [US3] Implement `code/analysis.py` (FR-008): Apply Bonferroni correction to p-values across tested electrodes (FCz, Cz, Fz).
- [ ] T030 [US3] Implement `code/analysis.py`: Generate diagnostic report in `results/diagnostics/validation_report.md` including VIF values, corrected p-values, and the exact phrase "associational" in the Conclusion section.
- [ ] T031 [US3] Implement `code/analysis.py`: Ensure the final report explicitly states the family-wise error rate control method used.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test `tests/test_analysis.py::test_vif_calculation`: Verify that `calculate_vif` returns a value < 5 for uncorrelated predictors and ≥ 5 for perfectly correlated predictors.
- [ ] T033 [P] [US3] Unit test `tests/test_analysis.py::test_bonferroni_correction`: Verify that `apply_bonferroni` correctly divides alpha by the number of tests and adjusts p-values accordingly.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T034 [P] [Polish] Update `README.md` with execution instructions and dependency list
- [ ] T035 [P] [Polish] Add `requirements.txt` with pinned versions
- [ ] T036 [Polish] Run full pipeline on N=5 subset to verify < 10 mins runtime
- [ ] T037 [Polish] Verify `results/diagnostics/feasibility_report.json` shows < 7GB RAM usage
- [ ] T038 [P] [Polish] Final review: Ensure all artifacts (plots, tables, reports) are generated in correct directories
- [ ] T039 [P] [Polish] Run `pytest` on all test modules to ensure **[deferred]** pass rate

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must complete before US2/US3** as they rely on its outputs.
- **User Story 2 (P2)**: Depends on US1 (needs the primary model logic and data preprocessing).
- **User Story 3 (P3)**: Depends on US1 (needs the model results to calculate VIF and correct p-values).

### Within Each User Story

- Implementation MUST precede tests (Producer before Consumer)
- Models/Download before preprocessing
- Preprocessing before analysis
- Core implementation before visualization
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
Task: "Unit test for angular deviation calculation in tests/test_preprocess.py::test_angular_deviation_handles_zero_vectors"
Task: "Unit test for MFN extraction in tests/test_preprocess.py::test_mfn_extraction_mean_vs_peak"

# Launch all implementation tasks for preprocessing (Sequential):
Task: "Implement code/download.py (FR-001)"
Task: "Implement code/preprocess.py (FR-002, FR-003, FR-004)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Download -> Preprocess -> Primary Model -> Viz)
4. **STOP and VALIDATE**: Test User Story 1 independently on N=5 subset.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Critical Path)
 - Developer B: Prepare Test Data / Documentation
 - Developer C: Prepare US2/US3 scaffolding (once US1 data flow is clear)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Warning**: All tasks must run on CPU-only CI with limited core and memory resources. Do not use GPU-accelerated libraries or 8-bit quantization. Use `mne`, `statsmodels`, and `pygam` exclusively.
- **Dataset Note**: Task T010 supports synthetic data fallback for local testing if the Zenodo URL is missing, ensuring the pipeline remains executable during development.