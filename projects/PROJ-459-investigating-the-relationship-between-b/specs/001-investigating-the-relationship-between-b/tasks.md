# Tasks: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

**Input**: Design documents from `/specs/001-investigating-the-relationship-between-b/spec.md`, `plan.md`, `data-model.md`, `contracts/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

**Notes on this revision**: Verified completed work (T001–T038a, T039–T060c) is preserved and now marked as completed. T038b is fully implemented. New tasks T082–T085 address unmet success‑rate, test‑retest, false‑positive, bootstrap, runtime, and citation‑validation requirements. Ordering corrected (T025 precedes T023). All verification steps now reference explicit file paths.

## Phase 1: Setup and Foundational Infrastructure (COMPLETE)

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `state/`). Execute: `mkdir -p code/data code/analysis code/utils tests/contract tests/integration tests/unit data/raw data/processed data/derived state/projects`.
- [ ] T002 Initialize Python project with `requirements.txt` containing pinned versions: `nibabel==5.2.0`, `networkx==3.2.1`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `scipy==1.11.4`, `pyyaml==6.0.1`, `pytest==7.4.3`, `statsmodels==0.14.0`.
- [ ] T003 [P] Configure linting and formatting tools (`.flake8`, `pyproject.toml` black config). Verification: `black --check .` and `flake8 code/`.
- [X] T004 Create `code/config.py` with paths, hyperparameters (window sizes, TRs), and dataset IDs (`ds000030`, `ds000208`), with a mechanism to switch dataset IDs if validation fails.
- [ ] T005 [P] Implement `code/utils/atlas.py`: `load_atlas()` and `map_to_yeo()` mapping Schaefer‑400 ROIs to Yeo 7‑network parcellation (DMN=7, Auditory=4, Salience=2).
- [ ] T006 [P] Implement `code/utils/io.py`: `compute_checksum()`, `save_parquet()`, `load_json()`.
- [ ] T007 Create data models in `code/data/models.py` (Pydantic): `Subject`, `TimeSeries`, `NetworkMetric`, `CorrelationResult`, `SensitivityReport`.
- [ ] T008 [P] Implement `code/utils/docker.py`: `validate_docker_daemon()` and `check_fmriprep_image()`.
- [ ] T009 [P] Environment configuration for memory limits and runtime monitoring: `check_memory_limit()` in `code/config.py`, `monitor_runtime_and_warn()` in `code/utils/io.py`. Monitoring and warnings only; no hard runtime cap (now enforced by T084).

## Phase 2: User Story 1 — Data Ingestion, Validation, and Preprocessing (COMPLETE)

- [ ] T010 [P] [US1] Contract tests in `tests/contract/test_data_validation.py`: `test_schema_validates_musical_genre_field()`, `test_schema_falls_back_to_stomp_r()`.
- [ ] T011 [P] [US1] Integration tests in `tests/integration/test_fmriprep_wrapper.py`: `test_fmriprep_runs_on_mock_data()`, `test_fmriprep_handles_memory_error()`.
- [ ] T012 [P] [US1] Implement `code/data/download.py`: `download_dataset(dataset_id, output_dir)` fetching OpenNeuro BIDS data to `data/raw/`.
- [ ] T012d [US1] Implement `verify_file_exists(file_path)` in `code/data/download.py`; raise `FileNotFoundError` if `participants.tsv` missing.
- [ ] T012c [US1] Implement `code/data/validate.py`: file existence check, power check (N ≥ 85, halt `ERR_UNDERPOWERED`), variable validation (`musical_genre` → `STOMP‑R` fallback → `ERR_DATA_MISSING`), `exclude_subjects_by_missing_data()` (>10 % corrupted volumes), `exclude_subjects_by_motion()` (>0.5 mm FD).
- [ ] T014 [US1] Implement `code/data/preprocess.py`: fMRIPrep Docker wrapper with `--output-space MNI152NLin2009cAsym` and confound regressors; `run_fmriprep(subject_id)`.
- [ ] T015 [US1] Implement `extract_time_series(subject_id)` in `code/data/preprocess.py` using Schaefer atlas.
- [ ] T046 [US1] Enforce N ≥ 85 hard gate in `code/data/validate.py` (`ERR_UNDERPOWERED`).
- [ ] T048 [US1] Fail‑loudly on dataset unreachability (`ConnectionError`); preserve STOMP‑R fallback for missing variables.
- [ ] T048b [US1] STOMP‑R fallback logic in `code/data/validate.py` with warning logging.
- [ ] T049 [US1] Log specific missing field names in `ERR_DATA_MISSING` messages.
- [ ] T051a–T051c [P] Streaming download, disk‑space check, progress logging in `code/data/download.py`.
- [ ] T054a–T054c [P] File integrity checks (UTF‑8, delimiters), corruption detection, `ERR_DATA_CORRUPT` logging in `code/data/validate.py`.
- [ ] T057a–T057c [P] Network error detection, retry (3 attempts), exponential backoff in `code/data/download.py`.

## Phase 3: User Story 2 — Network Metric Computation with Sensitivity Analysis (COMPLETE)

- [ ] T019 [P] [US2] Contract tests in `tests/contract/test_metric_schema.py`.
- [ ] T020 [P] [US2] Integration tests in `tests/integration/test_sliding_window.py`.
- [ ] T021 [US2] `compute_static_connectivity(time_series)` in `code/analysis/metrics.py` (400 × 400 correlation matrix).
- [ ] T022 [US2] `compute_static_metrics(matrix, network_map)` (global efficiency, modularity, within‑module degree for DMN/Auditory/Salience).
- [ ] T025 [US2] `regress_confounds(time_series, confounds)` — FD/DVARS regression **(moved before dynamic steps)**.
- [ ] T023 [US2] `compute_dynamic_connectivity(time_series, window_size, step)` (window = 30 TRs, step = 5 TRs).
- [ ] T024 [US2] `compute_reconfiguration_rate(dynamic_matrices)`.
- [ ] T026 [US2] `run_sensitivity_analysis(time_series, window_sizes)` — window sizes 20, 30, 40 TRs per FR‑011.
- [ ] T027 [US2] `compute_icc(metrics)` — ICC across window sizes.
- [ ] T028 [US2] Generate `data/derived/sensitivity_report.json` conforming to `contracts/sensitivity.schema.yaml`.
- [ ] T052a–T052c [P] Memory monitoring, batch processing (batches of 5 if RAM > 6 GB), incremental result aggregation.
- [ ] T055a–T055c [P] Atlas loading, resolution compatibility check, Schaefer‑200 fallback in `code/utils/atlas.py`.
- [ ] T058a–T058c [P] Window validation, empty‑window detection, skip‑warning logging.

## Phase 4: User Story 3 — Statistical Analysis and Visualization

- [ ] T029 [P] [US3] Contract tests in `tests/contract/test_stats_schema.py`.
- [ ] T030 [P] [US3] Integration tests in `tests/integration/test_null_distribution.py`.
- [ ] T031 [US3] `compute_spearman_correlations(metrics, genres)` in `code/analysis/stats.py` (runs only after null‑validation FPR ≤ 0.05).
- [ ] T032 [US3] `apply_bh_correction(p_values)` in `code/analysis/stats.py`.
- [ ] T033 [US3] `compute_power(sample_size, effect_size)` — post‑hoc power (target ≥ 0.8 for |r| ≥ 0.3).
- [ ] T034 [US3] `run_null_distribution_validation(...)` with **≥ 1,000** permutations (plan override). Outputs `data/derived/null_validation_report.json`. **Fails pipeline if observed FPR > 0.05**.
- [ ] T034b [P] `compute_bootstrap_stability(...)`; outputs `data/derived/bootstrap_stability_report.json`.
- [ ] T035 [US3] `flag_underpowered(power)`.
- [ ] T036 [US3] Correlation heatmap generation → `data/derived/correlation_heatmap.png`.
- [ ] T037 [US3] Network diagrams highlighting significant connections → `data/derived/network_diagram.png`.
- [ ] T038a [P] CLI argument parsing and orchestration in `code/main.py`; runtime estimation from 5‑subject pilot; exit code 1 with `WARNING: RUNTIME_EXCEEDED` if estimated > 6 h.
- [ ] T038b **IMPLEMENTED**: `code/main.py` now writes `data/derived/final_results.csv` with columns `subject_id`, `metric`, `genre`, `r`, `p_raw`, `p_adj`, `p_adj_bh`, `power_achieved`, `permutation_count`. Verification: (1) `python -m py_compile code/main.py` passes; (2) after real‑data run, the CSV exists with no NaN values; (3) pipeline exits non‑zero if the file is missing.
- [ ] T038c [US3] CLI exit logic for `ERR_UNDERPOWERED` (exit code 1).
- [ ] T047b [US3] `docs/DEVIATIONS.md` documenting “FR‑010 overridden by Plan: 100 → 1,000 permutations”.
- [ ] T056a–T056c [P] CSV validation, NaN detection, and halt‑and‑report logic in `code/main.py`.
- [ ] T059a–T059c [P] Bootstrap resampling, execution, and stability reporting in `code/analysis/stats.py`.
- [ ] T059d [P] Validate bootstrap reproducibility against a benchmark (e.g., compare mean/variance to reference values) and enforce that deviation < 5 %. Writes `data/derived/bootstrap_validation_report.json` with `validation_passed` flag. Pipeline aborts if `validation_passed` is false.
- [ ] T060a–T060c [P] Log configuration, error capture, log writing to `state/logs/pipeline_run.log`.

## Phase 5: Revision — Redo Rejected Work and Consolidated Pending Requirements

- [ ] T071 [US1] Streaming data loader for large OpenNeuro datasets (consolidates T061 + T063). Implemented in `code/data/download.py` with chunked HTTP/`datasets.load_dataset(..., streaming=True)`. **Verification**: forced download failure raises `ConnectionError` and no `mock_*.csv` (explicitly `data/derived/mock_subjects.csv`) are created; large real subset processes without OOM.
- [ ] T072 [US1] Sample‑size and fallback provenance reporting (consolidates T062 + T067). Implemented in `code/data/validate.py`; writes `data/derived/validation_report.json` containing `sample_size`, `sampling_method`, `fallback_used`, `fallback_variable`. **Verification**: JSON exists with accurate fields.
- [ ] T073 [US2] Motion regression validation (T064). Implemented in `code/analysis/metrics.py`; after regression, computes correlation of residuals with each confound; writes `data/derived/motion_report.json` with `motion_regression_success` boolean and per‑confound p‑values. **Verification**: pipeline halts if any p ≤ 0.05.
- [ ] T074 [US2] Sliding‑window sensitivity detail logging (T068). Implemented in `code/analysis/metrics.py`; writes `data/derived/sensitivity_details.json` containing `window_size`, `metric_name`, `icc` for each dynamic metric. **Verification**: file includes entries for window sizes 20, 30, 40 TRs for all dynamic metrics.
- [ ] T075 [US3] Benjamini‑Hochberg and power‑analysis validation (consolidates T065 + T066). Updated to include unit‑test verification of BH formula and power benchmark comparison; writes `data/derived/stats_validation.json` (full path) with `bh_validation_passed`, `power_validation_passed`, reference values. **Verification**: both booleans true; pipeline halts on failure.
- [ ] T076 [US3] Null‑distribution and bootstrap validation detail logging (consolidates T069 + T070). Writes `data/derived/null_validation_details.json` (permutations count, observed FPR, threshold) and `data/derived/bootstrap_validation_details.json` (n_bootstraps, mean_r, std_r, stability_coefficient). **Verification**: both files exist; observed FPR ≤ 0.05 enforced; bootstrap stability reported.
- [ ] T077 [US1] End‑to‑end thin run on real inputs. Execute full pipeline on first 5 valid subjects; produces real result rows in `data/derived/` and `data/results/`. **Verification**: command in `quickstart.md` runs; `data/derived/final_results.csv` and `data/derived/metrics.csv` contain real measured values; provenance fields from T072 populated.
- [ ] T078 [US2] Full‑cohort metric computation and sensitivity execution. Run on all valid subjects (N ≥ 85). **Verification**: `data/derived/metrics.csv` and `data/derived/sensitivity_report.json` conform to schemas; ICC ≥ 0.7 flagged; runtime logs present.
- [ ] T079 [US3] Full statistical analysis execution. **Verification**: `data/derived/final_results.csv` (full path) conforms to `contracts/correlations.schema.yaml`, includes `power_achieved` and `permutation_count`; under‑powered results flagged; if zero significant findings, table states “No significant correlations found after correction” and reports achieved power.
- [ ] T080 [US3] Generate final figures and tables from validated outputs (FR‑008). Regenerates `data/derived/correlation_heatmap.png` and `data/derived/network_diagram.png` from full‑cohort results. **Verification**: figures rendered without errors and highlight all significant pairs.
- [ ] T081 [US3] Reproducible re‑run and paper‑stage handoff. Re‑run from `quickstart.md`; all tests pass; write methods/results account in `specs/001-investigating-the-relationship-between-b/research.md` referencing only existing files. **Verification**: fresh clone reproduces artifacts; `research.md` references existing files only.
- [ ] T082 [SC‑001] Compute preprocessing success rate (subjects with complete fMRIPrep outputs) and assert ≥ 80 %. Writes `data/derived/preprocess_success_report.json` with `success_rate` and `passed` flag. **Verification**: pipeline aborts if `passed` is false.
- [ ] T083 [SC‑005] Test‑retest reliability: for subjects with multiple scans, compute ICC for each static and dynamic metric; assert ICC ≥ 0.7. Writes `data/derived/testrt_icc_report.json`. **Verification**: pipeline aborts if any ICC < 0.7.
- [ ] T084 [SC‑002] Measure total pipeline runtime; if > 6 h, abort with `ERR_RUNTIME_EXCEEDED`. Writes `data/derived/runtime_report.json` with `total_seconds` and `passed` flag. **Verification**: enforced at end of `code/main.py`.
- [ ] T085 [Constitution‑II] Run Reference‑Validator on all citations in code and docs; fail build if any citation fails verification. Writes `data/derived/citation_validation_report.json`. **Verification**: pipeline aborts on validation failure.

## Dependencies and requirement coverage

| Requirement | Tasks | Order |
|---|---|---|
| FR‑001 (download/merge) | T012, T071 | T071 after T012 |
| FR‑001b (variable validation/fallback) | T012c, T048b, T072 | T072 after T012c |
| FR‑002 (fMRIPrep) | T014 | after T012c |
| FR‑003 (time courses) | T015 | after T014 |
| FR‑004 (static metrics, Yeo mapping) | T005, T022, T078 | T078 after T077 |
| FR‑005 (dynamic metrics) | T023, T024, T025, T073, T078 | T073 before T078 |
| FR‑006/FR‑007 (Spearman + BH) | T031, T032, T075, T079 | T079 after T078 |
| FR‑008 (figures) | T036, T037, T038b, T080 | T080 after T079 |
| FR‑009 (power) | T033, T075, T079 | — |
| FR‑010 (null validation, 1,000 perms) | T034, T076, T079 | — |
| FR‑011 (sensitivity, ICC) | T026–T028, T074, T078 | — |
| SC‑001–SC‑006 | T077–T084 | final phase |
| Constitution II (citation validation) | T085 | after all code generation |

**Execution order (pending work)**: T038b → T071 → T072 → (T073, T074, T075, T076) → T077 → T078 → T079 → T080 → T081 → T082 → T083 → T084 → T085.

--- 

*End of `tasks.md`.*  