# Tasks: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

**Input**: Design documents from `/specs/001-investigating-the-relationship-between-b/spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Notes on this revision**: Verified completed work (T001–T038a, T039–T060c) is preserved. T038b was rejected by independent verification (truncated `code/main.py`, missing `data/derived/final_results.csv`) and is reopened. The pending robustness tasks T061–T070 have been consolidated into substantive research tasks (T071–T081) grouped by scientific requirement; every acceptance criterion and verification step is retained. Tasks follow the Plan's active requirements where it overrides the Spec (N ≥ 85 hard gate; 1,000 permutations).

## Phase 1: Setup and Foundational Infrastructure (COMPLETE — preserved)

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `state/`). Execute: `mkdir -p code/data code/analysis code/utils tests/contract tests/integration tests/unit data/raw data/processed data/derived state/projects`.
- [ ] T002 Initialize Python project with `requirements.txt` containing pinned versions: `nibabel==5.2.0`, `networkx==3.2.1`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`, `scipy==1.11.4`, `pyyaml==6.0.1`, `pytest==7.4.3`, `statsmodels==0.14.0`.
- [ ] T003 [P] Configure linting and formatting tools (`.flake8`, `pyproject.toml` black config). Verification: `black --check .` and `flake8 code/`.
- [ ] T004 Create `code/config.py` with paths, hyperparameters (window sizes, TRs), and dataset IDs (ds000030, ds000208), with a mechanism to switch dataset IDs if validation fails.
- [ ] T005 [P] Implement `code/utils/atlas.py`: `load_atlas()` and `map_to_yeo()` mapping Schaefer-400 ROIs to Yeo 7-network parcellation (DMN=7, Auditory=4, Salience=2).
- [ ] T006 [P] Implement `code/utils/io.py`: `compute_checksum()`, `save_parquet()`, `load_json()`.
- [ ] T007 Create data models in `code/data/models.py` (Pydantic): `Subject`, `TimeSeries`, `NetworkMetric`, `CorrelationResult`, `SensitivityReport`.
- [ ] T008 [P] Implement `code/utils/docker.py`: `validate_docker_daemon()` and `check_fmriprep_image()`.
- [ ] T009 [P] Environment configuration for memory limits and runtime monitoring: `check_memory_limit()` in `code/config.py`, `monitor_runtime_and_warn()` in `code/utils/io.py`. Monitoring and warnings only; no hard runtime cap.

## Phase 2: User Story 1 — Data Ingestion, Validation, and Preprocessing (COMPLETE — preserved)

- [ ] T010 [P] [US1] Contract tests in `tests/contract/test_data_validation.py`: `test_schema_validates_musical_genre_field()`, `test_schema_falls_back_to_stomp_r()`.
- [ ] T011 [P] [US1] Integration tests in `tests/integration/test_fmriprep_wrapper.py`: `test_fmriprep_runs_on_mock_data()`, `test_fmriprep_handles_memory_error()`.
- [ ] T012 [P] [US1] Implement `code/data/download.py`: `download_dataset(dataset_id, output_dir)` fetching OpenNeuro BIDS data to `data/raw/`.
- [ ] T012d [US1] Implement `verify_file_exists(file_path)` in `code/data/download.py`; raise `FileNotFoundError` if `participants.tsv` missing.
- [ ] T012c [US1] Implement `code/data/validate.py`: file existence check, power check (N ≥ 85, halt `ERR_UNDERPOWERED`), variable validation (`musical_genre` → `STOMP-R` fallback → `ERR_DATA_MISSING`), `exclude_subjects_by_missing_data()` (>10% corrupted volumes), `exclude_subjects_by_motion()` (>0.5mm FD).
- [ ] T014 [US1] Implement `code/data/preprocess.py`: fMRIPrep Docker wrapper with `--output-space MNI152NLin2009cAsym` and confound regressors; `run_fmriprep(subject_id)`.
- [ ] T015 [US1] Implement `extract_time_series(subject_id)` in `code/data/preprocess.py` using Schaefer atlas.
- [ ] T046 [US1] Enforce N ≥ 85 hard gate in `code/data/validate.py` (`ERR_UNDERPOWERED`).
- [ ] T048 [US1] Fail-loudly on dataset unreachability (`ConnectionError`); preserve STOMP-R fallback for missing variables.
- [ ] T048b [US1] STOMP-R fallback logic in `code/data/validate.py` with warning logging.
- [ ] T049 [US1] Log specific missing field names in `ERR_DATA_MISSING` messages.
- [ ] T051a [P] [US1] Streaming download mechanism in `code/data/download.py`.
- [ ] T051b [P] [US1] Disk-space check before download (warn if < 14GB).
- [ ] T051c [P] [US1] Download progress logging to `state/logs/download.log`.
- [ ] T054a–T054c [P] [US1] File integrity checks (UTF-8, delimiters), corruption detection, `ERR_DATA_CORRUPT` logging in `code/data/validate.py`.
- [ ] T057a–T057c [P] [US1] Network error detection, retry (3 attempts), exponential backoff in `code/data/download.py`.

