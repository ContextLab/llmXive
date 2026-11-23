---
description: "Task list for feature implementation"
---

# Tasks: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`

**Tests**: Unit‑ and integration‑tests are included where explicitly requested in the specification.

**Organization**: Tasks are grouped by phase and by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] T001 Create project directory structure (`mkdir -p data/raw data/processed data/results data/preprocess_log.txt data/analysis_log.txt data/metrics_log.txt code tests contracts`) |
- [ ] T002 Verify directory creation (assert each required folder exists) |
- [ ] T003 Create placeholder `README.md` with installation, usage, and reproducibility sections |
- [ ] T004 Create Python virtual environment in `venv/` and verify activation script exists |
- [X] T005 Create linting and formatting configuration files `pyproject.toml` (black) and `.ruff.toml` (ruff) |
- [ ] T006 Initialise empty log files `data/preprocess_log.txt`, `data/analysis_log.txt`, `data/metrics_log.txt` |
- [ ] T007 Add minimal JSON‑Schema skeletons in `contracts/` (dataset, metric, result) |
- [ ] T008 Create top‑level `requirements.txt` and pin exact versions for all dependencies (nilearn, networkx, scikit‑learn, pandas, matplotlib, nibabel, scipy, pytest, dask, distributed, etc.) |
- [ ] T009 Verify `requirements.txt` contains pinned versions and that imports succeed (`pip install -r requirements.txt && python -c "import nilearn"`) |
- [ ] T010 Configure linting (ruff) and formatting (black) tools (install and ensure config files exist) |
- [~] T011 Verify linting configuration files exist (`pyproject.toml`, `.ruff.toml`) |

## Phase 2: Foundational (Blocking Prerequisites)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [~] T012 Implement logging utilities in `code/utils.py` (`setup_logger()` writes to both `data/preprocess_log.txt` and `data/analysis_log.txt` with ISO timestamps) |
- [~] T013 Verify `setup_logger()` writes ISO‑timestamped entries to both log files (unit test) |
- [~] T014 Implement reproducible RNG helper in `code/utils.py` (`get_seeded_rng(seed=42)`) |
- [~] T015 Verify RNG seeding reproducibility (unit test comparing generated sequences) |
- [~] T016 Implement QC helpers in `code/utils.py` (`check_fd(fd_value, threshold=0.5)` and `log_exclusion(reason, subject_id)`) |
- [~] T017 Verify `check_fd()` returns expected boolean for known FD values (unit test) |
- [~] T018 Create data‑schema definitions: `contracts/dataset.schema.yaml`, `contracts/metric.schema.yaml`, `contracts/result.schema.yaml` |
- [~] T019 Validate schema files against minimal example (schema‑validation test) |
- [~] T020 Implement base `Subject` entity in `code/models.py` with attributes `id`, `fmriprep_path`, `dsst_score`, `qc_metrics` and method `has_valid_data()` |
- [~] T021 Verify `Subject` instantiation and `has_valid_data()` behavior (unit test) |
- [~] T022 Implement HCP download logic in `code/download.py` (URL list, retry up to 3 ×, checksum verification, status reporting) |
- [~] T023 Integration test confirming download, checksum, and retry logic on a small known file |

## Phase 3: User Story 1 – Data Acquisition & Pre‑processing (Priority P1)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [~] T024 Unit test `tests/unit/test_download.py::test_download_retries_on_error` (must fail before implementation) |
- [~] T025 Unit test `tests/unit/test_preprocess.py::test_fmriprep_invocation_logs_hash` (must fail before implementation) |
- [~] T026 Implement `verify_fMRI_availability()` in `code/download.py` – returns `{'status':'PRESENT'}` or raises `RuntimeError('Data Gap: fMRI time‑series not found')` |
- [~] T027 Verify both PRESENT and MISSING branches (unit test) |
- [~] T028 Implement main runner in `code/main.py` that calls `verify_fMRI_availability()`; on MISSING raise `RuntimeError` with clear message |
- [~] T029 Test that the main runner aborts with the expected error when data are missing |
- [~] T030 Implement thin wrapper `code/preprocess.py` that invokes the fMRIPrep Docker container (pinned image, required flags) and supports `--mode ci` (subset) and `--mode cluster` |
- [~] T031 Verify fMRIPrep Docker wrapper logs exact container image hash and all required flags (unit test) |
- [~] T032 Add QC validation in `code/preprocess.py`: after fMRIPrep finishes, run `check_fd()` on each subject, exclude subjects with FD > 0.5 mm and log exclusions via `log_exclusion()` |
- [~] T033 Verify QC after fMRIPrep correctly excludes high‑motion subjects and logs them (unit test) |
- [~] T034 Ensure `code/download.py` and `code/preprocess.py` use the logger from T012 for all messages |
- [~] T035 Test that logger calls are made from both modules (mock logger and assert calls) |
- [~] T036 After preprocessing, compute percentage of subjects that passed QC and log `SC‑001: X % subjects passed fMRIPrep QC` to `data/analysis_log.txt` | <!-- FAILED-IN-EXECUTION: code/log_qc_pass_rate.py exit=1 -->
- [~] T037 Log the SC‑001 success‑rate metric (implementation) |

