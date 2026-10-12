# Tasks: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  

The list follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
All tasks are ordered to respect data flow; each includes the exact artifact path(s) it
produces and a deterministic verification step that can be run on the CPU‑only
GitHub‑Actions runner.

---  

## Phase 1 – Setup and First End‑to‑End Analysis  

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
- [ ] T001a **[P]** Create the core Python package hierarchy under `code/` (`ingestion`, `processing`, `analysis`, `utils`, `tests`).  
  - **Path**: `code/` and sub‑directories.  
  - **Verification**: `ls -R code/` lists the expected directories and an empty `__init__.py` in each.  

- [ ] T001b **[P]** Create the data directory hierarchy for raw and processed assets.  
  - **Path**: `data/raw/tng100/`, `data/raw/millennium/`, `data/processed/`, `data/metadata.yaml`.  
  - **Verification**: `tree data/` shows the four sub‑folders and a non‑empty `metadata.yaml` file (even if only a placeholder comment).  

- [ ] T001c **[P]** Create output and documentation directories.  
  - **Path**: `outputs/figures/`, `outputs/reports/`, `docs/quickstart.md`, `docs/README.md`.  
  - **Verification**: `ls -R outputs/ docs/` lists the directories and the two markdown files; each markdown file contains a top‑level header (`# Quickstart` or `# README`).  

- [ ] T002 **[P]** Add placeholder documentation in `docs/quickstart.md` and `docs/README.md` describing how to run the pipeline (`python -m code.main`).  
  - **Verification**: Both files exist and contain a code block with the command.  

- [ ] T003a **[P]** Add a minimal `.ruff.toml` at the repository root that enables core lint rules for Python 3.11.  
  - **Path**: `.ruff.toml`.  
  - **Verification**: Running `ruff check .` returns *no* syntax errors (exit code 0).  

- [ ] T003b **[P]** Add `pyproject.toml` with Black configuration (`line-length = 88`).  
  - **Verification**: `black --check .` exits with code 0.  

- [ ] T004 **[P]** Implement `code/utils/config.py` containing a seeded random generator (`random.seed(42)`) and project‑wide path constants (`PROJECT_ROOT`, `DATA_ROOT`, etc.).  
  - **Verification**: Importing the module in a REPL reproduces the same random state.  

- [ ] T005 **[P]** Implement `code/utils/io.py` with streaming CSV/Parquet read‑write helpers that automatically inject the required `associational_only=true` flag into file headers/metadata.  
  - **Verification**: Write a test CSV with the helper and `head -n 1` shows the flag.  

- [ ] T006 **[P]** Add `code/utils/logging.py` and configure a basic logger in `code/main.py`.  
  - **Verification**: Running `python -m code.main` prints a timestamped INFO line to stdout.  

- [ ] T026a **[P]** Extend `code/utils/io.py` with `write_associational_flag()` that writes the flag to CSV headers and JSON metadata.  
- [ ] T026b **[P]** Update `code/ingestion/tng_loader.py` (and any future ingestion scripts) to call `write_associational_flag()` on every output file.  
- [ ] T026c **[P]** Add `code/tests/test_io.py::test_associational_flag` ensuring the flag appears in all written CSVs.  

- [ ] T010 **[P]** Implement integration test `code/tests/test_pipeline.py::test_pipeline_chunking` that simulates downloading a single TNG‑100 HDF5 chunk and verifies a processed halo row appears in `data/processed/halo_shapes.csv`.  

---  

## Phase 2 – Core Data Ingestion & Halo Shape Computation (User Story 1, P1)  

- [ ] T011 **[P]** Implement `code/ingestion/tng_loader.py` to query the official TNG API, paginate halo files, download HDF5 chunks to `data/raw/tng100/`, and record checksums in `data/metadata.yaml`.  
  - **Verification**: After execution, `data/raw/tng100/` contains at least one `*.hdf5` file and `metadata.yaml` has a matching entry.  

- [ ] T012 **[P]** Create `code/processing/inertia_tensor.py` with signature `compute_reduced_inertia_tensor(particle_positions, masses) -> np.ndarray`.  
  - **Verification**: Importing the module and calling the function raises `NotImplementedError`.  