## Phase 3: User Story 2 — Network Metric Computation with Sensitivity Analysis (COMPLETE — preserved)

- [ ] T019 [P] [US2] Contract tests in `tests/contract/test_metric_schema.py`.
- [ ] T020 [P] [US2] Integration tests in `tests/integration/test_sliding_window.py`.
- [ ] T021 [P] [US2] `compute_static_connectivity(time_series)` in `code/analysis/metrics.py` (400×400 correlation matrix).
- [ ] T022 [US2] `compute_static_metrics(matrix, network_map)` (global efficiency, modularity, within-module degree for DMN/Auditory/Salience).
- [ ] T023 [US2] `compute_dynamic_connectivity(time_series, window_size, step)` (window=30 TRs, step=5 TRs).
- [ ] T024 [US2] `compute_reconfiguration_rate(dynamic_matrices)`.
- [ ] T025 [US2] `regress_confounds(time_series, confounds)` — FD/DVARS regression before dynamic analysis.
- [ ] T026 [US2] `run_sensitivity_analysis(time_series, window_sizes)` — window sizes 20, 30, 40 TRs per FR-011.
- [ ] T027 [US2] `compute_icc(metrics)` — ICC across window sizes.
- [ ] T028 [US2] Generate `data/derived/sensitivity_report.json` conforming to `contracts/sensitivity.schema.yaml`.
- [ ] T052a–T052c [P] [US2] Memory monitoring, batch processing (batches of 5 if RAM > 6GB), incremental result aggregation in `code/analysis/metrics.py`.
- [ ] T055a–T055c [P] [US2] Atlas loading, resolution compatibility check, Schaefer-200 fallback in `code/utils/atlas.py`.
- [ ] T058a–T058c [P] [US2] Window validation, empty-window detection, skip-warning logging in `code/analysis/metrics.py`.

## Phase 4: User Story 3 — Statistical Analysis and Visualization