## Phase 4: User Story 2 – Network Reconfigurability Metric Computation (Priority P2)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [~] T038 Unit test `tests/unit/test_metrics.py::test_sliding_window_correlation_shapes` (must fail before implementation) |
- [~] T039 Unit test `tests/unit/test_metrics.py::test_louvain_retry_on_failure` (must fail before implementation) |
- [~] T040 Before metric computation, invoke `check_fd()` to exclude high‑motion subjects; log exclusions (reuse from US1) |
- [~] T041 Verify that `check_fd()` runs before sliding‑window computation (integration test) |
- [~] T042 Implement `compute_sliding_window()` in `code/metrics.py` (30 s window, 5 s step, Schaefer 200‑parcel atlas) – returns array of connectivity matrices |
- [~] T043 Verify output shape and numeric ranges for synthetic NIfTI input (unit test) |
- [~] T044 Save each subject’s sliding‑window connectivity array to `data/processed/connectivity_{subject_id}.npy` and verify file existence (unit test) |
- [~] T045 Implement `extract_reconfigurability()` in `code/metrics.py` – runs Louvain community detection (seeded RNG), retries with new seeds up to three times, counts community‑state transitions |
- [~] T046 Verify Louvain retry logic and correct counting (unit test) |
- [~] T047 Write reconfigurability metric for each subject to `data/results/metrics_{subject_id}.json` (`subject_id`, `transition_count`) |
- [~] T048 Verify JSON file exists, follows `contracts/metric.schema.yaml`, and respects naming convention (unit test) |
- [~] T049 Aggregate all subject JSON files into a single TSV `data/processed/metrics_aggregated.tsv` (`subject_id`, `transition_count`) |
- [~] T050 Verify aggregated TSV contains one row per subject with correct columns (unit test) |
- [ ] T051 Log metric‑computation progress and exclusions to `data/metrics_log.txt` |
- [~] T052 Verify `data/metrics_log.txt` exists and contains expected entries (unit test) |
- [~] T053 Re‑run metric computation with the same seeded RNG and assert that generated JSON and TSV files are bit‑wise identical (SC‑002) |
- [~] T054 Verify repeatability test passes (identical output files) |

## Phase 5: User Story 3 – Statistical Correlation & Visualization (Priority P3)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [~] T055 Unit test `tests/unit/test_analysis.py::test_spearman_correlation_known_values` (must fail before implementation) |
- [~] T056 Unit test `tests/unit/test_viz.py::test_scatter_plot_generation` (must fail before implementation) |
- [~] T057 Implement subject filtering in `code/analysis.py` – keep only subjects where `Subject.has_valid_data()` is `True`; log number of excluded subjects to `data/analysis_log.txt` |
- [~] T058 Verify filtering logic and exclusion logging (unit test) |
- [~] T059 Write explicit summary line to `data/analysis_log.txt` such as `Excluded X subjects due to missing DSST or QC failures` |
- [~] T060 Implement `compute_spearman()` in `code/analysis.py` – calculates Spearman rank correlation between `transition_count` and `DSST_score` for all valid subjects |
- [~] T061 Implement Bonferroni correction (`apply_bonferroni()`) in `code/analysis.py` for the set of metric‑behavior pairs |
- [~] T062 Compute Cohen’s *r* effect size; clamp extreme p‑values to a small constant (e.g., 1e‑12) to avoid division‑by‑zero |
- [ ] T063 Write aggregated statistical summary to `data/analysis_results.tsv` (`metric_pair`, `spearman_rho`, `p_val`, `p_adj`, `cohens_r`) |
- [~] T064 Verify `analysis_results.tsv` exists, has required columns, and non‑empty rows (unit test) |
- [~] T065 Validate that the TSV complies with `contracts/result.schema.yaml` |
- [~] T066 Implement `generate_scatter_plot()` in `code/viz.py` – creates PNG scatter plots with 95 % confidence intervals and effect‑size annotation |
- [~] T067 Save each plot as `data/results/plot_{metric}_{behavior}.png` |
- [~] T068 Verify each PNG plot file exists and is non‑empty (unit test) |
- [~] T069 Ensure plot files are listed in `data/analysis_log.txt` for traceability | <!-- FAILED-IN-EXECUTION: code/viz.py exit=1 -->

