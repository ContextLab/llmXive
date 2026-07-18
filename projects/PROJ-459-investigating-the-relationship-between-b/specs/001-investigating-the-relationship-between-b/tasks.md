# Tasks: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

**Input**: Design documents from `/specs/001-brain-music-preference/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `state/`). Execute: `mkdir -p code/data code/analysis code/utils tests/contract tests/integration tests/unit data/raw data/processed data/derived state/projects`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions: `nilearn==0.10.1`, `networkx==3.2.1`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `scipy==1.11.4`, `pyyaml==6.0.1`, `pytest==7.4.3`, `statsmodels==0.14.0`, `nibabel==5.2.0`.
- [X] T003 [P] Configure linting and formatting tools. Create `.flake8` (max-line-length=100, exclude=venv) and `pyproject.toml` (black config). Execute verification: `black --check.` and `flake8 code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with paths, hyperparameters (window sizes, TRs), and dataset IDs (ds000030, ds000208). Include a mechanism to switch dataset IDs if validation fails.
- [X] T005 [P] Implement `code/utils/atlas.py` to load Schaefer atlas and map ROIs to Yeo 7-network parcellation (DMN=7, Auditory=4, Salience=2). Define `load_atlas()` and `map_to_yeo()` functions.
- [X] T006 [P] Implement `code/utils/io.py` for checksums, JSON/Parquet handling, and directory creation. Define `compute_checksum()`, `save_parquet()`, `load_json()`.
- [X] T007 Create base data models/entities in `code/data/models.py` using Pydantic. Define `Subject` (id: str, genre_scores: dict), `TimeSeries` (roi_id: str, values: list[float]), `NetworkMetric` (subject_id: str, metric_name: str, value: float), `CorrelationResult` (metric: str, genre: str, r: float, p_raw: float, p_adj: float), `SensitivityReport` (window_size: int, icc: float).
- [X] T008 [P] Configure Docker environment validation script in `code/utils/docker.py` (moved from preprocess.py to separate validation unit). Define `validate_docker_daemon()` and `check_fmriprep_image()` to ensure environment readiness before any heavy compute.
- [ ] T009 Setup environment configuration management for memory limits and runtime caps. Define `check_memory_limit()` and `set_runtime_cap()`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and validate fMRI/behavioral data, preprocess with fMRIPrep, and extract regional time courses.

