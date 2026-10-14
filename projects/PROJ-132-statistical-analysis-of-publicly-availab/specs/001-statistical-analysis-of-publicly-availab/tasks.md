# Tasks: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Inputs**: `spec.md`, `plan.md`, original research idea, contracts, and reviewer feedback (task-format rejection: duplicate ID `T005c5`; verifier rejection: T015a produced no real artifacts).

This revision consolidates the prior fragmented task list into a minimal complete study with unique, sequential task IDs. All scientific requirements from the specification are preserved. Since no working source artifacts exist (the verifier confirmed T015a produced no code or data), the study uses the canonical `code/` layout. Every deliverable is a real file whose content can be deterministically verified.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] **Establish project layout, configuration, and data-source provenance** — Create `code/config.py` (grid resolution 0.5°, random seeds, permutation count 10000, per-species GAMM timeout 600 s, 2020–2024 date filter, migratory-species list constant) and `code/data/fetch_species.py` that downloads the Cornell Lab migratory species list from a real, reachable source (a pinned raw GitHub URL of a public migratory-species list, or `datasets.load_dataset` of a real eBird-derived species dataset), writes `data/raw/migratory_list.json`, records its SHA-256 in `data/provenance/ebird_checksums.json`, and RAISES `DataFetchError` on any download failure — never falls back to a synthetic list. Also write `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` documenting the ratified NOAA→Daymet and full-EBD→sampled-eBird scope deviation, and `data/provenance/spec_plan_deviation.json` with `{"status":"ratified"}`. Document the runnable entry command in the feature's `quickstart.md`.
  - Verification: `python code/data/fetch_species.py` exits 0; `data/raw/migratory_list.json` is valid JSON with ≥1 species entry; the checksum file matches `sha256sum` of the downloaded file.

- [ ] T002 [P] [US1] **Implement streaming data acquisition for eBird and climate data** — Create `code/data/download.py` and `code/data/stream_utils.py` that (a) stream the verified eBird sample via `datasets.load_dataset("vvud/eb-data", streaming=True)` in chunks, writing raw records to `data/raw/ebird_sample/` with `checksums.sha256`; (b) fetch Daymet climate data for the available recent years via a real package-based recipe (`datasets` loader or an installable Daymet client), writing `data/raw/daymet/` with checksums; (c) verify endpoint reachability before download and abort loudly (`raise DataFetchError`) if unavailable and the deviation is not ratified. Never fall back to generated, mock, or placeholder data; a failed fetch must fail the run. Write `data/provenance/data_availability_report.json` stating the exact streaming/sampling rule used (which split, chunk size, row counts).
  - Verification: running the module produces real non-empty files under `data/raw/` whose checksums match; `code/tests/test_download.py` asserts a forced network failure raises rather than writing placeholder data.

- [ ] T003 [US1] **Preprocessing: filter, grid-align, compute phenology metrics, and join climate** — Create `code/data/preprocess.py` that streams the eBird records from T002, filters to migratory species (T001 list) and 2020–2024, aggregates weekly counts per 0.5°×0.5° grid cell, computes phenology metrics (first arrival, median arrival, stopover duration = days between 10th–90th percentile arrival dates), marks cells with <5 observations as `data_quality="insufficient"` and excludes them from downstream modeling with a log entry recording species, grid cell, and reason, imputes missing climate values via spatial interpolation from neighboring cells within 1° radius with an `imputed` flag, joins climate variables (March–May mean temperature, total precipitation, extreme weather index), and writes `data/processed/preprocessed_data.parquet` conforming to `specs/.../contracts/phenology_metric.schema.yaml` and `dataset.schema.yaml`, plus provenance `data/provenance/row_mapping.json` linking processed rows to original `checklist_id`s. Include focused unit tests `code/tests/test_preprocess.py` (empty input raises, sparse-cell flagging, imputation edge cases).
  - Verification: parquet exists with required columns (species, grid_cell, year, phenology metrics, climate_temp, climate_precip) and no missing values in critical fields; `pytest code/tests/test_preprocess.py` passes.
  - Depends on: T001, T002.

