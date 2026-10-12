# Tasks: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

**Input**: Design documents from `/specs/001-quantifying-the-effects-of-dark-matter-h/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`

---

## Phase 1 – Setup and First End‑to‑End Analysis  

**Goal**: Establish the project skeleton, utilities, and a runnable “hello‑world” pipeline on a tiny real input so that the next phases can be built on a verified base.

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
- [ ] T001a [P] **Setup** Create the `code/` package hierarchy (`ingestion`, `processing`, `analysis`, `utils`, `tests`).  
  - **Path**: `code/` and sub‑directories.  
  - **Verification**: Run `ls -R code/` and confirm the expected tree exists.  

- [ ] T001b **Setup** Create the data directory hierarchy for raw and processed assets.  
  - **Path**: `data/raw/tng100/`, `data/raw/millennium/`, `data/processed/`, `data/metadata.yaml`.  
  - **Verification**: `ls -R data/` must list the four sub‑folders and an empty `metadata.yaml` file.  

- [ ] T001c **Setup** Create output and documentation directories.  
  - **Path**: `outputs/figures/`, `outputs/reports/`, `docs/quickstart.md`, `docs/README.md`.  
  - **Verification**: `ls -R outputs/ docs/` must show the directories and placeholder markdown files.  

- [ ] T002 [P] **Docs** Add `docs/quickstart.md` and `docs/README.md` placeholders describing how to run the pipeline.  
  - **Verification**: Both files exist and contain a `## Quickstart` section with a `python -m code.main` command.  

- [ ] T003a **Lint Config** Add a minimal `.ruff.toml` that enables the core linter rules for Python 3.11.  
  - **Path**: `.ruff.toml` at repository root.  
  - **Verification**: `ruff check .` runs without syntax errors on the empty repo.  

- [ ] T003b **Formatter Config** Add `pyproject.toml` with Black configuration (`line-length = 88`).  
  - **Verification**: `black --check .` runs without formatting violations on existing code.  

- [ ] T004 **Config Utility** Implement `code/utils/config.py` containing a seeded random generator (`random.seed(42)`) and path constants (`PROJECT_ROOT`, `DATA_ROOT`, etc.).  
  - **Verification**: Import the module in a REPL and confirm `random.getstate()` is deterministic.  

- [ ] T005 **I/O Utilities** Implement `code/utils/io.py` with streaming CSV/Parquet read/write helpers that automatically inject the required `associational_only=true` flag into the header or metadata.  
  - **Verification**: Write a test CSV and inspect the first line for the flag.  

- [ ] T006 **Logging** Add `code/utils/logging.py` and configure a basic logger in `code/main.py`.  
  - **Verification**: Running `python -m code.main` prints a timestamped INFO line.  

- [ ] T026a **Metadata Flag Injection** Extend `code/utils/io.py` with `write_associational_flag()` that writes the flag to CSV headers and JSON metadata.  
- [ ] T026b **Ingestion Hook** Update `code/ingestion/tng_loader.py` (and any future ingestion scripts) to call `write_associational_flag()` on every output file.  
- [ ] T026c **Flag Verification Test** Add `code/tests/test_io.py::test_associational_flag` ensuring the flag appears in all written CSVs.  
- [ ] T010 **Integration Test – Chunked TNG Download** Implement `code/tests/test_pipeline.py::test_pipeline_chunking` that simulates downloading a single TNG‑100 HDF5 chunk and verifies that a processed halo row appears in `data/processed/halo_shapes.csv`.  

---

## Phase 2 – Core Data Ingestion & Halo Shape Computation (User Story 1, P1)

- [ ] T011 **TNG‑100 Loader** Implement `code/ingestion/tng_loader.py` to query the official TNG API, paginate through halo files, download HDF5 chunks to `data/raw/tng100/`, and verify checksums.  
  - **Verification**: After a run, `data/raw/tng100/` contains at least one `*.hdf5` file and a matching entry in `data/metadata.yaml`.  

- [ ] T012 **Inertia Tensor Stub** Create `code/processing/inertia_tensor.py` with documented signatures: `compute_reduced_inertia_tensor(particle_positions, masses) -> np.ndarray`.  
  - **Verification**: Import the module and call the stub; it raises `NotImplementedError`.  