- [ ] T029 [P] [US3] Contract tests in `tests/contract/test_stats_schema.py`.
- [ ] T030 [P] [US3] Integration tests in `tests/integration/test_null_distribution.py`.
- [ ] T031 [US3] `compute_spearman_correlations(metrics, genres)` in `code/analysis/stats.py` (runs only after null-validation FPR ≤ 0.05).
- [ ] T032 [US3] `apply_bh_correction(p_values)` in `code/analysis/stats.py`.
- [ ] T033 [US3] `compute_power(sample_size, effect_size)` — post-hoc power (target ≥ 0.8 for |r| ≥ 0.3).
- [ ] T034 [US3] `run_null_distribution_validation(...)` with 1,000 permutations (Plan override of FR-010); outputs `data/derived/null_validation_report.json`.
- [ ] T034b [P] [US3] `compute_bootstrap_stability(...)`; outputs `data/derived/bootstrap_stability_report.json`.
- [ ] T035 [US3] `flag_underpowered(power)`.
- [ ] T036 [US3] Correlation heatmap generation in `code/analysis/viz.py` → `data/derived/correlation_heatmap.png`.
- [ ] T037 [US3] Network diagrams highlighting significant connections → `data/derived/network_diagram.png`.
- [ ] T038a [US3] [P] CLI argument parsing and orchestration in `code/main.py`; runtime estimation from 5-subject pilot; exit code 1 with `WARNING: RUNTIME_EXCEEDED` if estimated > 6h.
- [ ] T038c [US3] [P] CLI exit logic for `ERR_UNDERPOWERED` (exit code 1).
- [ ] T047b [US3] [P] `docs/DEVIATIONS.md` documenting "FR-010 overridden by Plan: 100 -> 1000 permutations".
- [ ] T056a–T056c [P] [US3] CSV validation, NaN detection, and halt-and-report logic in `code/main.py`.
- [ ] T059a–T059c [P] [US3] Bootstrap resampling, execution, and stability reporting in `code/analysis/stats.py`.
- [ ] T060a–T060c [P] [US3] Log configuration, error capture, log writing to `state/logs/pipeline_run.log`.

## Phase 5: Revision — Redo Rejected Work and Consolidated Pending Requirements

- [ ] T038b [US3] **REDO (rejected by verifier)**. Depends: T031, T034. Complete the final report generation logic in `code/main.py` — the existing file is truncated and contains no logic writing `data/derived/final_results.csv`.
  - Implement the full orchestration: after correlations (T031) and null validation (T034) complete, assemble and write `data/derived/final_results.csv` with columns `subject_id`, `metric`, `genre`, `r`, `p_raw`, `p_adj`, `p_adj_bh` (per FR-008 and US-3), conforming to `contracts/correlations.schema.yaml` field semantics.
  - **Verification**: (1) `code/main.py` is syntactically complete (`python -m py_compile code/main.py` passes) and contains the write call for `data/derived/final_results.csv`; (2) the file `data/derived/final_results.csv` exists in the repository after a pipeline run on real data; (3) it contains all specified columns with zero NaN values in numeric columns; (4) if the file is not generated, the pipeline exits non-zero. Do NOT re-check this box until the real artifact exists.

- [ ] T071 [US1] Streaming data loader for large OpenNeuro datasets (consolidates T061 + T063). Implement in `code/data/download.py` memory-efficient ingestion for datasets exceeding 14GB disk / 7GB RAM: use chunked HTTP requests (or `datasets.load_dataset(..., streaming=True)` where applicable) to process data in batches without loading the full dataset into RAM.
  - **Fail-loudly guarantee (T063)**: audit `code/data/download.py` and remove ANY `try/except` or `if download_failed:` block that falls back to `generate_synthetic_*()`, `mock_*()`, random, or placeholder data. A failed real fetch MUST raise `ConnectionError` with the specific URL and error; the run must FAIL, never substitute fake data.
  - **Verification**: a forced download failure raises an exception and produces no `mock_*.csv` or synthetic data files; a large real dataset subset processes without OOM errors.

- [ ] T072 [US1] Sample-size and fallback provenance reporting (consolidates T062 + T067). Implement in `code/data/validate.py` explicit documentation of any sampling and any variable fallback.
  - If a sample is used (e.g., `itertools.islice` first N rows or fixed-seed random sample), log the exact sample size, seed, and representativeness limitation; add `sample_size` and `sampling_method` fields to `data/derived/validation_report.json` (e.g., "Sampled N=50 from N=100 using seed 42").
  - If 'musical_genre' is missing and 'STOMP-R' is used, log a clear warning with both variable names; add `fallback_used` and `fallback_variable` fields to `data/derived/validation_report.json` (e.g., "Fallback: musical_genre -> STOMP-R").
  - **Verification**: `data/derived/validation_report.json` exists and contains `sample_size`, `sampling_method`, `fallback_used`, `fallback_variable` with honest values reflecting the actual run.

