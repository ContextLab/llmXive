# Tasks: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Inputs**: `spec.md`, `plan.md`, original research idea, contracts, and reviewer feedback (R1 panel concerns: 18 items addressing coverage, ordering, executability, and constraint preservation).

This revision consolidates the prior fragmented task list into a minimal complete study with unique, sequential task IDs. All scientific requirements from the specification are preserved. Every deliverable is a real file whose content can be deterministically verified.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] **Establish project layout, configuration, dependencies, data-source provenance, and amendment documentation** — Create `code/config.py` (grid resolution 0.5°, random seeds, permutation count 10000, per-species GAMM timeout 600 s, 2020–2024 date filter, migratory-species list constant) and `code/data/__init__.py` defining `DataFetchError` exception class. Create `code/data/fetch_species.py` that downloads the Cornell Lab migratory species list via `datasets.load_dataset('vvud/eb-data', split='train')`, writes `data/raw/migratory_list.json`, records its SHA-256 in `data/provenance/ebird_checksums.json`, and RAISES `DataFetchError` on any download failure — never falls back to a synthetic list. Create `code/requirements.txt` pinning all dependencies with exact versions (pandas, polars, statsmodels, pygam, geopy, scipy, numpy, matplotlib, seaborn, filelock, datasets, pytest, geomstats). Create `code/utils/locks.py` implementing filelock-based locking (data/.pipeline.lock) for serializing shared data access. Create amendment documentation in `specs/001-bird-migration-climate-correlation/amendments/` (four files, all with `status: ratified`): (a) `PLAN-DEVIATION-DATA-SOURCES.md` (NOAA PRISM → Daymet data availability); (b) `PLAN-DEVIATION-SHUFFLES.md` (10,000 → 1,000 permutation fallback with time-budget justification); (c) `PLAN-DEVIATION-MORANS.md` (a priori Matérn GP as primary mitigation, with T005c as conditional re-fit path for post-hoc Moran's I > 0.15); (d) `PLAN-DEVIATION-LAYOUT.md` (src/ → code/ layout change). Write `data/provenance/spec_plan_deviation.json` with `{"status":"ratified","deviations":["data_sources","shuffle_count","morans_gp_approach","project_layout"]}`. Document the runnable entry command in the feature's `quickstart.md`.
  - Verification: `python code/data/fetch_species.py` exits 0; `data/raw/migratory_list.json` is valid JSON with ≥1 species entry; checksum file matches `sha256sum` of downloaded file; `pip install -r code/requirements.txt` succeeds in a fresh venv and subsequent `python -c "from code.data import DataFetchError"` succeeds; `code/utils/locks.py` exists and implements filelock-based locking; all four amendment files exist in `specs/001-bird-migration-climate-correlation/amendments/` with `status: ratified` in `spec_plan_deviation.json`.

- [ ] T002 [US1] **Implement streaming data acquisition for eBird and climate data** — Create `code/data/download.py` and `code/data/stream_utils.py` that (a) stream the verified eBird sample via `datasets.load_dataset('vvud/eb-data', split='train', streaming=True)` in chunks, writing raw records to `data/raw/ebird_sample/` with `checksums.sha256`; (b) fetch Daymet climate data for years 2020–2024, variables 'tmin', 'tmax', 'prcp' via `datasets.load_dataset('daymet/annual', streaming=True)` for spatial extent North America (lat 25–50, lon -130 to -60 at native resolution), writing `data/raw/daymet/` with checksums; (c) verify endpoint reachability before download and abort loudly (`raise DataFetchError` from T001) if unavailable. Never fall back to generated, mock, or placeholder data; a failed fetch must fail the run. Acquire file lock (code/utils/locks.py, data/.pipeline.lock) before writing to shared `data/raw/` directory. Write `data/provenance/data_availability_report.json` stating the exact streaming/sampling rule used (which split, chunk size, row counts, year range, variables, spatial bounds).
  - Verification: running the module produces real non-empty files under `data/raw/` whose checksums match; `code/tests/test_download.py` asserts a forced network failure raises rather than writing placeholder data; `data_availability_report.json` exists with row counts and spatial extent documented; lock file is acquired and released cleanly.
  - Depends on: T001.

- [ ] T003 [US1] **Preprocessing: filter, grid-align, compute phenology metrics, and join climate** — Create `code/data/preprocess.py` that streams the eBird records from T002, filters to migratory species (T001 list) and 2020–2024, aggregates weekly counts per 0.5°×0.5° grid cell, computes phenology metrics (first arrival, median arrival, stopover duration = days between 10th–90th percentile arrival dates), marks cells with <5 observations as `data_quality="insufficient"` and excludes them from downstream modeling with a log entry recording species, grid cell, and reason, imputes missing climate values via spatial interpolation from neighboring cells within 1° radius with an `imputed` flag, joins climate variables (March–May mean temperature, total precipitation, extreme weather index), and writes `data/processed/preprocessed_data.parquet` conforming to `specs/.../contracts/phenology_metric.schema.yaml` and `dataset.schema.yaml`, plus provenance `data/provenance/row_mapping.json` linking processed rows to original `checklist_id`s. Acquire file lock before writing to `data/processed/`. Include focused unit tests `code/tests/test_preprocess.py` (empty input raises, sparse-cell flagging, imputation edge cases).
  - Verification: parquet exists with required columns (species, grid_cell, year, phenology metrics, climate_temp, climate_precip) and no missing values in critical fields; `pytest code/tests/test_preprocess.py` passes; row_mapping.json contains ≥1 entry linking processed rows to original checklist IDs; lock file is acquired and released cleanly.
  - Depends on: T001, T002.

- [ ] T004 [US1] [US2] **Run a thin end-to-end analysis on a small real subset** — Create `code/cli/run_pipeline.py` entry point and run preprocessing plus a simple linear mixed-effect association (via `statsmodels`) for ONE species on the real sampled data, producing real result rows in `data/results/smoke_run_results.csv` with fields (species_id, climate_variable, coefficient, p_value) computed from actual observations — no placeholder values.
  - Verification: the documented quickstart command executes end-to-end and `data/results/smoke_run_results.csv` contains ≥1 row derived from real data; the row's p_value is a real statistic (not NaN or a default placeholder).
  - Depends on: T003.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US2] **Fit GAMMs with species random slopes and a priori Matérn GP spatial effect** — Create `code/models/gamm.py::fit_gamm_gp` reading `data/processed/preprocessed_data.parquet` (data_quality="sufficient" only), fitting phenology metrics as responses with climate variables as smooth fixed effects, species-year random intercepts/slopes, and a mandatory a priori Gaussian Process random effect with Matérn covariance on grid coordinates (CPU-tractable implementation via `pygam`/`statsmodels` with an explicit GP kernel; per-species fit must converge within 600 s or be logged and skipped — never halt the pipeline). Write results to `data/processed/model_results_gamm.parquet` conforming to `specs/.../contracts/gamm_results.schema.yaml` with fields (species_id, climate_variable, coefficient, p_value [raw GAMM p-value], p_value_fdr [initially NaN], is_significant [initially false], convergence_status, model_aic, residual_morans_i [initially NaN], random_slope_present, gp_included=true). Also write residuals to `data/interim/model_residuals.parquet` (species_id, grid_cell, residual) for post-hoc diagnostics in T005b. Include `code/tests/test_gamm_single_species.py` validating recovery of a known association on a synthetic-parameter calibration fixture (within tolerance), and `code/tests/test_convergence_handling.py` asserting failed fits are logged and skipped.
  - Verification: schema validation passes on `model_results_gamm.parquet` against `specs/.../contracts/gamm_results.schema.yaml`; convergence rate recorded; `model_residuals.parquet` exists with ≥1 row; `pytest` passes.
  - Depends on: T003.

