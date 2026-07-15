# Tasks: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project structure: Execute `mkdir -p data/raw data/processed data/results code/ tests/ state/` to initialize directories per implementation plan.
- [ ] T002a [P] Create Python virtual environment: Run `python3.11 -m venv venv` in repository root.
- [X] T002b [P] Create requirements.txt: Initialize `code/requirements.txt` file.
- [X] T002c [P] Pin dependencies: Add exact versions to `code/requirements.txt` for: nilearn, networkx, scikit-learn, pandas, matplotlib, nibabel, scipy, pytest, dask, distributed.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils.py` logging: Add `setup_logger()` function returning a logger writing to `data/preprocess_log.txt` and `data/analysis_log.txt` with ISO timestamps.
- [X] T004b [P] Implement `code/utils.py` RNG: Add `get_seeded_rng(seed=42)` function returning a numpy.random.Generator with pinned seed for reproducibility.
- [ ] T004c [P] Implement `code/utils.py` QC: Add `check_fd(fd_value, threshold=0.5)` returning boolean and `log_exclusion(reason, subject_id)` functions.
- [ ] T007 Create data schema definitions: Create `contracts/dataset.schema.yaml`, `contracts/metric.schema.yaml`, and `contracts/result.schema.yaml` defining the JSON/YAML schemas for all data artifacts.
- [X] T008 Create base Subject entity model: Implement `code/models.py` with a `Subject` class containing attributes: `id` (str), `fMRI_path` (str), `DSST_score` (float or None), `qc_metrics` (dict). **MUST include** `has_valid_data()` method returning `True` only if `fMRI_path` exists and `DSST_score` is not `None`.
- [X] T006 [P] Implement `code/download.py` with HCP data retrieval logic, checksum verification, and status-based availability checking (no exceptions for missing data).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download HCP fMRI/behavioral data and preprocess fMRI using fMRIPrep (or fail gracefully with "Data Gap" if real data is missing/unavailable on CI).

**Independent Test**: The pipeline is tested by executing the download and preprocessing script on a 1-2 subject subset. The system must verify that output NIfTI files exist in MNI space with motion correction, consuming ≤ 2 CPU cores and ≤ 7 GB RAM, AND verify that output files pass fMRIPrep QC metrics (motion < 0.5mm). If real data is missing, the system must fail gracefully by skipping preprocessing and logging 'N/A - Data Unavailable' rather than crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for download logic: Add `tests/unit/test_download.py::test_download_retries_on__error` verifying multiple retries on HTTP 404 and raising `ConnectionError` on final failure.
- [~] T010 [P] [US1] Unit test for fMRIPrep wrapper validation: Add `tests/unit/test_preprocess.py::test_fmriprep_invocation_logs_hash` verifying that a mock call logs the container hash to `data/preprocess_log.txt`.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/download.py` to fetch HCP resting-state fMRI and behavioral datasets from verified URLs, including retry logic (A limited number of attempts.) and checksum verification. **MUST use** `setup_logger()` from T004.
- [X] T012 [US1] Implement `verify_fMRI_availability()` in `code/download.py`: Check for existence of fMRI time-series files. **MUST return** a status object: `{'status': 'PRESENT'}` or `{'status': 'MISSING', 'reason': 'Data Gap: fMRI time-series not found'}`. **DO NOT** raise exceptions; return status to allow graceful handling.
- [~] T012b [US1] Implement Main Runner Logic in `code/main.py` (or `code/download.py`): Add logic to call `verify_fMRI_availability()`. **IF** status is 'MISSING', log "N/A - Data Unavailable" to `data/preprocess_log.txt`, skip all preprocessing tasks (T013, T014), and exit gracefully. **IF** status is 'PRESENT', proceed to T013.
- [~] T013 [US1] Implement `code/preprocess.py` to invoke fMRIPrep container (version specified in plan.md) with flags: `--motion-correction --slice-timing --MNI --nuisance-regression`. **MUST check** T012b status first; if 'MISSING', skip execution. Support cluster mode (`--mode cluster`) and CI subset mode (`--mode ci`) via CLI argument or `MODE` env variable. Log container hash and full command to `data/preprocess_log.txt`.
- [~] T014 [US1] Implement QC validation in `code/preprocess.py`: Run `check_fd()` on output files; exclude subjects with FD > 0.5mm and log exclusion reasons to `data/preprocess_log.txt`. **MUST check** T012b status first; if 'MISSING', skip execution.
- [~] T015 [US1] Apply `setup_logger()` usage in `code/download.py` and `code/preprocess.py`: Ensure all download and preprocessing operations log to `data/preprocess_log.txt` using the logger from T004.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (or correctly skip with 'N/A' if data is missing)

---

## Phase 4: User Story 2 - Network Reconfigurability Metric Computation (Priority: P2)

**Goal**: Compute sliding-window functional connectivity matrices and extract network reconfigurability metrics (community state transitions) for each subject.