- [ ] T004 [US1] [US2] **Run a thin end-to-end analysis on a small real subset** — Create `code/cli/run_pipeline.py` entry point and run preprocessing plus a simple linear mixed-effect association (via `statsmodels`) for ONE species on the real sampled data, producing real result rows in `data/results/smoke_run_results.csv` with fields (species_id, climate_variable, coefficient, p_value) computed from actual observations — no placeholder values.
  - Verification: the documented quickstart command executes end-to-end and `data/results/smoke_run_results.csv` contains ≥1 row derived from real data.
  - Depends on: T003.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US2] **Fit GAMMs with species random slopes and a priori Matérn GP spatial effect** — Create `code/models/gamm.py::fit_gamm_gp` reading `data/processed/preprocessed_data.parquet` (data_quality="sufficient" only), fitting phenology metrics as responses with climate variables as smooth fixed effects, species-year random intercepts/slopes, and a mandatory a priori Gaussian Process random effect with Matérn covariance on grid coordinates (CPU-tractable implementation via `pygam`/`statsmodels` with an explicit GP kernel; per-species fit must converge within 600 s or be logged and skipped — never halt the pipeline). Write results to `data/processed/model_results_final.parquet` conforming to `gamm_results.schema.yaml` and `output.schema.yaml` (coefficient, p_value, AIC, convergence_status, gp_included=true, random_slope_present). Include `code/tests/test_gamm_single_species.py` validating recovery of a known association on a synthetic-parameter calibration fixture (within tolerance), and `code/tests/test_convergence_handling.py` asserting failed fits are logged and skipped.
  - Verification: schema validation passes on the parquet; convergence rate recorded; `pytest` passes.
  - Depends on: T003.

- [ ] T006 [US2] **Permutation tests, Moran's I diagnostics, and FDR correction** — Create `code/models/utils.py` with (a) `run_permutation_chunked` performing 10,000 shuffles of climate series per species-climate coefficient (reduce to 1,000 only if the 6-hour budget is genuinely exceeded, with a logged justification), writing `data/results/permutation_results_coefficients.json`; (b) `compute_morans_i` post-hoc diagnostic on GAMM residuals, writing `data/results/morans_i_result.json` and flagging models with Moran's I > 0.15; (c) `apply_fdr_correction` applying Benjamini–Hochberg across ALL hypothesis tests, writing `data/results/model_results_fdr.parquet` with `p_value_fdr` and `is_significant` (p_fdr < 0.05). Unit test `code/tests/test_fdr.py` asserts BH correction on a known p-value vector.
  - Verification: JSON/parquet outputs exist; FDR-corrected p-values are monotone-consistent with BH; `pytest` passes.
  - Depends on: T005.

- [ ] T007 [US3] **Route-shift analysis: weekly centroids, Riemannian trajectory statistics, and shift detection** — Create `code/models/trajectory.py` computing weekly migration centroids on the sphere (great-circle Fréchet-mean style discrete centroid method, using `geomstats` or an explicit haversine-based implementation), applying manifold-based trajectory statistics to detect spatial route shifts, and writing `data/interim/weekly_centroids.parquet`, `data/interim/trajectory_statistics.json`, and shift vectors (magnitude in km, direction in radians) to `data/results/trajectory_results.json` conforming to `trajectory.schema.yaml`. Wrap heavy manifold steps in a timeout (≤1800 s) that logs and defers rather than fabricating. Include `code/tests/test_manifold_coords.py` for coordinate conversion and `code/tests/test_trajectory_null.py` asserting a null (label-shuffled) synthetic input yields p > 0.05.
  - Verification: schema validation passes; null-case test passes.
  - Depends on: T003.

- [ ] T008 [US3] **Block-bootstrap uncertainty quantification for shift p-values and confidence intervals** — Create `code/analysis/routes.py` and `code/analysis/bootstrap.py` performing a moving-block bootstrap (block = 4 weeks, rationale documented in-code) over (a) the centroid estimation process for route-shift permutation p-values (10,000 shuffles, fallback 1,000 with logged justification), writing `data/results/permutation_results_spatial.json`, and (b) GAMM phenology-shift predictions, writing `data/results/uncertainty_quantification.json` with 95% CIs and `data/results/ci_width_report.json` reporting CI width in days.
  - Verification: CI outputs exist with real resampled intervals; the CI width report states the measured width and its comparison to the ≤7-day target with honest fallback reporting.
  - Depends on: T005, T007.