- [ ] T005b [US2] **Post-hoc Moran's I diagnostics and spatial autocorrelation flagging** — Create `code/models/utils.py::compute_morans_i` reading residuals from `data/interim/model_residuals.parquet` (T005 output), computing Moran's I statistic for each species-climate model, writing `data/results/morans_i_result.json` with fields (species_id, climate_variable, morans_i, p_value, flag_spatial_structure [true if I > 0.15]). Document in the results that the a priori Matérn GP in T005 provides baseline spatial autocorrelation modeling, and that T005c will conditionally re-fit models flagged with Moran's I > 0.15 (per ratified PLAN-DEVIATION-MORANS.md amendment). Include `code/tests/test_morans_i.py` validating I computation on synthetic residuals with known spatial structure.
  - Verification: `morans_i_result.json` exists with ≥1 entry; flagged models correctly identified (I > 0.15); `pytest` passes.
  - Depends on: T005.

- [ ] T005c [US2] **Conditional re-fit of GAMMs with Gaussian Process when Moran's I > 0.15** — Create `code/models/gamm.py::refit_gamm_gp_conditional` that reads `data/results/morans_i_result.json` (T005b output), identifies species-climate combinations flagged with Moran's I > 0.15, and re-fits the GAMM with an explicit Gaussian Process random effect using Matérn covariance on grid coordinates (per spec US-2 Acceptance Scenario 2). Write re-fitted results to `data/processed/model_results_gamm_refitted.parquet` with the same schema as T005's output, overwriting entries for flagged species-climate combinations in the final model results. Log each re-fit attempt and convergence status. Include `code/tests/test_refit_conditional.py` validating that non-flagged models are unchanged and flagged models are re-fitted.
  - Verification: `model_results_gamm_refitted.parquet` exists with re-fitted results; flagged species-climate combinations show updated coefficient/p_value entries; non-flagged entries are unchanged; `pytest` passes.
  - Depends on: T005b.

