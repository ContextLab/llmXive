# Tasks: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.  

The tasks are organized into research phases.  Each task follows the canonical format  

```
- [ ] T### [P] [USx] <description> – <artifact path>
```  

`[P]` indicates the task can run in parallel with other tasks (different files, no data‑flow dependency).  
`[USx]` identifies the user story the task satisfies (US1, US2, US3).  
A checked box `[X]` denotes a completed task.  

---

## Phase 0 – Pre‑Implementation & Spec Alignment  

| ID | Status | Description |
|----|--------|-------------|
- [ ] T001 [P] **Establish project layout & quick‑start command** – Create `docs/quickstart.md` describing how to run the pipeline (`python -m src.cli.run_pipeline --help`).  
- [ ] T002 [P] **Verify project layout** – Add unit test `tests/unit/test_setup_structure.py` that asserts required directories exist.  
- [ ] T003a_1 [P] **Create `pyproject.toml`** – Add build system, Black, and Ruff configuration.  
- [ ] T003a_2 [P] **Verify Ruff config syntax** – Run `ruff check --config pyproject.toml`; succeed = exit 0.  
- [ ] T003b [P] **Create pre‑commit config** – Add `.pre-commit-config.yaml` with Black & Ruff hooks and reference it in `README.md`.  
- [ ] T003c [P] **Add `geomstats` dependency** – Append `geomstats>=2.4.0` to `[project].dependencies` in `pyproject.toml`.  

### Data‑source deviation handling (required by the plan)  
- [ ] T005c4 [M] **Document Plan deviation (NOAA → Daymet, full → sampled eBird)** – Write `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` with ratification timestamp and JSON field `{"status":"ratified"}`.  
- [ ] T005c3 [M] **Record deviation in JSON** – Write `data/provenance/spec_plan_deviation.json` (see spec for exact fields).  
- [ ] T005c1_validate [S] **Validate deviation documents** – Read the Markdown and JSON, output `data/provenance/deviation_validation.json`.  
- [ ] T005a [S] **Verify raw data availability** – Script `src/data/verify_dataset.py` checks streaming load of `vvud/eb-data` and writes `data/provenance/data_availability_report.json`.  
- [ ] T005b [S] **Download verified eBird sample** – Stream `vvud/eb-data` into `data/raw/ebird_sample/` and generate `data/raw/ebird_sample/checksums.sha256`.  
- [ ] T005c1_fetch [S] **Download climate data (primary or fallback)** – Implement `src/data/download.py::fetch_climate_data` that obeys the ratified deviation and writes either `data/raw/noaa_prism/` or `data/raw/daymet/` plus checksums.  
- [ ] T005d_state_sync [S] **Archive raw inputs & sync state** – Copy raw files to `data/raw/archive/`, generate CI upload snippet (`ci/upload_artifacts.yml`), and update `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml`.  

### Infrastructure utilities  
- [ ] T045a [S] **File‑based lock implementation** – Create `src/utils/locks.py` exposing `pipeline_lock = filelock.FileLock("data/interim/pipeline.lock")`.  
- [ ] T045b [S] **Integrate lock into heavy tasks** – Modify GAMM, permutation, and trajectory scripts to acquire `pipeline_lock` before writing shared resources.  

---

## Phase 1 – Setup & First End‑to‑End Analysis  