- [ ] T013 **Shape Metrics** Implement `code/processing/shape_metrics.py` functions `compute_axial_ratios(eigenvalues) -> (b_a, c_a)` and `compute_triaxiality(a, b, c) -> T`.  
  - **Verification**: Unit test in `code/tests/test_shape.py` validates known eigenvalue sets.  

- [ ] T014 **Resolution Filter** Add logic to `shape_metrics.py` that drops any halo with `n_dm_particles < 10_000`.  
  - **Verification**: `test_filter_low_res` ensures such halos never appear in the output CSV.  

- [ ] T016 **Chunked Streaming Pipeline** Implement `code/processing/pipeline_runner.py` that streams the full FoF catalog using `datasets.load_dataset(..., streaming=True)`, processes each halo chunk, applies the filter, computes shape metrics, and writes rows incrementally to `data/processed/halo_shapes.csv`.  
  - **Verification**: After a short run on a single stream chunk, the CSV contains at least one row with valid `b_a`, `c_a`, `T` values (0 < ≤ 1).  

- [ ] T017 **Aggregation & Validation** Extend the pipeline runner to: (1) merge streamed chunks, (2) validate that every row respects the axial‑ratio bounds, (3) log excluded halos to `data/processed/exclusion_log.json`, and (4) write the final CSV with the schema defined in `halo_schema.schema.yaml`.  
  - **Verification**: Run `pytest code/tests/test_validation.py::test_axial_ratio_bounds` and `::test_completeness_check`.  

- [ ] T018 **Galaxy Property Ingestion** Extend `tng_loader.py` to extract for each FoF halo the central galaxy’s `stellar_mass`, `sfr`, and `effective_radius`, writing them to `data/processed/galaxy_properties.csv`.  
  - **Verification**: The CSV contains a matching `halo_id` column and passes `test_galaxy_schema` in `code/tests/test_ingestion.py`.  

- [ ] T009 **Inertia Tensor Singular‑Matrix Test** Add `code/tests/test_inertia.py::test_singular_matrix_raises_error` that supplies < 10 000 particles and expects a `ValueError`.  
  - **Verification**: Test passes after T014 is implemented.  

---

## Phase 3 – Statistical Correlation, Binning & Mass Control (User Story 2, P2)

- [ ] T020a **Binning Unit Test** `code/tests/test_stats.py::test_binning_logic` confirms that `c/a < 0.5` → “Prolate”, `0.5 ≤ c/a ≤ 0.8` → “Triaxial”, `c/a > 0.8` → “Spherical”.  
- [ ] T020b **Bonferroni Unit Test** `code/tests/test_stats.py::test_bonferroni_correction` validates that raw p‑values are multiplied by the number of comparisons and capped at 1.  

- [ ] T021 **Mass‑Matching Interface** Define in `code/analysis/stats.py` the functions `match_by_mass(df_halo, df_gal, tolerance=0.05) -> pd.DataFrame` and `streamed_match(...)` with clear docstrings.  

- [ ] T021b **Streaming Mass‑Matching** Implement a block‑wise nearest‑neighbor matcher that reads `halo_shapes.csv` and `galaxy_properties.csv` in chunks, pairs halos with galaxies of similar `mass_total` (within 5 % tolerance), and writes each block to `data/processed/matched_chunks/match_###.csv`.  
  - **Verification**: `code/tests/test_stats.py::test_mass_matching_chunks` checks that each output file contains the columns `halo_id`, `galaxy_id`, `mass_total`, `triaxiality`, `sfr`, `effective_radius`.  

- [ ] T022 **Non‑Parametric Tests** Implement `kruskal_wallis`, `mann_whitney_u`, and `kolmogorov_smirnov` in `stats.py`, each returning a dict conforming to `analysis_result_schema.schema.yaml`.  

- [ ] T020c **Shape Binning Logic** Add `assign_shape_bin(c_a_ratio)` to `shape_metrics.py` returning the categorical bin string.  

- [ ] T023a **Linear Regression with Mass Control**  
  - **Description**: Using `statsmodels` fit separate OLS models for each galaxy property (SFR, Effective Radius) with predictors `triaxiality`, `b_a_ratio`, and `mass_total`.  
  - **Input**: Iterate over all CSVs in `data/processed/matched_chunks/`.  
  - **Output**: `data/processed/regression_results.csv` with columns: `test_type`, `property`, `predictor`, `coefficient`, `p_value_raw`, `p_value_adj`, `significant`, `ci_lower`, `ci_upper`, `threshold_set`, `associational_only`.  
  - **Verification**: `code/tests/test_analysis.py::test_regression_output_schema` validates the CSV against the JSON schema.  