## Phase 6: User Story 4 – Permutation‑Testing Validation (Priority P3)

| ID | Parallel? | Description |
|----|-----------|-------------|
- [~] T070 Unit test `tests/unit/test_analysis.py::test_permutation_null_distribution` (must fail before implementation) |
- [~] T071 Implement `run_permutation_test()` in `code/analysis.py` – shuffles DSST scores while keeping metrics fixed, uses seeded RNG, default 1000 permutations |
- [~] T072 Compute permutation‑derived p‑values by comparing the observed Spearman statistic to the null distribution |
- [~] T073 Save raw permutation results & null distribution to `data/results/permutation_results.tsv` | <!-- FAILED-IN-EXECUTION: code/save_permutation_results.py exit=1 -->
- [~] T074 Verify `permutation_results.tsv` has 1000 rows and correct headers (unit test) |
- [~] T075 Ensure each row of `permutation_results.tsv` contains `shuffle_index` and `spearman_rho` (validation) |
- [~] T076 Generate visual report `data/results/permutation_report.png` showing the null histogram with the observed statistic highlighted | <!-- FAILED-IN-EXECUTION: code/permutation_report.py exit=1 -->
- [~] T077 Verify the permutation report PNG exists and is non‑empty (unit test) |
- [~] T078 Log creation of the permutation report in `data/analysis_log.txt` | <!-- FAILED-IN-EXECUTION: code/log_permutation_report_creation.py exit=1 -->
- [~] T079 Log permutation‑test execution details (seed, number of shuffles, runtime) to `data/analysis_log.txt` |
- [~] T080 Verify log contains seed, shuffle count, and runtime entries (unit test) |

## Phase N: Polish & Cross‑Cutting Concerns

| ID | Parallel? | Description |
|----|-----------|-------------|
- [~] T081 Update `README.md` with installation instructions, CLI usage examples, and description of each pipeline stage |
- [~] T082 Verify `README.md` contains sections: Installation, Usage, Pipeline Overview, Reproducibility |
- [~] T083 Remove duplicate import of `numpy` in `code/metrics.py` |
- [~] T084 Standardise function naming to `snake_case` across all `code/` modules |
- [~] T085 Verify code cleanup (no duplicate imports, consistent naming) via lint test |
- [~] T086 Replace loop in sliding‑window computation with NumPy‑vectorised operation |
- [~] T087 Benchmark new implementation against old; assert ≥20 % speed‑up |
- [~] T088 Add edge‑case unit tests for missing DSST scores, Louvain non‑convergence, and high‑motion subjects (files in `tests/edge_cases/`) |
- [~] T089 Run edge‑case tests in CI and ensure they pass |
- [~] T090 Validate `quickstart.md` by running an end‑to‑end CI test on the 1‑2 subject subset |
- [ ] T091 Create GitHub Actions workflow `.github/workflows/ci.yml` defining a `quickstart_test` job that executes `python -m code.main --mode ci` and asserts exit code 0 |
- [~] T092 Verify the CI job `quickstart_test` passes (log inspection) |
- [~] T093 Compute and log percentage of subjects successfully processed through fMRIPrep (SC‑001) – already done in T036/T037 |
- [~] T094 Re‑run metric computation with the same seed and assert identical results (SC‑002) – already done in T053/T054 |
- [~] T095 Verify Louvain retry‑logic works as intended (unit test forcing failure) |
- [~] T096 Verify metric pipeline repeatability (run twice, compare outputs) |

---

**Execution Order Summary**

1. **Phase 1 → Phase 2** – foundational infrastructure must be in place before any user‑story work.
2. **Phase 3** (US‑1) – data download, availability check, fMRIPrep wrapper, QC, and SC‑001 logging.
3. **Phase 4** (US‑2) – sliding‑window connectivity, Louvain‑based reconfigurability, aggregation, and SC‑002 repeatability check.
4. **Phase 5** (US‑3) – filtering, Spearman correlation, Bonferroni correction, effect size, results TSV, and scatter‑plot generation.
5. **Phase 6** (US‑4) – permutation testing, null‑distribution report, and detailed logging.
6. **Phase N** – documentation, code cleanup, performance optimisation, edge‑case testing, CI workflow, and final validation.

All tasks respect the producer‑before‑consumer data flow and adhere to the specification’s functional and non‑functional requirements.