- [ ] T002a [P] **Create project directory tree** – `src/data`, `src/models`, `src/analysis`, `src/utils`, `src/cli`, `data/raw`, `data/processed`, `data/interim`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`.  
- [ ] T002b [P] **Unit test for directory existence** – `tests/unit/test_setup_structure.py`.  

### Core data‑acquisition (User Story 1)  
- [ ] T015a [S] [US1] **Retrieve verified migratory species list** – Implement `src/data/fetch_species.py` that downloads `vvud/eb-migratory-list` into `data/raw/migratory_list.json`, records SHA‑256 in `data/provenance/ebird_checksums.json`, and fails loudly if download fails.  
- [ ] T051 [P] **Streaming utility for full eBird dataset** – Implement `src/data/stream_utils.py` using `datasets.load_dataset(..., streaming=True)` with chunk size ≤ 6 GB.  
- [ ] T007 [P] **Spatial imputation utility** – Create `src/data/impute.py` with `impute_spatial_missing(df, column, radius=1.0)` returning imputed DataFrame + `is_imputed` flag.  
- [ ] T009 [P] **Define core data entities** – `src/data/entities.py` with Pydantic models `MigrationRecord`, `PhenologyMetric`, `ClimateVariable`, `Trajectory`.  
- [ ] T010a [P] **Global constants** – `src/config.py` (grid resolution, seeds, permutation count, CI target, max runtime).  
- [ ] T010b [P] **Logging infrastructure** – `src/utils/logging.py` exposing `get_logger(name)` writing JSON lines to `logs/pipeline.log`.  
- [ ] T010c [P] **Test logging format** – `tests/unit/test_logging.py`.  

#### Pre‑processing pipeline (US1)  
- [ ] T015b [S] [US1] **Implement preprocessing** – `src/data/preprocess.py` streams eBird via T051, filters with T015a, aggregates to 0.5° × 0.5° grid, computes phenology metrics, flags “insufficient” cells, joins climate (NOAA or Daymet) data, imputes missing climate values (T007), writes provenance `data/provenance/row_mapping.json`, and outputs `data/processed/preprocessed_data.parquet`.  
- [ ] T013 [S] [US1] **Integration test for ingestion** – `tests/integration/test_data_ingestion.py` (mocks streaming & climate fetch, asserts final parquet schema and no missing critical fields).  
- [ ] T017d [P] **Validate imputation metadata** – Unit test `tests/unit/test_imputation_metadata.py` checking `data/processed/imputation_metadata.json`.  

---

## Phase 2 – Phenology‑Climate Correlation Modeling (User Story 2)  

- [ ] T021 [P] **Test GAMM output schema** – `tests/contract/test_gamm_schemas.py` validates `data/processed/model_results_final.parquet`.  
- [ ] T022 [P] **Integration test for GAMM convergence** – `tests/integration/test_gamm_convergence.py` runs GAMM on synthetic data, asserts `converged=True`.  

- [ ] T023a_gamm_gp [S] [US2] **Fit GAMM with random slopes & mandatory GP** – `src/models/gamm.py::fit_gamm_gp` reads `data/processed/preprocessed_data.parquet`, fits model with `pyMC` using formula `phenology_metric ~ s(temp) + s(precip) + s(extreme_weather_index) + (1 + temp | species + year)` and a priori Matérn 5/2 GP, acquires `pipeline_lock`, writes `data/processed/model_results_final.parquet`.  
- [ ] T023d [S] **Compute Moran’s I diagnostic** – `src/models/gamm.py::compute_morans_i` writes `data/interim/morans_i_result.json`.  
- [ ] T025a [P] **Benchmark permutation runtime** – `src/models/utils.py::benchmark_permutation` writes `data/processed/permutation_benchmark.json`.  
- [ ] T025d [S] [US2] **Permutation test for GAMM coefficients** – `src/models/utils.run_permutation_chunked` performs 10 000 shuffles (fallback → 1 000 if > 6 h), writes `data/processed/permutation_results_coefficients.json`.  
- [ ] T025b_spatial [S] [US3] **Permutation test for spatial shift vectors** – Same utility on shift‑vector data, writes `data/processed/permutation_results_spatial.json`.  
- [ ] T025c [S] [US2] **Apply Benjamini–Hochberg FDR across all tests** – `src/models/utils.py::apply_fdr_correction` reads outputs of T025d & T025b_spatial, writes `data/processed/model_results_fdr.parquet`.  
- [ ] T025e [S] **Effective power calculation with fallback awareness** – `src/analysis/power_analysis.py::calculate_effective_power` reads permutation results, writes `data/processed/power_with_fallback.json`.  
- [ ] T027 [S] **Robust convergence handling** – Wrap GAMM fitting in try/except, log failures to `logs/modeling.log`, skip species, and add unit test `tests/unit/test_convergence_handling.py`.  

---

## Phase 3 – Route‑Shift Analysis & Uncertainty (User Story 3)  

- [ ] T030 [S] [US3] **Compute weekly centroids on S² manifold** – `src/models/trajectory.py::compute_weekly_centroids` (uses `geomstats`), writes `data/interim/weekly_centroids.parquet`.  
- [ ] T031a_manifold [S] [US3] **Riemannian trajectory statistics** – Uses centroids from T030, writes `data/interim/trajectory_statistics.json`.  
- [ ] T031b_manifold [S] [US3] **Detect spatial route shifts** – Consumes trajectory statistics, writes `data/interim/shift_candidates.json`.  
- [ ] T031c_permutation [S] [US3] **Permutation test on shift vectors** – 10 000 shuffles (fallback → 1 000), writes `data/processed/trajectory_results.json`.  
- [ ] T028 [P] **Test trajectory output schema** – `tests/contract/test_trajectory_schemas.py` validates `data/processed/trajectory_results.json`.  
- [ ] T029 [P] **Integration test for route‑shift detection** – `tests/integration/test_trajectory_analysis.py` runs pipeline on null synthetic data, asserts `p_value>0.05`.  

- [ ] T033a [S] **Unified 95 % confidence‑interval generation** – `src/analysis/bootstrap.py::generate_unified_ci` performs moving‑block bootstrap (block = 4 weeks) on GAMM predictions and centroid estimations, writes `data/processed/uncertainty_quantification.json`.  
- [ ] T033b [S] **Compute CI width metrics** – Reads CI file, writes `data/processed/ci_width_report.json`.  

---

## Phase 4 – Success‑Criteria Evaluation (SC‑001 → SC‑005)  

- [ ] T043a [S] **Write target definitions** – Parse success‑criteria section of `plan.md`, output `data/processed/target_definitions.json` (includes spec‑deferred notes).  
- [ ] T043b [S] **Power‑analysis script** – `src/analysis/power_analysis.py` (different from T025e) calculates statistical power, writes `data/processed/power_report.json`.  
- [ ] T043c1 [S] **Insufficient‑data proportion report** – Reads preprocessed data, writes `data/processed/insufficient_data_report.json`.  
- [ ] T043c2 [S] **Model‑convergence rate report** – Reads `logs/modeling.log` & model results, writes `data/processed/convergence_report.json`.  
- [ ] T043d [S] **CI‑width target report** – Compares CI widths (T033b) to targets, writes `data/processed/ci_width_target_report.json`.  
- [ ] T043 [S] **Aggregate final success report** – Combines all SC reports plus runtime check (`src/analysis/runtime_validation.py`), writes `data/processed/final_success_report.json`.  

---

## Phase 5 – Polishing & Cross‑Cutting Concerns  

- [ ] T036 [P] **Update README** – Add installation steps and pipeline entry point.  
- [ ] T037 [P] **Generate API docs for preprocessing** – `docs/api.md` with docstrings from `src/data/preprocess.py`.  
- [ ] T038a [P] **Run Ruff auto‑fix** – Apply `ruff --fix src/`.  
- [ ] T038b [P] **Add pre‑commit hook for docstring validation** – Update `.pre-commit-config.yaml`.  
- [ ] T040a [P] **Unit test for empty input handling in preprocessing** – `tests/unit/test_preprocess_empty.py`.  
- [ ] T040b [P] **Unit test for single‑species GAMM fit** – `tests/unit/test_gamm_single_species.py`.  
- [ ] T040c [P] **Unit test for imputation edge cases** – `tests/unit/test_imputation_edge_cases.py`.  
- [ ] T041a [P] **Create CI workflow** – `.github/workflows/ci.yml`.  
- [ ] T041b [P] **Add task‑ordering validation job** – Calls `src/cli/validate_task_order.py`.  
- [ ] T041c [P] **Runtime assertion (< 6 h) in CI** – Integrated into `validate_quickstart` job.  

### Validation & Robustness (must run loudly on failure)  
- [ ] T052 [S] **Enforce loud failure on data‑fetch errors** – Review `src/data/download.py` & `src/data/fetch_species.py` to remove silent fallbacks; raise `DataFetchError` on any download problem.  
- [ ] T054 [S] **Block‑bootstrap implementation verification** – Ensure `src/analysis/bootstrap.py` uses moving‑block bootstrap for both GAMM predictions and centroids.  
- [ ] T055 [S] **Explicit NOAA/PRISM availability check** – Extend `src/data/download.py::fetch_climate_data` to verify official API endpoints before download; abort if unavailable and deviation not ratified.  
- [ ] T060 [S] **Task‑ordering rule for phenology metrics** – `src/cli/validate_task_order.py` must enforce that T015b precedes any modeling or trajectory task.  
- [ ] T061 [S] **Document streaming strategy** – Add detailed docstring to `src/data/stream_utils.py` and `src/data/preprocess.py`.  
- [ ] T062 [S] **Verify FDR aggregates across all hypothesis tests** – Review `apply_fdr_correction` to ensure combined p‑value set.  
- [ ] T063 [S] **Timeout handling for heavy manifold calculations** – Wrap T030 & T031a in a timeout (e.g., `signal.alarm`), log warnings, and mark tasks as deferred if exceeded.  
- [ ] T064 [S] **Manifold coordinate conversion unit test** – `tests/unit/test_manifold_coords.py`.  
- [ ] T065 [S] **Document block‑size rationale** – Comment in `src/analysis/bootstrap.py` explaining 4‑week block choice.  

---

## Phase 6 – Reporting & Handoff  

- [ ] T052a [S] **Generate methods & results summary** – Write `docs/methods_results.md` linking directly to generated artifact files (tables, figures, JSON reports).  
- [ ] T052b [S] **Re‑run full pipeline from scratch** – Execute `python -m src.cli.run_pipeline` and confirm all checks pass; record command in `docs/reproducibility.md`.  

---

### Dependency Summary (selected)  

| Task | Depends on |
|------|------------|
| T015a | T005a (data availability) |
| T015b | T051, T015a, T005b, T005c1_fetch |
| T013  | T015b |
| T023a_gamm_gp | T015b, T045a |
| T025d | T023a_gamm_gp, T025a, T045a |
| T025b_spatial | T031b_manifold, T025a, T045a |
| T025c | T025d, T025b_spatial |
| T030 | T015b |
| T031a_manifold | T030 |
| T031b_manifold | T031a_manifold |
| T031c_permutation | T031b_manifold, T045a |
| T033a | T023a_gamm_gp, T030, T045a |
| T043c1 | T015b |
| T043c2 | T023a_gamm_gp, T027 |
| T043d | T033b |
| T043 | T043a, T043b, T043c1, T043c2, T043d, T025c, T027, T033b |

---

**Note** – All pending tasks (unchecked boxes) must be implemented and their output files verified before the pipeline can be considered complete. The most critical pending item is **T015a** (retrieving the verified migratory species list) which underpins the entire preprocessing flow.