- [ ] T023b **Binning Statistical Tests**  
  - **Description**: For each galaxy property, run Kruskal‑Wallis across the three shape bins, then pairwise Mann‑Whitney U and KS tests, applying Bonferroni correction.  
  - **Input**: Same matched‑chunk CSVs as T023a.  
  - **Output**: `data/processed/binning_tests.csv` containing one row per test with the full schema fields.  
  - **Verification**: `code/tests/test_analysis.py::test_binning_results_schema`.  

- [ ] T024 **Bonferroni Correction Utility** Implement `apply_bonferroni(p_values: List[float]) -> List[float]` used by both T023a and T023b.  

- [ ] T025 **Aggregate Statistical Results** Create a driver script `code/analysis/aggregate_results.py` that merges `regression_results.csv` and `binning_tests.csv` into a single `data/processed/statistical_results.csv`.  
  - **Verification**: The merged file contains all columns from both source files and passes a schema‑agnostic row‑count sanity check.  

- [ ] T027 **Null‑Hypothesis Logging**  
  - **Description**: Extend `code/analysis/stats.py` to emit an INFO log line each time a test’s adjusted p‑value < 0.01, e.g., `"[REJECTED] Kruskal‑Wallis on SFR (p_adj=0.004)"`.  
  - **Verification**: Run the full analysis on a small sample and assert that `tests/logs/null_hypothesis.log` contains at least one such line.  

---

## Phase 4 – Robustness Validation & Sensitivity Analysis (User Story 3, P3)

- [ ] T028 **Sensitivity Sweep Unit Test** `code/tests/test_sensitivity.py::test_sensitivity_sweep` ensures the sweep function returns a DataFrame with columns `threshold_set`, `p_value_adj`, `significant`.  

- [ ] T029 **Millennium‑II Loader (Conditional)** Attempt to download the Millennium‑II halo catalog from the verified URL listed in `data/metadata.yaml`.  
  - **On Success**: Store HDF5 files under `data/raw/millennium/` and record version info in `metadata.yaml`.  
  - **On Failure**: Immediately trigger T031‑LogGap (see Phase 5).  

- [ ] T030 **Sensitivity Logic Definition** Implement `code/analysis/sensitivity.py` exposing `run_sweep(thresholds: List[Tuple[float,float]]) -> pd.DataFrame`.  

- [ ] T030‑RunSweep **Sensitivity Orchestration** Create `code/analysis/run_sensitivity.py` that (1) loads the mass‑matched chunks, (2) iterates over the four threshold sets `{0.45,0.55,0.75,0.85}`, (3) re‑runs the binning tests (T023b) for each set, and (4) writes `data/processed/sensitivity_results.csv`.  
  - **Verification**: `code/tests/test_sensitivity.py::test_sweep_results` confirms four rows, one per threshold set.  

- [ ] T031‑LogGap **Data‑Gap Logging** If any Millennium‑II or WDM fetch fails, append `"millennium_url": "unverified"` (or `"wdm_url": "unverified"`) to `data/metadata.yaml` and write `outputs/reports/gap_log.md` describing the missing datasets. Also mark SC‑004 as “Not Measurable” in the final report template.  

- [ ] T032 **Sensitivity Report** Generate `outputs/reports/sensitivity_report.md` summarizing p‑value stability, variance, and rank‑order preservation per SC‑003.  

- [ ] T032‑VerifySC003 **SC‑003 Verification** Implement `code/tests/test_sensitivity.py::test_sc003_metric` that computes variance of p‑values across thresholds and checks the rank‑order condition; writes a pass/fail note to `outputs/reports/sc003_verification.md`.  

- [ ] T033 **Cross‑Dataset Comparison** After successful Millennium‑II (or after logging a gap), produce `outputs/reports/cross_dataset_comparison.md` that contrasts correlation coefficients and p‑values between TNG‑100 and Millennium‑II (or notes absence).  

---

## Phase 5 – Orientation Misalignment Analysis (User Story 4, P3)