- [ ] T073 [US2] Motion regression validation (T064). Implement in `code/analysis/metrics.py`: after regressing out FD/DVARS, verify the residual time series has no significant correlation with motion parameters (p > 0.05 for each motion confound).
  - Log a `motion_regression_success` boolean in `data/derived/motion_report.json`.
  - **Verification**: the pipeline halts if motion regression fails to reduce motion correlation below threshold; `data/derived/motion_report.json` contains the boolean and per-confound p-values from the actual run.

- [ ] T074 [US2] Sliding-window sensitivity detail logging (T068). Implement in `code/analysis/metrics.py`: log the exact window sizes tested (20, 30, 40 TRs per FR-011) and resulting ICC values for each dynamic metric.
  - Save `data/derived/sensitivity_details.json` with `window_size`, `metric_name`, and `icc` for each combination, conforming to `contracts/sensitivity.schema.yaml` semantics.
  - **Verification**: the file contains entries for all three window sizes and all dynamic metrics (`dynamic_reconfiguration_rate` for DMN, Auditory, Salience, Global).

- [ ] T075 [US3] Benjamini-Hochberg and power-analysis validation (consolidates T065 + T066). Implement in `code/analysis/stats.py`:
  - BH validation: unit test with known p-values verifying adjusted p-values match the theoretical BH formula exactly; log `bh_validation_passed` boolean.
  - Power validation: compare calculated power against a known reference (e.g., published G*Power output) for a given N and effect size; log `power_validation_passed` boolean; halt if power deviates >1% from reference.
  - **Output**: both booleans and reference values in `data/derived/stats_validation.json`.
  - **Verification**: `data/derived/stats_validation.json` exists with both keys set from actual validation runs; pipeline halts on failure.

- [ ] T076 [US3] Null-distribution and bootstrap validation detail logging (consolidates T069 + T070). Implement in `code/analysis/stats.py`:
  - Null validation logging: save `data/derived/null_validation_details.json` with `permutations_count`, `observed_fpr`, and `threshold` (0.05) — the exact values used (permutation_count ≥ 1000 per `contracts/correlations.schema.yaml`).
  - Bootstrap validation logging: save `data/derived/bootstrap_validation_details.json` with `n_bootstraps`, `mean_r`, `std_r`, and `stability_coefficient` from the actual resampling run.
  - **Verification**: both files exist, contain all required keys, and values are computed from real data (no placeholders); observed FPR ≤ 0.05 is reported honestly even if it fails.

- [ ] T077 [US1] End-to-end thin run on real inputs. Execute the full pipeline (`code/main.py`) on a small real subset (e.g., the first 5 valid subjects from the validated OpenNeuro dataset) to produce real result rows under `data/derived/` and `data/results/`.
  - **Verification**: documented command in the active feature's `quickstart.md` executes; `data/derived/final_results.csv` and `data/derived/metrics.csv` contain real measured values (no NaN, no synthetic stand-ins); provenance fields from T072 are populated.
  - **Checkpoint**: do not start Phase 6 report writing from expected or invented results — only from these actual outputs.