**Independent Test**: The pipeline can be tested by verifying the existence of preprocessed BOLD time series files and a merged CSV containing subject IDs, network metrics (placeholder), and genre preference scores for a subset of subjects (e.g., 10 subjects), AND verifying that the system correctly flags or falls back when the primary behavioral variable is missing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data validation schema in `tests/contract/test_data_validation.py`. Implement `test_schema_validates_musical_genre_field()` and `test_schema_falls_back_to_stomp_r()`. <!-- SKIPPED: non-mapping output -->
- [X] T011 [P] [US1] Integration test for fMRIPrep wrapper in `tests/integration/test_fmriprep_wrapper.py`. Implement `test_fmriprep_runs_on_mock_data()` and `test_fmriprep_handles_memory_error()`. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/download.py` to download resting-state fMRI data from OpenNeuro (ds000030, ds000208) using `requests` or `bids-validator` logic. Define `download_dataset(dataset_id: str, output_dir: str)`.
- [X] T012e [US1] Implement `code/data/validate.py` to dynamically validate dataset IDs against a verified list of datasets containing required behavioral variables. If a hardcoded ID (e.g., ds000030) is not in the verified list, halt with `ERR_INVALID_DATASET` and log the specific missing variable. Define `validate_dataset_id()`.
- [X] T012c [US1] Implement `code/data/validate.py` to perform comprehensive data integrity checks:
 1. Check sample size N >= 85 (Hard Gate). If N < 85, log `ERR_UNDERPOWERED` and halt execution unconditionally. No bypass for 'Spec Amendment' is permitted.
 2. Verify dataset variable availability: Check `participants.tsv` for 'musical_genre'. If missing, attempt fallback to 'STOMP-R'. If both missing, halt with `DataValidationError` (code `ERR_DATA_MISSING`). Log specific missing field name.
 3. Verify the dataset source matches the Constitution's Verified Accuracy principle (check against a verified list of datasets).
 Define `check_data_integrity()`.
- [X] T016 [P] [US1] Implement `code/data/validate.py` to check for 'musical_genre' or 'STOMP-R' in `participants.tsv`; halt with `DataValidationError` (code `ERR_DATA_MISSING`) if missing. Log specific missing field name. (Integrated into T012c logic, but kept as separate task for testability of specific validation step).
- [ ] T017 [P] [US1] Add validation logic to exclude subjects with >10% missing behavioral data or >10% corrupted fMRI volumes. Define `exclude_subjects_by_missing_data()`.
- [ ] T018 [P] [US1] Add logic to flag/exclude subjects with excessive head motion (>0.5mm FD). Define `exclude_subjects_by_motion()`.
- [X] T014 [US1] Depends: T008, T012c, T012e. Implement `code/data/preprocess.py` to run fMRIPrep (Docker) with memory limits and generate standardized BOLD/confounds. Command args: `--output-space MNI152NLin2009cAsym --confounds trans_x,trans_y,trans_z,rot_x,rot_y,rot_z,framewise_displacement,dvars`. Define `run_fmriprep(subject_id: str)`.
- [X] T015 [US1] Depends: T005, T014. Implement `code/data/preprocess.py` to extract regional time courses using Schaefer-400 atlas (400 ROIs × timepoints). Define `extract_time_series(subject_id: str)`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static and Dynamic Network Metric Computation with Sensitivity Analysis (Priority: P2)

**Goal**: Compute static/dynamic network metrics and perform sensitivity analysis on sliding-window parameters.

**Independent Test**: The computation can be tested by running the metric calculation on a small synthetic time-series dataset and verifying that the output CSV contains the expected columns (e.g., `global_efficiency`, `modularity_Q`, `dynamic_reconfiguration_rate`) with numeric values within plausible ranges. The sensitivity analysis is tested by verifying that the system runs the pipeline with window sizes of 20, 30, and 40 TRs and reports the correlation stability of the resulting metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for metric calculation outputs in `tests/contract/test_metric_schema.py`. Implement `test_metric_schema_has_required_columns()` and `test_metric_values_in_range()`.
- [X] T020 [P] [US2] Integration test for sliding-window analysis in `tests/integration/test_sliding_window.py`. Implement `test_sliding_window_produces_time_series()` and `test_sensitivity_analysis_reports_icc()`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/analysis/metrics.py` to calculate static functional connectivity matrices (400x400 correlation). Define `compute_static_connectivity(time_series: np.array)`.
- [X] T022 [US2] Implement `code/analysis/metrics.py` to derive static network metrics (global efficiency, modularity, within-module degree) for DMN, Auditory, Salience networks. Define `compute_static_metrics(matrix: np.array, network_map: dict)`.
- [X] T023 [US2] Implement `code/analysis/metrics.py` for sliding-window dynamic connectivity (window=30 TRs, step=5 TRs). Define `compute_dynamic_connectivity(time_series: np.array, window_size: int, step: int)`.
- [X] T024 [US2] Implement `code/analysis/metrics.py` to calculate dynamic reconfiguration rate from sliding-window matrices. Define `compute_reconfiguration_rate(dynamic_matrices: list[np.array])`.
- [X] T025 [US2] Depends: T015. Implement `code/analysis/metrics.py` to regress out FD/DVARS from time series before dynamic analysis using `sklearn.linear_model.LinearRegression`. Output format: CSV with timepoints and residuals. Define `regress_confounds(time_series: np.array, confounds: np.array)`.
- [X] T026 [US2] Implement `code/analysis/metrics.py` to run sensitivity analysis with window sizes 30, 40 TRs. Define `run_sensitivity_analysis(time_series: np.array, window_sizes: list[int])`.
- [X] T027 [US2] Implement `code/analysis/metrics.py` to calculate Intraclass Correlation Coefficient (ICC) for dynamic metrics across window sizes. Define `compute_icc(metrics: list[float])`.
- [ ] T028 [US2] Generate `SensitivityReport` JSON/Parquet with stability metrics and ICC values. Save to `data/derived/sensitivity_report.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation, Power Analysis, and Visualization (Priority: P3)

**Goal**: Perform Spearman correlations, Benjamini-Hochberg correction, power analysis, and generate visualizations.

**Independent Test**: The analysis can be tested by running the correlation module on a mock dataset with known correlations and verifying that the output table correctly identifies significant correlations (p<0.05) and that the Benjamini-Hochberg adjusted p-values are calculated correctly. Power analysis is tested by verifying the system reports the achieved power (≥0.8) for the sample size and effect size observed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for statistical output schema in `tests/contract/test_stats_schema.py`. Implement `test_stats_schema_has_required_columns()` and `test_bh_correction_applied()`.
- [ ] T030 [P] [US3] Integration test for null distribution validation in `tests/integration/test_null_distribution.py`. Implement `test_null_distribution_false_positive_rate()`.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `code/analysis/stats.py` to perform Spearman correlations between network metrics and genre preference scores. Define `compute_spearman_correlations(metrics: pd.DataFrame, genres: pd.Series)`.
- [ ] T032 [US3] Implement `code/analysis/stats.py` to apply Benjamini-Hochberg correction to raw p-values. Define `apply_bh_correction(p_values: list[float])`.
- [ ] T033 [US3] Implement `code/analysis/stats.py` to perform post-hoc power analysis (target: power ≥ 0.8 for |r| ≥ 0.3). Define `compute_power(sample_size: int, effect_size: float)`.
- [ ] T034 [US3] Implement `code/analysis/stats.py` to run null distribution validation (A large number of permutations) to verify false positive rate ≤ 0.05. Generate `data/derived/null_validation_report.json` with keys: `false_positive_rate`, `permutations_count`.
- [ ] T035 [US3] Implement `code/analysis/stats.py` to flag results as 'Underpowered' if power < 0.8. Define `flag_underpowered(power: float)`.
- [ ] T036 [US3] Implement `code/analysis/viz.py` to generate correlation heatmap (PNG/PDF). Save to `data/derived/correlation_heatmap.png`.
- [ ] T037 [US3] Implement `code/analysis/viz.py` to generate network diagrams highlighting significant connections (adjusted p < 0.05). Save to `data/derived/network_diagram.png`.
- [ ] T038 [US3] Implement `code/main.py` to orchestrate the full pipeline with error handling for `ERR_UNDERPOWERED` (log warning, require spec amendment, halt if not amended) and `ERR_DATA_MISSING`. Define CLI interface with exit codes.
- [ ] T038a [US3] [P] Implement `code/main.py` CLI argument parsing and pipeline orchestration logic.
- [ ] T038b [US3] [P] Implement `code/main.py` final report generation logic to produce `data/derived/final_results.csv`.
- [ ] T039 [US3] Generate final results CSV with all metrics, correlations, and p-values. Save to `data/derived/final_results.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` and `README.md`. Update sections: 'Installation', 'Usage', 'Data Sources', 'Validation'.
- [ ] T041 Code cleanup and refactoring
- [ ] T042 Performance optimization across all stories (ensure CPU-only, no GPU dependencies)
- [ ] T043 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T044 Security hardening (Docker image scanning, dependency checks)
- [ ] T045 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metric output

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
Task: "Contract test for data validation schema in tests/contract/test_data_validation.py::test_schema_validates_musical_genre_field"
Task: "Integration test for fMRIPrep wrapper in tests/integration/test_fmriprep_wrapper.py::test_fmriprep_runs_on_mock_data"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to download resting-state fMRI data from OpenNeuro"
Task: "Implement code/data/validate.py to check for 'musical_genre' or 'STOMP-R'"
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