- [ ] T035 **Alignment Unit Test** `code/tests/test_alignment.py::test_angle_calculation` verifies that the angle between two normalized vectors is computed via `arccos(dot)` and lies within `[0,180]`.  

- [ ] T036 **Spin & Major‑Axis Calculation** Implement `code/processing/alignment.py` to (1) compute halo spin vectors from dark‑matter particle angular momenta, (2) compute galaxy spin vectors from stellar particles, and (3) calculate the major‑axis eigenvectors for both.  

- [ ] T037 **Misalignment Angle Computation** Extend `alignment.py` to join halo and galaxy tables on `halo_id` and compute `spin_angle_deg` (halo‑spin vs galaxy‑spin) and `axis_angle_deg` (halo‑major‑axis vs galaxy‑major‑axis).  

- [ ] T038 **Alignment CSV Output** Write the results to `data/processed/alignment_angles.csv` with schema: `halo_id`, `galaxy_id`, `spin_angle_deg`, `axis_angle_deg`, `associational_only=true`.  
  - **Verification**: `code/tests/test_alignment.py::test_output_schema` checks column types and flag presence.  

- [ ] T039 **Misalignment Correlation & Mass‑Controlled Regression**  
  - **Description**: Using `statsmodels`, regress each galaxy property (SFR, Effective Radius) on `spin_angle_deg`, `axis_angle_deg`, and `mass_total`.  
  - **Input**: `alignment_angles.csv` merged with `matched_chunks/` data.  
  - **Output**: `data/processed/alignment_correlations.csv` containing regression coefficients, p‑values, adjusted p‑values, significance flags, and 95 % CIs, plus the `mass_coefficient`.  
  - **Verification**: `code/tests/test_analysis.py::test_alignment_regression_schema`.  

- [ ] T040 **Integrate Misalignment Results into Final Report** Append a Markdown section to `outputs/reports/final_report.md` summarizing the correlation coefficients, regression outcomes, and scientific interpretation of the misalignment analysis.  

---

## Phase N – Polishing & Cross‑Cutting Concerns  

- [ ] T041 **Documentation Update** Revise `README.md` and `docs/quickstart.md` to reflect the full pipeline commands (`python -m code.main --run-all`).  

- [ ] T042 **Code Cleanup** Run `ruff format` and `ruff check`; commit any auto‑fixed changes.  

- [ ] T043 **Performance Optimisation** Profile the streaming pipeline and, if needed, replace any `np.linalg.eig` calls with `np.linalg.svd` for better memory usage; ensure total runtime stays < 6 h on the GitHub Actions free tier.  

- [ ] T044 **Additional Edge‑Case Tests** Add tests for (a) singular inertia tensors, (b) outlier SFR values, and (c) halos where the central galaxy is not the most massive subhalo.  

- [ ] T045 **Quickstart Validation** Execute `scripts/validate_quickstart.sh` which runs the minimal pipeline on a single streamed chunk and asserts that `halo_shapes.csv` and `galaxy_properties.csv` each contain ≥ 1 row.  

- [ ] T046 **Final Research Report Generation** Implement `code/report/generate_report.py` that pulls tables/figures from `data/processed/` and `outputs/figures/` into `outputs/reports/final_report.md` using the provided template.  

- [ ] T047 **Metadata Flag Compliance Check** Add `code/utils/verification.py` that scans **all** generated CSV/JSON/MD files for the `associational_only=true` flag and writes `outputs/reports/metadata_compliance_report.md` summarising any violations.  

---

## Dependency & Execution Order Summary  

1. **Phase 1** (setup) must finish before any other phase.  
2. **Phase 2** (US 1) depends only on Phase 1.  
3. **Phase 3** (US 2) requires the outputs of Phase 2 (`halo_shapes.csv`, `galaxy_properties.csv`).  
4. **Phase 4** (US 3) requires the statistical results from Phase 3 and, optionally, successful Millennium‑II fetches.  
5. **Phase 5** (US 4) needs the raw halo/galaxy data from Phase 2 and the statistical framework from Phase 3.  
6. **Phase N** runs after all scientific phases are complete and validates reproducibility, documentation, and compliance.  

All tasks are written as independent, checkable units; each includes a concrete artifact path and a deterministic verification step that can be executed on the CPU‑only GitHub Actions runner.