- [ ] T078 [US2] Full-cohort metric computation and sensitivity execution. Run the complete specified parameter/data domain on all valid subjects (N ≥ 85 per the Plan's hard gate): static metrics for DMN/Auditory/Salience/Global, dynamic metrics (window=30, step=5), and the FR-011 sensitivity analysis across window sizes 20/30/40 TRs.
  - Preserve every scientific constraint: motion-regressed time series only (T073 gate), exclusion rules (>10% missing behavioral data, >10% corrupted volumes, FD > 0.5mm), exclusion counts reported.
  - **Verification**: `data/derived/metrics.csv` has one row per subject × network × metric conforming to `contracts/metrics.schema.yaml`; `data/derived/sensitivity_report.json` reports ICC per metric with `is_stable` flags (ICC ≥ 0.7); runtime monitoring logs from T009 are present.

- [ ] T079 [US3] Full statistical analysis execution. Run the complete correlation analysis on the full-cohort metrics: Spearman correlations for all metric-genre pairs, BH correction, post-hoc power analysis, null-distribution validation (1,000 permutations), and bootstrap stability.
  - **Verification**: `data/derived/final_results.csv` complete with all columns and conforming to `contracts/correlations.schema.yaml` (including `power_achieved` and `permutation_count`); underpowered results flagged; if zero significant findings after correction, the results table and report explicitly state "No significant correlations found after correction" and still report achieved power (spec edge case).

- [ ] T080 [US3] Generate final figures and tables from validated outputs (FR-008). Using `code/analysis/viz.py` on the actual `final_results.csv`: regenerate the correlation heatmap (`data/derived/correlation_heatmap.png`) and network diagrams highlighting significant connections (adjusted p < 0.05, `data/derived/network_diagram.png`), plus a statistical summary table.
  - **Verification**: figures are regenerated from the real full-cohort results (not the pilot subset); all significant pairs from `final_results.csv` are visually marked; figures render without errors.

- [ ] T081 [US3] Reproducible re-run and paper-stage handoff. Re-run the documented workflow from its declared inputs (per `quickstart.md`), confirm all required tests (`pytest tests/`) and artifact checks pass, and write a concise methods/results account in `research.md` (or the active feature's results document) linked to the actual output cells and figure files.
  - Describe negative findings, failures, and limitations honestly (including power status, sensitivity ICC results, and any dataset-variable fallback used).
  - Document the paper-stage handoff: figures, `final_results.csv`, sensitivity/bootstrap/null-validation reports, and the deviations log (`docs/DEVIATIONS.md`) are the inputs for the subsequent paper pipeline; paper layout and PDF compilation belong to that stage.
  - **Verification**: a fresh clone plus `pip install -r requirements.txt` plus the documented command reproduces all artifacts; `pytest` passes; the results document references only files that exist.

## Dependencies and requirement coverage

| Requirement | Tasks | Order |
|---|---|---|
| FR-001 (download/merge) | T012, T071 | T071 after T012 |
| FR-001b (variable validation/fallback) | T012c, T048b, T072 | T072 after T012c |
| FR-002 (fMRIPrep) | T014 | after T012c |
| FR-003 (time courses) | T015 | after T014 |
| FR-004 (static metrics, Yeo mapping) | T005, T022, T078 | T078 after T077 |
| FR-005 (dynamic metrics) | T023, T024, T025, T073, T078 | T073 before T078 |
| FR-006/FR-007 (Spearman + BH) | T031, T032, T075, T079 | T079 after T078 |
| FR-008 (figures) | T036, T037, T038b, T080 | T080 after T079 |
| FR-009 (power) | T033, T075, T079 | — |
| FR-010 (null validation, 1000 perms) | T034, T076, T079 | — |
| FR-011 (sensitivity, ICC) | T026–T028, T074, T078 | — |
| SC-001–SC-006 | T077–T081 | final phase |

**Execution order (pending work)**: T038b → T071 → T072 → (T073, T074, T075, T076 parallel) → T077 → T078 → T079 → T080 → T081.

## Revision behavior

- Verified completed tasks (checked boxes with matching artifacts) are preserved as-is; their identities and status carry forward.
- T038b is reopened per the verifier rejection: both the truncated `code/main.py` logic and the missing `data/derived/final_results.csv` must be genuinely produced before re-checking.
- Pending tasks T061–T070 were consolidated into T071–T081 without dropping any acceptance criterion; each verification step is retained in the task item or its continuation lines.
- Plan-Spec conflicts remain resolved in favor of the Plan: N ≥ 85 hard gate (`ERR_UNDERPOWERED`), 1,000 permutations (documented in `docs/DEVIATIONS.md`).