- [ ] T013 **[P]** Implement `code/processing/shape_metrics.py` with `compute_axial_ratios(eigenvalues) -> (b_a, c_a)` and `compute_triaxiality(a, b, c) -> T`.  
  - **Verification**: `code/tests/test_shape.py` validates known eigenvalue sets.  

- [ ] T014 **[P]** Add resolution filter in `shape_metrics.py` that drops any halo with `n_dm_particles < 10_000`.  
  - **Verification**: `test_filter_low_res` confirms such halos never appear in the output CSV.  

- [ ] T016 **[P]** Implement `code/processing/pipeline_runner.py` that streams the full FoF catalog using `datasets.load_dataset(..., streaming=True)`, processes each halo chunk, applies the filter, computes shape metrics, and writes rows incrementally to `data/processed/halo_shapes.csv`.  
  - **Verification**: After a short run on a single stream chunk, the CSV contains ≥ 1 row with `0 < b_a ≤ 1`, `0 < c_a ≤ 1`, and `0 ≤ T ≤ 1`.  

- [ ] T017 **[P]** Extend the runner to (1) merge streamed chunks, (2) validate axial‑ratio bounds, (3) log excluded halos to `data/processed/exclusion_log.json`, and (4) write the final CSV conforming to `halo_schema.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_validation.py::test_axial_ratio_bounds` and `::test_completeness_check` both pass.  

- [ ] T018 **[P]** Extend `tng_loader.py` to extract, for each FoF halo, the central galaxy’s `stellar_mass`, `sfr`, and `effective_radius`, writing them to `data/processed/galaxy_properties.csv`.  
  - **Verification**: The CSV contains a matching `halo_id` column and passes `test_galaxy_schema` in `code/tests/test_ingestion.py`.  

- [ ] T009 **[P]** Add `code/tests/test_inertia.py::test_singular_matrix_raises_error` that supplies < 10 000 particles and expects a `ValueError`.  
  - **Verification**: Test passes after T014 is implemented.  

---  

## Phase 3 – Statistical Correlation, Binning & Mass Control (User Story 2, P2)  

- [ ] T020a **[P]** Unit test `code/tests/test_stats.py::test_binning_logic` confirming that `c/a < 0.5 → “Prolate”`, `0.5 ≤ c/a ≤ 0.8 → “Triaxial”`, `c/a > 0.8 → “Spherical”`.  

- [ ] T020b **[P]** Unit test `code/tests/test_stats.py::test_bonferroni_correction` validating raw p‑values are multiplied by the number of comparisons and capped at 1.  

- [ ] T020c **[P]** Add `assign_shape_bin(c_a_ratio)` to `shape_metrics.py` returning the categorical bin string.  

- [ ] T021 **[P]** Define in `code/analysis/stats.py` the function `match_by_mass(df_halo, df_gal, tolerance=0.05) -> pd.DataFrame`.  

- [ ] T021b **[P]** Implement a block‑wise nearest‑neighbor matcher that reads `halo_shapes.csv` and `galaxy_properties.csv` in chunks, pairs halos with galaxies of similar `mass_total` (within 5 % tolerance), and writes each block to `data/processed/matched_chunks/match_###.csv`.  
  - **Verification**: `code/tests/test_stats.py::test_mass_matching_chunks` checks that each output file contains the required columns.  

- [ ] T022 **[P]** Implement non‑parametric tests (`kruskal_wallis`, `mann_whitney_u`, `kolmogorov_smirnov`) in `stats.py`, each returning a dict that conforms to `analysis_result_schema.schema.yaml`.  

- [ ] T023a **[P]** Linear regression with mass control:  
  - **Description**: Using `statsmodels.OLS`, fit separate regressions for each galaxy property (SFR, Effective Radius) with predictors `triaxiality`, `b_a_ratio`, and `mass_total`. Iterate over all CSVs in `data/processed/matched_chunks/`.  
  - **Output**: `data/processed/regression_results.csv` with columns `test_type`, `property`, `predictor`, `coefficient`, `p_value_raw`, `p_value_adj`, `significant`, `ci_lower`, `ci_upper`, `threshold_set`, `associational_only`.  
  - **Verification**: `code/tests/test_analysis.py::test_regression_output_schema` validates the CSV against the JSON schema.  

