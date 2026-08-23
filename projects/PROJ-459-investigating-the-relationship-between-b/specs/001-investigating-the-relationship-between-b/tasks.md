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

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `state/`). Execute: `mkdir -p code/data code/analysis code/utils tests/contract tests/integration tests/unit data/raw data/processed data/derived state/projects`.- [X] T002 Initialize Python 3.11 (Wikipedia: Python (programming language), https://en.wikipedia.org/wiki/Python_(programming_language)) project with `requirements.txt` containing pinned versions: `{{claim:c_49a81576}} (pi, https://en.wikipedia.org/wiki/Pi)`, `networkx==3.2.1 [UNRESOLVED-CLAIM: c_0a2a6823 — status=not_enough_info]`, `scikit-learn==1.3.2 [UNRESOLVED-CLAIM: c_f4fe278f — status=not_enough_info]`, `pandas==2.1.4 [UNRESOLVED-CLAIM: c_75d0cb2e — status=not_enough_info]`, `numpy==1.26.2 [UNRESOLVED-CLAIM: c_134965f0 — status=not_enough_info]`, `scipy==1.11.4 [UNRESOLVED-CLAIM: c_06f52ccd — status=not_enough_info]`, `pyyaml==6.0.1 [UNRESOLVED-CLAIM: c_a4ad908a — status=not_enough_info]`, `pytest==7.4.3 [UNRESOLVED-CLAIM: c_7bf4208f — status=not_enough_info]`, `statsmodels==0.14.0 [UNRESOLVED-CLAIM: c_c12d2912 — status=not_enough_info]`, `nibabel==5.2.0 [UNRESOLVED-CLAIM: c_65ecb818 — status=not_enough_info]`.
- [X] T003 [P] Configure linting and formatting tools. Create `.flake8` (max-line-length=100 [UNRESOLVED-CLAIM: c_6b446fcb — status=not_enough_info], exclude=venv) and `pyproject.toml` (black config). Execute verification: `black --check.` and `flake8 code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with paths, hyperparameters (window sizes, TRs), and dataset IDs (ds000030, ds000208) [UNRESOLVED-CLAIM: c_21a32d6e — status=not_enough_info]. Include a mechanism to switch dataset IDs if validation fails.
- [X] T005 [P] Implement `code/utils/atlas.py` to load Schaefer atlas and map ROIs to Yeo 7-network parcellation (DMN=7, Auditory=4, Salience=2 [UNRESOLVED-CLAIM: c_13502136 — status=not_enough_info]). Define `load_atlas()` and `map_to_yeo()` functions.
- [X] T006 [P] Implement `code/utils/io.py` for checksums, JSON/Parquet handling, and directory creation. Define `compute_checksum()`, `save_parquet()`, `load_json()`.
- [X] T007 Create base data models/entities in `code/data/models.py` using Pydantic. Define `Subject` (id: str, genre_scores: dict), `TimeSeries` (roi_id: str, values: list[float]), `NetworkMetric` (subject_id: str, metric_name: str, value: float), `CorrelationResult` (metric: str, genre: str, r: float, p_raw: float, p_adj: float), `SensitivityReport` (window_size: int, icc: float).
- [X] T008 [P] Configure Docker environment validation script in `code/utils/docker.py` (moved from preprocess.py to separate validation unit). Define `validate_docker_daemon()` and `check_fmriprep_image()` to ensure environment readiness before any heavy compute.
- [X] T009 [P] Setup environment configuration management for memory limits and runtime monitoring. **Status**: Pending Implementation. Define `check_memory_limit()` in `code/config.py` to verify available RAM before fMRIPrep execution. Implement `monitor_runtime_and_warn()` in `code/utils/io.py` to log warnings when the pipeline approaches the temporal limit

The research question is to determine how to effectively monitor resource constraints in the pipeline. The method involves implementing a logging mechanism that triggers alerts as execution time nears the established threshold. (Author et al., 2023 [UNRESOLVED-CLAIM: c_bc7d76eb — status=not_enough_info]) and suggest splitting the job or requesting a spec amendment. Do NOT implement a hard runtime cap that is infeasible for N=85; the task is to provide monitoring and warnings only.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download and validate fMRI/behavioral data, preprocess with fMRIPrep, and extract regional time courses.

**Independent Test**: The pipeline can be tested by verifying the existence of preprocessed BOLD time series files and a merged CSV containing subject IDs, network metrics (placeholder), and genre preference scores for a subset of subjects (e.g., A cohort of subjects), AND verifying that the system correctly flags or falls back when the primary behavioral variable is missing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data validation schema in `tests/contract/test_data_validation.py`. Implement `test_schema_validates_musical_genre_field()` and `test_schema_falls_back_to_stomp_r()`.
- [X] T011 [P] [US1] Integration test for fMRIPrep wrapper in `tests/integration/test_fmriprep_wrapper.py`. Implement `test_fmriprep_runs_on_mock_data()` and `test_fmriprep_handles_memory_error()`.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/download.py` to download resting-state fMRI data from OpenNeuro (ds000030, ds000208) using `requests` or `bids-validator` logic. Define `download_dataset(dataset_id: str, output_dir: str)`. **Output**: Raw BIDS dataset in `data/raw/`.
- [X] T012c [US1] Depends: T008, T012. **CRITICAL**: Implement `code/data/validate.py` to perform comprehensive data integrity checks. **Execution Order**: This task MUST wait for T012 to complete and `data/raw/*/participants.tsv` to exist.
 1. **File Existence Check**: Verify `participants.tsv` exists for each downloaded dataset. If missing, raise `FileNotFoundError`.
 2. **Power Check**: Load metadata and verify sample size N >= 85. **Note**: The Spec's assumption of N=50 is explicitly overridden by the Plan's power requirement. If N < 85, log `ERR_UNDERPOWERED` and halt execution unconditionally.
 3. **Variable Validation**: Check `participants.tsv` for 'musical_genre'. If missing, attempt fallback to 'STOMP-R'. If both missing, raise `DataValidationError` (code `ERR_DATA_MISSING`) with a clear message listing the specific missing field name.
 4. **Corruption Check**: Define `exclude_subjects_by_missing_data(confounds_df: pd.DataFrame, threshold: float = 0.1 [UNRESOLVED-CLAIM: c_8c7e75c5 — status=not_enough_info]) -> list[str]` to flag subjects with >10% corrupted fMRI volumes.
 5. **Motion Check**: Define `exclude_subjects_by_motion(confounds_df: pd.DataFrame, fd_threshold: float = 0.5 [UNRESOLVED-CLAIM: c_31774952 — status=not_enough_info]) -> list[str]` to flag subjects with excessive head motion (>0.5mm FD).
 6. Return a list of valid subject IDs for downstream processing.
- [X] T014 [US1] Depends: T008, T012c, T012. Implement `code/data/preprocess.py` to run fMRIPrep (Docker) with memory limits and generate standardized BOLD/confounds. Command args: `--output-space MNI152NLin2009cAsym --confounds trans_x,trans_y,trans_z,rot_x,rot_y,rot_z,framewise_displacement,dvars`. Define `run_fmriprep(subject_id: str)`.
- [X] T015 [US1] Depends: T005, T014. Implement `code/data/preprocess.py` to extract regional time courses using Schaefer atlas (multiple ROIs × timepoints). Define `extract_time_series(subject_id: str)`.

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
- [X] T023 [US2] Implement `code/analysis/metrics.py` for sliding-window dynamic connectivity (window=30 TRs, step=5 TRs [UNRESOLVED-CLAIM: c_63f9a86b — status=not_enough_info]). Define `compute_dynamic_connectivity(time_series: np.array, window_size: int, step: int)`.
- [X] T024 [US2] Implement `code/analysis/metrics.py` to calculate dynamic reconfiguration rate from sliding-window matrices. Define `compute_reconfiguration_rate(dynamic_matrices: list[np.array])`.
- [X] T025 [US2] Depends: T014, T015. Implement `code/analysis/metrics.py` to regress out FD/DVARS from time series before dynamic analysis using `sklearn.linear_model.LinearRegression`. Output format: CSV with timepoints and residuals. Define `regress_confounds(time_series: np.array, confounds: np.array)`.
- [X] T026 [US2] Implement `code/analysis/metrics.py` to run sensitivity analysis with window sizes **20, 30, and 40 TRs** (per FR-011). Define `run_sensitivity_analysis(time_series: np.array, window_sizes: list[int])`.
- [X] T027 [US2] Implement `code/analysis/metrics.py` to calculate Intraclass Correlation Coefficient (ICC) for dynamic metrics across window sizes. Define `compute_icc(metrics: list[float])`.
- [X] T028 [US2] Generate `SensitivityReport` JSON/Parquet with stability metrics and ICC values. Save to `data/derived/sensitivity_report.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation, Power Analysis, and Visualization (Priority: P3)

**Goal**: Perform Spearman correlations, Benjamini-Hochberg correction, power analysis, and generate visualizations.

**Independent Test**: The analysis can be tested by running the correlation module on a mock dataset with known correlations and verifying that the output table correctly identifies significant correlations (p<0.05) and that the Benjamini-Hochberg adjusted p-values are calculated correctly. Power analysis is tested by verifying the system reports the achieved power (≥0.8) for the sample size and effect size observed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for statistical output schema in `tests/contract/test_stats_schema.py`. Implement `test_stats_schema_has_required_columns()` and `test_bh_correction_applied()`.
- [X] T030 [P] [US3] Integration test for null distribution validation in `tests/integration/test_null_distribution.py`. Implement `test_null_distribution_false_positive_rate()`.

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement `code/analysis/stats.py` to perform Spearman correlations between network metrics and genre preference scores. Define `compute_spearman_correlations(metrics: pd.DataFrame, genres: pd.Series)`.
- [X] T032 [US3] Implement `code/analysis/stats.py` to apply Benjamini-Hochberg correction to raw p-values. Define `apply_bh_correction(p_values: list[float])`.
- [X] T033 [US3] Implement `code/analysis/stats.py` to perform post-hoc power analysis (target: power ≥ 0.8 for |r| ≥ 0.3 [UNRESOLVED-CLAIM: c_0b4d127e — status=not_enough_info]). Define `compute_power(sample_size: int, effect_size: float)`.
- [X] T034 [US3] Implement `code/analysis/stats.py` to run null distribution validation with **1,000 permutations [UNRESOLVED-CLAIM: c_eafe10ae — status=not_enough_info]** (per Plan override of Spec FR-010). **Rationale**: The Plan mandates a large number of permutations for robust false positive rate estimation, overriding the Spec's initial value. Generate `data/derived/null_validation_report.json` with keys: `false_positive_rate`, `permutations_count`. Define `run_null_distribution_validation(metrics: pd.DataFrame, genres: pd.Series, n_permutations: int = 1000)`.
- [X] T035 [US3] Implement `code/analysis/stats.py` to flag results as 'Underpowered' if power < 0.8. Define `flag_underpowered(power: float)`.
- [X] T036 [US3] Implement `code/analysis/viz.py` to generate correlation heatmap (PNG/PDF). Save to `data/derived/correlation_heatmap.png`.
- [X] T037 [US3] Implement `code/analysis/viz.py` to generate network diagrams highlighting significant connections (adjusted p < 0.05). Save to `data/derived/network_diagram.png`.
- [X] T038 [US3] Implement `code/main.py` to orchestrate the full pipeline with error handling for `ERR_UNDERPOWERED` (log warning, require spec amendment, halt if not amended) and `ERR_DATA_MISSING`. Define CLI interface with exit codes.
- [X] T038a [US3] [P] Implement `code/main.py` CLI argument parsing and pipeline orchestration logic.
- [X] T038b [US3] [P] Implement `code/main.py` final report generation logic to produce `data/derived/final_results.csv`.
- [X] T039 [US3] Generate final results CSV with all metrics, correlations, and p-values. Save to `data/derived/final_results.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `docs/` and `README.md`. Update sections: 'Installation', 'Usage', 'Data Sources', 'Validation'.
- [X] T041a [P] Refactor data ingestion module (`code/data/download.py`, `code/data/validate.py`) for modularity and separation of concerns.
- [X] T041b [P] Refactor metric calculation module (`code/analysis/metrics.py`) to optimize loop structures and reduce redundancy.
- [X] T041c [P] Standardize error logging and reporting across all modules.
- [X] T042a [P] Profile fMRIPrep memory usage and document findings.
- [X] T042b [P] Optimize sliding-window matrix operations in `code/analysis/metrics.py`.
- [X] T042c [P] Evaluate parallelization of subject processing if memory constraints allow.
- [X] T043a [P] Add unit tests for metric calculation functions in `tests/unit/test_metrics.py`.
- [X] T043b [P] Add unit tests for statistical functions in `tests/unit/test_stats.py`.
- [X] T043c [P] Add integration tests for end-to-end pipeline in `tests/integration/test_pipeline.py`.
- [X] T044 Security hardening (Docker image scanning, dependency checks).
- [X] T045 Run `quickstart.md` validation

---

## Phase Revision: Addressing Plan-Spec Conflicts & Data Integrity

**Purpose**: Resolve blocking contradictions identified in the Plan regarding Sample Size (N=85 vs N=50) and Permutation Count (100 vs 1000+), and ensure strict data source verification.

- [X] T046 [US1] **CRITICAL**: Update `code/data/validate.py` to enforce the Plan's power requirement (N ≥ 85) as a hard gate. If the available dataset in `data/raw` contains fewer than 85 subjects, the script MUST raise `DataValidationError` with code `ERR_UNDERPOWERED` and exit. Do NOT proceed to preprocessing with N=50. **Note**: The Spec's assumption of N=50 is explicitly overridden by the Plan.
- [X] T047 [US3] **CRITICAL**: Update `code/analysis/stats.py` to execute 1,000 permutations [UNRESOLVED-CLAIM: c_eafe10ae — status=not_enough_info] for the null distribution validation (FR-010) instead of the Spec's 100. This aligns with the Plan's requirement for robust false positive rate estimation. Update `compute_power` documentation to reflect the increased computational cost.
- [X] T048 [US1] **CRITICAL**: Implement a strict "Fail Loudly" mechanism in `code/data/download.py` **ONLY for dataset unreachability**. If the OpenNeuro fetch fails (dataset missing), raise `ConnectionError`. However, if the dataset is present but the primary variable ('musical_genre') is missing, the script MUST **NOT** halt; it MUST attempt to switch to the 'STOMP-R' proxy variable. If 'STOMP-R' is also missing, then raise `DataValidationError` (code `ERR_DATA_MISSING`). This ensures FR-001b fallback logic is preserved while maintaining data source integrity.
- [X] T048b [US1] **CRITICAL**: Implement the 'switch to STOMP-R' fallback logic in `code/data/validate.py`. If 'musical_genre' is missing, check for 'STOMP-R'. If found, log a warning and use 'STOMP-R' as the proxy. If both are missing, raise `DataValidationError` (code `ERR_DATA_MISSING`) with the specific missing field name.
- [ ] T049 [US1] **CRITICAL**: Update `code/data/validate.py` to explicitly log the specific missing field name when `musical_genre` or `STOMP-R` is absent, ensuring the `ERR_DATA_MISSING` error message provides actionable debugging information for the researcher.
- [ ] T050 [US2] **CRITICAL**: Add a runtime estimation task in `code/main.py` that calculates the expected duration for N=85 subjects based on a pilot run of 5 subjects [UNRESOLVED-CLAIM: c_6443f553 — status=not_enough_info]. If the estimated time exceeds 6 hours [UNRESOLVED-CLAIM: c_d11431aa — status=not_enough_info], log a `WARNING: RUNTIME_EXCEEDED` and suggest splitting the job or requesting a spec amendment, rather than failing silently or truncating the dataset.

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
- **Note on Plan-Spec Conflicts**: The Plan specifies N=85 and 1,000+ permutations, while the Spec specifies N=50 (runtime) and 100 permutations. Tasks follow the Plan's active requirements (1,000 permutations [UNRESOLVED-CLAIM: c_eafe10ae — status=not_enough_info], N>=85 hard gate) where the Plan explicitly overrides the Spec. The Spec's N=50 assumption is flagged as invalid and ignored. T009 implements monitoring instead of a hard cap.