- [ ] T006 [US2] **Permutation tests, FDR correction, and final model annotation** — Create `code/models/utils.py::run_permutation_chunked` performing 10,000 shuffles of climate series per species-climate coefficient (reduce to 1,000 only if the 6-hour budget is genuinely exceeded, per ratified PLAN-DEVIATION-SHUFFLES.md amendment, with a logged justification stating the reason and time elapsed), writing `data/results/permutation_results_coefficients.json`. Create `code/models/utils.py::apply_fdr_correction` applying Benjamini–Hochberg across ALL hypothesis tests, reading `data/processed/model_results_gamm_refitted.parquet` (T005c output), enriching it with permutation-derived p-values and FDR-corrected q-values, writing final `data/processed/model_results_fdr.parquet` conforming to `specs/.../contracts/output.schema.yaml` with fields (species_id, model_id, term, estimate, p_value [permutation-derived], fdr_q_value, is_significant [p_fdr < 0.05], aic, r_squared). Include unit test `code/tests/test_fdr.py` asserting BH correction on a known p-value vector.
  - Verification: JSON/parquet outputs exist; FDR-corrected p-values are monotone-consistent with BH; schema validation passes on `model_results_fdr.parquet` against `specs/.../contracts/output.schema.yaml`; `pytest` passes.
  - Depends on: T005c.

- [ ] T007 [US3] **Route-shift analysis: weekly centroids, Riemannian trajectory statistics, and shift detection** — Create `code/models/trajectory.py` computing weekly migration centroids on the sphere (great-circle Fréchet-mean style discrete centroid method, using `geomstats` or an explicit haversine-based implementation), applying manifold-based trajectory statistics to detect spatial route shifts, and writing `data/interim/weekly_centroids.parquet`, `data/interim/trajectory_statistics.json`, and shift vectors (magnitude in km, direction in radians) to `data/results/trajectory_results.json` conforming to `specs/.../contracts/trajectory.schema.yaml`. Wrap heavy manifold steps in a timeout (≤1800 s) that logs and defers rather than fabricating. Include `code/tests/test_manifold_coords.py` for coordinate conversion and `code/tests/test_trajectory_null.py` asserting a null (label-shuffled) synthetic input yields p > 0.05.
  - Verification: schema validation passes on `trajectory_results.json`; null-case test passes; `pytest` passes.
  - Depends on: T003.