- [ ] T023b **[P]** Binning statistical tests:  
  - **Description**: For each galaxy property, run Kruskal‑Wallis across the three shape bins, then pairwise Mann‑Whitney U and KS tests, applying Bonferroni correction (via `apply_bonferroni`).  
  - **Input**: The mass‑matched chunk CSVs from T021b.  
  - **Output**: `data/processed/binning_tests.csv` where each row follows `analysis_result_schema.schema.yaml`.  
  - **Verification**: `code/tests/test_analysis.py::test_binning_results_schema` confirms schema compliance.  

- [ ] T024 **[P]** Implement utility `apply_bonferroni(p_values: List[float]) -> List[float]` used by both T023a and T023b.  

- [ ] T025 **[P]** Aggregate statistical results:  
  - **Description**: `code/analysis/aggregate_results.py` merges `regression_results.csv` and `binning_tests.csv` into a single `data/processed/statistical_results.csv`.  
  - **Verification**: The merged file contains all columns from both sources, has no duplicate header rows, and passes a sanity check that the row count equals the sum of the two inputs.  

- [ ] T027 **[P]** Null‑hypothesis rejection logging:  
  - **Description**: Extend `code/analysis/stats.py` so that whenever a test’s Bonferroni‑adjusted p‑value < 0.01, an INFO log line is emitted, e.g., `"[REJECTED] Kruskal‑Wallis on SFR (p_adj=0.004)"`.  
  - **Output**: Log file `outputs/reports/null_hypothesis.log`.  
  - **Verification**: Run the full analysis on a small sample and assert that `null_hypothesis.log` contains at least one line matching the regex `\[\w+\] .* p_adj=.*`.  

---  

## Phase 4 – Robustness Validation & Sensitivity Analysis (User Story 3, P3)  

- [ ] T028 **[P]** Unit test `code/tests/test_sensitivity.py::test_sensitivity_sweep` ensuring the sweep function returns a DataFrame with columns `threshold_set`, `p_value_adj`, `significant`.  

- [ ] T029 **[P]** Attempt to download the Millennium‑II halo catalog from the verified URL listed in `data/metadata.yaml`.  
  - **On Success**: Store HDF5 files under `data/raw/millennium/` and record version info in `metadata.yaml`.  
  - **On Failure**: Trigger T031‑LogGap (see Phase 5).  

- [ ] T030 **[P]** Implement `code/analysis/sensitivity.py` exposing `run_sweep(thresholds: List[Tuple[float,float]]) -> pd.DataFrame`.  

- [ ] T030‑RunSweep **[P]** Create `code/analysis/run_sensitivity.py` that (1) loads mass‑matched chunks, (2) iterates over the four threshold sets `{0.45,0.55,0.75,0.85}`, (3) re‑runs the binning tests (T023b) for each set, and (4) writes `data/processed/sensitivity_results.csv`.  
  - **Verification**: `code/tests/test_sensitivity.py::test_sweep_results` confirms four rows, one per threshold set.  

- [ ] T031‑LogGap **[P]** If any Millennium‑II or warm‑dark‑matter fetch fails, append `"millennium_url": "unverified"` (or `"wdm_url": "unverified"`) to `data/metadata.yaml` and write `outputs/reports/gap_log.md` describing the missing datasets. Also mark SC‑004 as “Not Measurable” in the final report template.  

- [ ] T032 **[P]** Generate `outputs/reports/sensitivity_report.md` summarising p‑value stability, variance, and rank‑order preservation per SC‑003.  

- [ ] T032‑VerifySC003 **[P]** Implement `code/tests/test_sensitivity.py::test_sc003_metric` that computes the variance of p‑values across thresholds and checks the rank‑order condition; write a pass/fail note to `outputs/reports/sc003_verification.md`.  

- [ ] T033 **[P]** After a successful Millennium‑II run (or after logging a gap), produce `outputs/reports/cross_dataset_comparison.md` contrasting correlation coefficients and p‑values between TNG‑100 and Millennium‑II (or noting their absence).  