- [ ] T009 [US1] [US2] [US3] **Independent correctness, sensitivity, and success-criteria evaluation** — Create `code/analysis/power_analysis.py` (statistical power and MDES given the actual sample size, with the "underpowered to detect effects < X" fallback statement) and `code/analysis/success_metrics.py` computing SC-001–SC-005: power/effect-size stability (SC-001), proportion of insufficient-data cells (SC-002), GAMM convergence rate (SC-003), CI width vs ≤7-day target (SC-004), and total pipeline runtime vs the 6-hour budget (SC-005). Write `data/results/final_success_report.json` aggregating all metrics with actual measured values and honest fallback statements where targets are unmet — no fabricated target attainment.
  - Verification: report exists with all five SC entries populated from actual measured artifacts; the runtime entry matches logged pipeline timings.
  - Depends on: T006, T008.

- [ ] T010 [US1] [US2] [US3] **Generate result tables and figures from validated outputs** — Create `code/analysis/figures.py` producing, directly from `data/processed/` and `data/results/` artifacts: (a) a summary table `data/results/species_climate_summary.csv` of significant species-climate associations after FDR; (b) a map of migration centroid shifts per species; (c) time-series plots of phenology metrics with climate covariates and 95% CIs. Save figures under `figures/`. No hand-typed numbers; every figure traces to result files.
  - Verification: each figure file exists and the generation script runs cleanly from the result artifacts.
  - Depends on: T009.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 **Write methods/results account with honest limitations** — Write `specs/001-bird-migration-climate-correlation/research.md` describing the methods (GAMM formulae, random effects, GP specification, permutation/FDR procedure, block bootstrap), linking every reported number to the actual output files under `data/results/` and `figures/`, and stating negative findings, convergence failures, power limitations, and the sampled-data scope deviation honestly.
  - Verification: every quantitative claim in the document references an existing artifact path.
  - Depends on: T010.

- [ ] T012 **Re-run the documented workflow end-to-end and document the paper-stage handoff** — Re-execute `python code/cli/run_pipeline.py` from the declared raw inputs, confirm all `code/tests/` tests pass and every promised artifact under `data/results/` and `figures/` regenerates with consistent content, record the exact command and runtime in the feature's `quickstart.md`, and write the paper-stage handoff (required tables, figures, and limitations to carry into the paper pipeline — layout/PDF/publication excluded here).
  - Verification: a clean re-run reproduces all artifacts; quickstart documents the verified command.
  - Depends on: T011.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (data download/cache, versioned) | T001, T002 | `python code/data/download.py` |
| FR-002 (species filter, grid aggregation) | T001, T003 | `python code/cli/run_pipeline.py --stage preprocess` |
| FR-003 (phenology + seasonal climate) | T003 | same as above; check `data/processed/preprocessed_data.parquet` |
| FR-004 (GAMM, random slopes, GP) | T005 | `pytest code/tests/test_gamm_single_species.py` |
| FR-005 (permutation + BH FDR) | T006 | `pytest code/tests/test_fdr.py` |
| FR-006 (Riemannian route shifts) | T007 | `pytest code/tests/test_trajectory_null.py` |
| FR-007 (bootstrapped 95% CIs) | T008 | check `data/results/uncertainty_quantification.json` |
| SC-001–SC-005 | T009 | check `data/results/final_success_report.json` |
| US-1/US-2/US-3 acceptance scenarios | T003/T004/T005/T006, T007/T008 | as above |

Execution order: T001, T002 (parallel) → T003 → T004 (smoke result) → T005, T007 (parallel) → T006, T008 → T009 → T010 → T011 → T012.

## Revision behavior

- **task-format rejection (duplicate `T005c5`)**: the prior fragmented task list was replaced by this consolidated set with unique, sequential IDs T001–T012; no requirement was dropped.
- **T015a verifier rejection (no real artifacts)**: reopened as T001–T004, which require the actual scripts, real downloaded data, and checkable output files; each task's verification names a concrete file and schema/content check.
- Platform-owned concerns removed: CI workflow creation, pre-commit/linting, state-file synchronization, README/API-doc scaffolding. Research scripts write only to `data/`, `figures/`, `code/`, and the feature's `specs/` directory.