**Independent Test**: The module is tested by running it on a single preprocessed subject (or synthetic data for logic only) and verifying that the output JSON contains the network reconfigurability metric with valid numerical ranges (transitions >= 0), completing within 30 minutes on 2 CPU cores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for sliding-window correlation logic: Add `tests/unit/test_metrics.py::test_sliding_window_correlation_shapes` verifying output matrix shape matches expected (n_windows, n_parcels, n_parcels) for synthetic input.
- [X] T017 [P] [US2] Unit test for Louvain algorithm convergence: Add `tests/unit/test_metrics.py::test_louvain_retry_on_failure` verifying multiple retries with different seeds and exclusion on final failure.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `code/metrics.py` `compute_sliding_window()` to generate functional connectivity matrices (s window, small step) using the Schaefer parcellated atlas.
- [X] T019 [US2] Implement `code/metrics.py` `extract_reconfigurability()` using Louvain community detection with `get_seeded_rng(42)`, A retry logic mechanism will be implemented to handle transient failures. The research question focuses on determining the optimal retry strategy for system resilience. The method involves simulating network instability scenarios to evaluate recovery performance. References include prior work on fault tolerance patterns []. for convergence failure, and subject exclusion logging.
- [~] T020 [US2] Implement extraction of network reconfigurability metric (community state transition count) and save to `data/results/metrics_{subject_id}.json` with keys: `subject_id`, `transition_count`.
- [~] T020a [US2] Implement `code/metrics.py` `aggregate_metrics_to_tsv()` to convert all JSON metric files into a single TSV file `data/processed/metrics_aggregated.tsv` (intermediate step) with columns: `subject_id`, `transition_count`.
- [X] T021 [US2] Implement QC check in `code/metrics.py` to exclude subjects with excessive motion (FD > 0.5mm) before metric computation using `check_fd()`.
- [ ] T022 [US2] Add logging for metric computation steps and exclusion reasons in `data/metrics_log.txt`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform Spearman correlations between reconfigurability metrics and DSST scores, apply Bonferroni correction, and generate scatter plots with confidence intervals.

**Independent Test**: The analysis module is tested by running it against a synthetic dataset of subjects with known correlation properties, verifying that the reported p-values and effect sizes match expected values within A strict convergence tolerance., and that plots are generated without error.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for Spearman correlation: Add `tests/unit/test_analysis.py::test_spearman_correlation_known_values` verifying coefficient and p-value match expected values for mock data within 1e-6.
- [X] T024 [P] [US3] Unit test for visualization: Add `tests/unit/test_viz.py::test_scatter_plot_generation` verifying that a PNG file is created and contains a trendline for mock data.

### Implementation for User Story 3

- [X] T025 [P] [US3] Implement `code/analysis.py` `compute_spearman()` to perform Spearman rank correlations between `transition_count` and `DSST_score`.
- [~] T025b [US3] Implement Subject Filtering in `code/analysis.py`: Add logic to iterate through subjects and **exclude** any where `Subject.has_valid_data()` returns `False` (missing `DSST_score` or `fMRI_path`). Log the count of excluded subjects to `data/analysis_log.txt` as per FR-005.
- [X] T026 [US3] Implement Bonferroni correction in `code/analysis.py` `apply_bonferroni()` to adjust p-values for multiple comparisons and report adjusted p-values.
- [ ] T027 [US3] Implement calculation of effect sizes (Cohen's r) and handling of extreme p-values (floor/ceiling at a predefined threshold) in `code/analysis.py`.
- [ ] T028 [US3] Save **Aggregated Statistical Summary** to `data/analysis_results.tsv`. **MUST** be one row per metric-behavior pair (aggregated statistics), NOT per subject. **Header**: `metric_pair\tcoef\tp_val\tadj_p\teffect_size`. (No `subject_id` column).
- [ ] T029 [US3] Implement `code/viz.py` `generate_scatter_plot()` to create scatter plots with confidence intervals and effect size annotations.
- [ ] T030 [US3] Save scatter plots as PNG files in `data/results/` with filenames `plot_{metric}_{behavior}.png`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Permutation Testing Validation (Priority: P3)

**Goal**: Perform permutation testing (A sufficient number of shuffles) to validate the significance of observed correlations against a null distribution.

**Independent Test**: The module is tested by running it on a dataset where the null hypothesis is known to be true (shuffled data), verifying that the p-value distribution is uniform and the observed p-value is not significant (p > 0.05).

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US4] Unit test for permutation testing: Add `tests/unit/test_analysis.py::test_permutation_null_distribution` verifying that shuffled data yields p > 0.05 for A sufficient number of shuffles.

### Implementation for User Story 4

- [ ] T032 [P] [US4] Implement permutation testing in `code/analysis.py` `run_permutation_test()` with A sufficient number of shuffles, random seed, shuffling DSST scores while keeping metrics fixed.
- [ ] T033 [US4] Calculate permutation-derived p-values in `code/analysis.py` by comparing observed correlation to the null distribution generated by T032.
- [ ] T034 [US4] Save permutation test raw results and null distribution data to `data/results/permutation_results.tsv`.
- [ ] T035 [US4] Generate Permutation Test Report: Create a visual report (PDF/PNG) in `data/results/` visualizing the null distribution histogram and highlighting the observed statistic, satisfying SC-005.
- [ ] T036 [US4] Add logging for permutation test execution and results in `data/analysis_log.txt`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update README.md: Add CLI usage examples and installation instructions for `code/` and `data/`.
- [ ] T037a Code cleanup: Refactor `code/metrics.py` to remove duplicate imports and ensure consistent variable naming.
- [ ] T038 Performance optimization for sliding-window calculations
- [ ] T039 [P] Additional unit tests for edge cases (missing data, convergence failures) in `tests/unit/`
- [ ] T040 Run quickstart.md validation to ensure end-to-end pipeline execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (preprocessed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (metrics)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US3 output (correlation results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
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
Task: "Unit test for download logic with mock HTTP responses in tests/unit/test_download.py"
Task: "Unit test for fMRIPrep wrapper validation (mocked execution) in tests/unit/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Create base Subject entity model in code/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify "Data Gap" handling or successful preprocessing)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 & 4
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
- **Critical**: Do NOT generate synthetic fMRI data for hypothesis testing. If real data is missing, the pipeline must skip preprocessing and log 'N/A - Data Unavailable' (via T012b), not crash. Synthetic data is ONLY for unit tests.