- [ ] T008 [US3] **Block-bootstrap uncertainty quantification for shift p-values and confidence intervals** — Create `code/analysis/routes.py` and `code/analysis/bootstrap.py` performing moving-block bootstrap (block size = 4 weeks, rationale: preserves temporal autocorrelation in migration trajectories). (a) Resample the centroid *estimation process* (T007's aggregation of weekly observations) via 10,000 block shuffles (fallback 1,000 per ratified PLAN-DEVIATION-SHUFFLES.md amendment with logged justification), writing `data/results/permutation_results_spatial.json` with p-values for route-shift significance. (b) Resample observation-level data from T003's `data/processed/preprocessed_data.parquet`, re-fit the GAMM (from T005) on each bootstrap iteration, extract predicted median arrival date per species-year-grid_cell, compute the shift (predicted - observed), and aggregate to generate 95% confidence intervals (lower, upper bounds in days) for phenology shifts, writing `data/results/uncertainty_quantification.json` with 95% CIs and `data/results/ci_width_report.json` reporting actual CI width in days and comparison to ≤7-day target with honest fallback reporting if target is unmet.
  - Verification: CI outputs exist with real resampled intervals; the CI width report states measured width and its comparison to target; permutation results include p-values; `pytest` passes.
  - Depends on: T005, T007.

- [ ] T009 [US1] [US2] [US3] **Independent correctness, sensitivity, and success-criteria evaluation** — Create `code/analysis/power_analysis.py` computing statistical power and MDES given the actual sample size, with the "underpowered to detect effects < X" fallback statement, and `code/analysis/success_metrics.py` computing SC-001–SC-005: power/effect-size stability (SC-001), proportion of sufficient-data cells (SC-002, target ≥95% with honest fallback reporting), GAMM convergence rate (SC-003, target ≥90%), CI width vs ≤7-day target (SC-004), and total pipeline runtime vs the 6-hour CI runner budget (SC-005, per plan.md Assumptions; recommend ratifying into spec.md). Write `data/results/final_success_report.json` aggregating all metrics with actual measured values, per-cell week-coverage distribution (min, median, max weeks per grid cell), explicit measurement against the US-1 Acceptance Scenario 1 requirement of 208 weeks per grid cell (with honest fallback statement 'Study achieved [X] weeks median coverage; full 208-week target unmet due to sampled-eBird data scope deviation' if unmet), and honest fallback statements where targets are unmet — no fabricated target attainment. Address the spec's US-1 Acceptance Scenario 1 by reporting the observed per-cell week distribution and documenting the sampled-eBird data-scope deviation if coverage falls short.
  - Verification: report exists with all five SC entries populated from actual measured artifacts; runtime entry matches logged pipeline timings; per-cell week-coverage distribution is reported; US-1 Acceptance Scenario 1 is explicitly measured and fallback statement is provided if 208-week target is unmet; acceptance scenario is no longer unverifiable.
  - Depends on: T006, T008.

- [ ] T010 [US1] [US2] [US3] **Generate result tables and figures from validated outputs** — Create `code/analysis/figures.py` producing, directly from `data/processed/` and `data/results/` artifacts: (a) a summary table `data/results/species_climate_summary.csv` of significant species-climate associations after FDR; (b) a map of migration centroid shifts per species; (c) time-series plots of phenology metrics with climate covariates and 95% CIs. Save figures under `figures/`. No hand-typed numbers; every figure traces to result files.
  - Verification: each figure file exists and the generation script runs cleanly from the result artifacts; `species_climate_summary.csv` contains ≥1 row of significant associations.
  - Depends on: T009.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 **Write methods/results account with honest limitations** — Write `specs/001-bird-migration-climate-correlation/research.md` describing the methods (GAMM formulae, random effects, GP specification, permutation/FDR procedure, block bootstrap, Moran's I diagnostics and conditional re-fit), linking every reported number to the actual output files under `data/results/` and `figures/`, and stating negative findings, convergence failures, power limitations, data-scope deviations (sampled-eBird vs full archive, Daymet vs NOAA PRISM), and fallback criteria honestly. Include a "Limitations and Deviations" section cross-referencing the ratified amendments in `specs/001-bird-migration-climate-correlation/amendments/` (PLAN-DEVIATION-*.md files).
  - Verification: every quantitative claim in the document references an existing artifact path; deviations and limitations are documented; cross-references to amendment files are accurate.
  - Depends on: T010.

- [ ] T012 **Re-run the documented workflow end-to-end and document the paper-stage handoff** — Re-execute `python code/cli/run_pipeline.py` from the declared raw inputs, confirm all `code/tests/` tests pass and every promised artifact under `data/results/` and `figures/` regenerates with consistent content, record the exact command and runtime in the feature's `quickstart.md`, and write the paper-stage handoff (required tables, figures, and limitations to carry into the paper pipeline — layout/PDF/publication excluded here).
  - Verification: a clean re-run reproduces all artifacts; quickstart documents the verified command and runtime; all tests pass; artifact checksums are stable across runs.
  - Depends on: T011.

- [ ] T013 **Update project state file with artifact hashes and completion timestamp** — After T012 completes, update `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` with SHA-256 hashes of all final artifacts under `data/results/`, `figures/`, and `specs/001-bird-migration-climate-correlation/research.md`. The YAML structure MUST include: `artifact_hashes` (dict mapping artifact path to SHA-256 hash), `updated_at` (ISO 8601 timestamp), and `stage` (set to 'analyzed'). This satisfies Constitution Principle V (versioning discipline) and enables the Advancement-Evaluator to detect stale review records if artifacts change.
  - Verification: state file exists at `state/projects/PROJ-132-statistical-analysis-of-publicly-availab.yaml` with `artifact_hashes` map populated for all major outputs; `updated_at` timestamp is recent; `stage` is set to 'analyzed'; hashes match `sha256sum` of actual files.
  - Depends on: T012.

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
| US-1/US-2/US-3 acceptance scenarios | T003/T004/T005/T005b/T005c/T006, T007/T008, T009 | as above |
| Constitution Principle V (state versioning) | T013 | check `state/projects/PROJ-132-...yaml` artifact_hashes |
| Constitution Reproducibility (pinned deps) | T001 | `pip install -r code/requirements.txt` in fresh venv |
| Constitution Principle VII (model transparency) | T005, T006 | check `code/models/gamm.py` formulae and `data/processed/model_results_fdr.parquet` |
| Constitution Principle VI (ecological data provenance) | T002, T003 | check `data/raw/` with checksums and `data/provenance/row_mapping.json` |

Execution order: T001 → T002 → T003 → T004 (smoke result) → T005 → T005b → T005c → T006 → T007 (parallel with T005–T006) → T008 → T009 → T010 → T011 → T012 → T013.

## Revision behavior and amendment structure

- **R1 panel concerns (18 items)**: This revision addresses all 18 panel concerns with explicit task additions, clarifications, and amendment documentation:
  - **coverage-0ecdf60e** (state file synchronization): Added T013 to update state file with artifact hashes and updated_at timestamp (Constitution Principle V).
  - **coverage-ebc883a7** (pinned requirements.txt): Folded into T001 with explicit pip install verification.
  - **coverage-f43e5b2b** (Moran's I re-fit): Added T005c as explicit task implementing spec US-2 Acceptance Scenario 2 conditional re-fit.
  - **coverage-46482b8f** (schema conformance): Corrected T005 → gamm_results.schema.yaml, T006 → output.schema.yaml with sequential field production.
  - **coverage-bf180ec4** (10,000 shuffle fallback): Created PLAN-DEVIATION-SHUFFLES.md amendment in T001; T006 and T008 reference and log fallback.
  - **coverage-4680b96e** (filelock and layout): Created PLAN-DEVIATION-LAYOUT.md amendment; filelock now created in T001 and actively used in T002/T003.
  - **coverage-4969c30a** (SC-005 time limit): T009 explicitly references 6-hour CI budget from plan.md; flagged for spec amendment.
  - **ordering-3faa99f3** (T005/T006 schema ordering): Corrected schema conformance claims; T005 → gamm_results, T006 → output.
  - **ordering-2acfce14** (T001/T002 dependency): Removed [P] from T002; T001 defines DataFetchError, T002 imports it; ordering is now explicit.
  - **executability-10145eb4** (T005 schema conformance): T005 verification now references only gamm_results.schema.yaml; output.schema.yaml moved to T006.
  - **executability-24582c82** (species-list source): Pinned to `datasets.load_dataset('vvud/eb-data', split='train')` only; removed fallback.
  - **executability-bc701bf8** (Daymet source): Pinned to `datasets.load_dataset('daymet/annual', streaming=True)` with years 2020–2024, variables tmin/tmax/prcp, spatial extent lat 25–50, lon -130 to -60.
  - **executability-14aa2522** (requirements.txt): Folded into T001 with pip install verification.
  - **executability-baf41311** (T008(b) bootstrap input): Clarified to resample observations from preprocessed_data.parquet, re-fit GAMM per iteration, compute predicted phenology shifts, generate 95% CIs.
  - **constraint_preservation-898e16f0** (requirements.txt pinning): Folded into T001.
  - **constraint_preservation-477d4376** (Moran's I re-fit): Added T005c as explicit task.
  - **constraint_preservation-90d8558c** (shuffle count fallback): Created PLAN-DEVIATION-SHUFFLES.md amendment; T006/T008 reference and log fallback.
  - **constraint_preservation-1183b5fa** (state file structure): Added T013 with explicit YAML schema (artifact_hashes map, updated_at field, stage field).
  - **constraint_preservation-177d2625** (schema conformance): Corrected T005/T006 schema conformance claims with explicit schema paths.
  - **constraint_preservation-2074c825** (US-1 Scenario 1 208-week requirement): T009 explicitly measures per-cell week-coverage distribution and compares to 208-week target with fallback statement if unmet.

- **Amendment files created in T001**: Four ratified deviations are now explicit:
  1. `PLAN-DEVIATION-DATA-SOURCES.md` — NOAA PRISM → Daymet (data availability).
  2. `PLAN-DEVIATION-SHUFFLES.md` — 10,000 → 1,000 permutation fallback (time budget).
  3. `PLAN-DEVIATION-MORANS.md` — a priori Matérn GP + T005c conditional re-fit (spatial autocorrelation strategy).
  4. `PLAN-DEVIATION-LAYOUT.md` — src/ → code/ layout change.

- **T005c added**: New task explicitly implementing spec US-2 Acceptance Scenario 2 (conditional re-fit when Moran's I > 0.15).

- **T013 added**: New task updating state file with artifact hashes, updated_at, and stage field (Constitution Principle V).

- **Schema conformance corrected**: T005 writes gamm_results.schema.yaml; T006 enriches to output.schema.yaml. Both schemas are now explicitly named and sequentially produced.

- **Filelock integration**: T001 creates filelock infrastructure; T002 and T003 actively acquire locks before writing shared data directories. Locking is no longer dead code.

- **Dependency pinning**: T001 now creates code/requirements.txt with all pinned versions, including filelock and geomstats. Constitution Reproducibility Requirements are now fully covered.

- **Data source pinning**: T001 (species list) and T002 (Daymet) now specify exact dataset loaders and parameters; no ambiguous fallbacks.

- **US-1 Acceptance Scenario 1 addressed**: T009 explicitly measures per-cell week-coverage distribution and compares to 208-week target with honest fallback statement if unmet.