---  

## Phase 5 – Orientation Misalignment Analysis (User Story 4, P3)  

- [ ] T035 **[P]** Unit test `code/tests/test_alignment.py::test_angle_calculation` confirming that the angle between two normalized vectors is computed via `arccos(dot)` and lies within `[0,180]`.  

- [ ] T036 **[P]** Implement `code/processing/alignment.py` to (1) compute halo spin vectors from dark‑matter particle angular momenta, (2) compute galaxy spin vectors from stellar particles, and (3) calculate the major‑axis eigenvectors for both.  

- [ ] T037 **[P]** Extend `alignment.py` to join halo and galaxy tables on `halo_id` and compute `spin_angle_deg` (halo‑spin vs galaxy‑spin) and `axis_angle_deg` (halo‑major‑axis vs galaxy‑major‑axis).  

- [ ] T038 **[P]** Write results to `data/processed/alignment_angles.csv` with schema `halo_id`, `galaxy_id`, `spin_angle_deg`, `axis_angle_deg`, `associational_only=true`.  
  - **Verification**: `code/tests/test_alignment.py::test_output_schema` checks column types and flag presence.  

- [ ] T039 **[P]** Misalignment regression: using `statsmodels`, regress each galaxy property (SFR, Effective Radius) on `spin_angle_deg`, `axis_angle_deg`, and `mass_total`.  
  - **Input**: `alignment_angles.csv` merged with the mass‑matched chunk data.  
  - **Output**: `data/processed/alignment_correlations.csv` containing regression coefficients, raw and Bonferroni‑adjusted p‑values, significance flags, 95 % CIs, and the `mass_coefficient`.  
  - **Verification**: `code/tests/test_analysis.py::test_alignment_regression_schema` validates the CSV against the schema.  

- [ ] T040 **[P]** Append a Markdown section to `outputs/reports/final_report.md` summarising the misalignment correlation coefficients, regression outcomes, and scientific interpretation.  

---  

## Phase N – Polishing & Cross‑Cutting Concerns  

- [ ] T041 **[P]** Update `README.md` and `docs/quickstart.md` to reflect the full pipeline commands (`python -m code.main --run-all`).  

- [ ] T042 **[P]** Run `ruff format` and `ruff check`; commit any auto‑fixed changes.  

- [ ] T043 **[P]** Profile the streaming pipeline; if memory usage is high, replace any `np.linalg.eig` calls with `np.linalg.svd` to stay below the 6‑hour / 7 GB RAM limit on GitHub Actions.  

- [ ] T044 **[P]** Add edge‑case tests for (a) singular inertia tensors, (b) extreme SFR outliers, and (c) halos where the central galaxy is not the most massive subhalo.  

- [ ] T045 **[P]** Execute `scripts/validate_quickstart.sh` which runs the minimal pipeline on a single streamed chunk and asserts that `halo_shapes.csv` and `galaxy_properties.csv` each contain ≥ 1 row.  

- [ ] T046 **[P]** Implement `code/report/generate_report.py` that pulls tables/figures from `data/processed/` and `outputs/figures/` into `outputs/reports/final_report.md` using the provided template.  

- [ ] T047 **[P]** Add `code/utils/verification.py` that scans **all** generated CSV/JSON/MD files for the `associational_only=true` flag and writes `outputs/reports/metadata_compliance_report.md` summarising any violations.  

---  

### Dependency & Execution Order Summary  

1. **Phase 1** must finish before any other phase.  
2. **Phase 2** (US 1) depends only on Phase 1.  
3. **Phase 3** (US 2) requires the outputs of Phase 2 (`halo_shapes.csv`, `galaxy_properties.csv`).  
4. **Phase 4** (US 3) needs the statistical results from Phase 3 and, optionally, successful Millennium‑II fetches.  
5. **Phase 5** (US 4) needs the raw halo/galaxy data from Phase 2 and the analysis framework from Phase 3.  
6. **Phase N** runs after all scientific phases are complete and validates reproducibility, documentation, and compliance.  

All tasks are expressed as concrete, checkable units that produce real files or logs; the verifier can run the associated unit‑tests to confirm each requirement is satisfied.
