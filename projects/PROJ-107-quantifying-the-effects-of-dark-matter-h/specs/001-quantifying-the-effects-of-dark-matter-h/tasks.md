# Tasks: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  

All tasks are expressed as concrete, checkable units that produce real files or logs.  
Each task lists the artifact paths it creates and an automated verification step that can be run on the CPU‑only GitHub‑Actions runner.

---  

## Phase 1 – Project scaffolding & core utilities  

- [ ] **T001** [US‑0] Create the full project directory hierarchy and verify its existence.  
  - **Paths created**:  
    - `code/ingestion/`, `code/processing/`, `code/analysis/`, `code/utils/`, `code/tests/`  
    - `data/raw/tng100/`, `data/raw/millennium/`, `data/processed/`  
    - `outputs/figures/`, `outputs/reports/`  
    - `docs/quickstart.md`, `docs/README.md`  
  - **Verification**: Run `tree -L 2 .` and assert that all listed directories appear; the command must exit with code 0.  
  - **Additional verification**: Capture the `tree` output to `data_dir_tree.txt` (data hierarchy) and `output_dir_tree.txt` (output/docs hierarchy) for later audit.

- [ ] **T002** [US‑0] Add core utility modules and ensure the required “associational_only” flag is automatically written to every CSV/Parquet output.  
  - **Files**: `code/utils/config.py` (sets `random.seed(42)` and path constants), `code/utils/io.py` (streaming read/write helpers that inject `associational_only=true` into file metadata), `code/utils/logging.py` (basic logger used by the pipeline).  
  - **Verification**:  
    1. Import each module in a fresh Python REPL – no ImportError.  
    2. Use `io.write_csv(df, "tmp.csv")` on a dummy DataFrame and check that the first line contains `associational_only=true`.  

- [ ] **T003** [US‑0] Create lint/format configuration files to satisfy code‑quality checks.  
  - **Files**: `.ruff.toml` (enables core lint rules for Python 3.11) and `pyproject.toml` (Black configuration `line-length = 88`).  
  - **Verification**: `ruff check .` returns exit code 0; `black --check .` returns exit code 0.  

- [ ] **T004** [US‑1] Download the IllustrisTNG‑100 public data, verify integrity, and store raw files.  
  - **Script**: `code/ingestion/tng_loader.py` (uses the official TNG API, paginates the FoF halo catalog, streams HDF5 chunks to `data/raw/tng100/`).  
  - **Metadata**: `data/metadata.yaml` is updated with SHA‑256 checksums for each downloaded file.  
  - **Verification**: After execution, `data/raw/tng100/` contains at least one `*.hdf5` file and `metadata.yaml` lists a matching checksum entry.  

- [ ] **T005** [US‑1] Process each halo chunk to compute reduced inertia tensors, axial ratios, triaxiality, and filter out low‑resolution haloes ( <n = 10 000 ).  
  - **Modules**: `code/processing/inertia_tensor.py` (function `compute_reduced_inertia_tensor`), `code/processing/shape_metrics.py` (functions `compute_axial_ratios`, `compute_triaxiality`, `assign_shape_bin`).  
  - **Output**: `data/processed/halo_shapes.csv` conforming to `halo_schema.schema.yaml`.  
  - **Verification**:  
    1. `csvstat data/processed/halo_shapes.csv` shows columns matching the schema.  
    2. All rows satisfy `0 < b_a ≤ 1`, `0 < c_a ≤ 1`, `0 ≤ T ≤ 1`.  
    3. No row has `n_dm_particles < 10000`.  

- [ ] **T006** [US‑1] Extract central‑galaxy properties (stellar mass, SFR, effective radius) and join them to the halo table.  
  - **Script**: Extension of `tng_loader.py` that reads the subhalo catalog, selects the most massive subhalo per FoF halo, and writes `data/processed/galaxy_properties.csv`.  
  - **Verification**: The CSV contains the columns `halo_id`, `stellar_mass`, `sfr`, `effective_radius` and passes the `halo_schema`‑required fields (the `associational_only` flag is present).  

## Phase 2 – Data ingestion & halo‑shape computation (User Story 1, FR‑001, FR‑002)  

- [ ] **T007** [US‑2] Perform mass‑matching (within 5 % tolerance) between haloes and galaxies and write chunked matched files.  
  - **Function**: `code/analysis/mass_match.py` → `match_by_mass(df_halo, df_gal, tolerance=0.05)`.  
  - **Outputs**: `data/processed/matched_chunks/match_001.csv`, `match_002.csv`, … (one per processed chunk).  
  - **Verification**: Each CSV contains the columns `halo_id`, `mass_total`, `sfr`, `effective_radius`, and the mass difference between paired rows never exceeds 5 %.  

- [ ] **T008** [US‑2] Run non‑parametric statistical tests across the three shape bins (prolate, triaxial, spherical) on the mass‑matched data.  
  - **Functions** in `code/analysis/stats.py`: `kruskal_wallis`, `mann_whitney_u`, `kolmogorov_smirnov`.  
  - **Bonferroni correction** applied via `apply_bonferroni(p_values)`.  
  - **Output**: `data/processed/binning_tests.csv` where each row conforms to `analysis_result_schema.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_analysis.py::test_binning_results_schema` passes; the file contains a `threshold_set` column with the default “0.5,0.8”.  

- [ ] **T009** [US‑2] Fit linear regressions controlling for halo mass for each galaxy property.  
  - **Implementation**: `code/analysis/regression.py` uses `statsmodels.OLS` on each matched chunk, predictors = `triaxiality`, `b_a_ratio`, `mass_total`.  
  - **Output**: `data/processed/regression_results.csv` adhering to `analysis_result_schema.schema.yaml` (one row per property‑predictor combination).  
  - **Verification**: `pytest code/tests/test_analysis.py::test_regression_output_schema` passes; the CSV includes `effect_size`, `ci_lower`, `ci_upper`, and the required `associational_only=true` flag.  

- [ ] **T010** [US‑2] Aggregate the two result tables into a single master file.  
  - **Script**: `code/analysis/aggregate_results.py` merges `binning_tests.csv` and `regression_results.csv` → `data/processed/statistical_results.csv`.  
  - **Verification**: The merged file contains all columns from both sources, row count equals the sum of the inputs, and `code/tests/test_aggregation.py::test_aggregation` validates schema‑agnostic integrity.  

- [ ] **T011** [US‑2] Log every instance where a Bonferroni‑adjusted p‑value < 0.01.  
  - **Change**: `code/analysis/stats.py` now emits an INFO line to `outputs/reports/null_hypothesis.log` of the form `"[REJECTED] <Test> on <Property> (p_adj=0.004)"`.  
  - **Verification**: After a full run on a small sample, `grep -c "\[REJECTED\]" outputs at least one line; `code/tests/test_logging.py::test_null_hypothesis_log` confirms the pattern.  

## Phase 3 – Robustness & sensitivity (User Story 3, FR‑006, FR‑007)  

- [ ] **T012** [US‑3] Run a sensitivity sweep over the four bin‑threshold sets `{0.45, 0.55, 0.75, 0.85}`.  
  - **Function**: `code/analysis/sensitivity.py` → `run_sweep(thresholds)`.  
  - **Output**: `data/processed/sensitivity_results.csv` with columns `threshold_set`, `test_type`, `property`, `p_value_adj`, `significant`.  
  - **Verification**: The CSV contains exactly four rows (one per threshold set) and `code/tests/test_sensitivity.py::test_sweep_results` passes.  

- [ ] **T013** [US‑3] Validate sensitivity stability (SC‑003).  
  - **Script**: `code/analysis/validate_sensitivity.py` computes the variance of `p_value_adj` across thresholds and checks that either variance ≤ 0.001 **or** the rank order of significance is unchanged.  
  - **Report**: `outputs/reports/sensitivity_report.md` summarises the variance, rank‑order check, and declares whether SC‑003 is satisfied.  
  - **Verification**: `code/tests/test_sensitivity.py::test_sc003_metric` succeeds; the report file exists.  

- [ ] **T014** [US‑3] Attempt to download the Millennium‑II halo catalog (verified URL).  
  - **Script**: `code/ingestion/millennium_loader.py`.  
  - **Success path**: Raw files stored under `data/raw/millennium/`, checksum added to `metadata.yaml`, and the full pipeline (T004‑T010) rerun, producing `outputs/reports/cross_dataset_comparison.md`.  
  - **Failure path**: If the URL is unreachable, append `"millennium_url": "unverified"` to `metadata.yaml` and write `outputs/reports/gap_log.md` describing the missing dataset; mark SC‑004 as “Not Measurable” in the final report template.  
  - **Verification**: After execution, either the Millennium‑II raw directory exists **or** `gap_log.md` is present and contains the required JSON key.  

- [ ] **T015** [US‑3] Generate the cross‑dataset comparison report (or note its absence).  
  - **Report**: `outputs/reports/cross_dataset_comparison.md` lists correlation coefficients and p‑values for TNG‑100 vs. Millennium‑II (or states “Millennium‑II unavailable”).  
  - **Verification**: The file exists and contains a markdown table with columns `Dataset`, `Property`, `Correlation`, `p_value_adj`.  

## Phase 4 – Orientation mis‑alignment analysis (User Story 4, FR‑009, FR‑010)  

- [ ] **T016** [US‑4] Compute halo and galaxy spin vectors and major‑axis eigenvectors, then calculate misalignment angles.  
  - **Module**: `code/processing/alignment.py` (functions `compute_halo_spin`, `compute_galaxy_spin`, `compute_major_axis`, `angle_between`).  
  - **Output**: `data/processed/alignment_angles.csv` with schema `halo_id`, `spin_angle_deg`, `axis_angle_deg`, `associational_only=true`.  
  - **Verification**: `pytest code/tests/test_alignment.py::test_output_schema` passes; all angle values lie in `[0,180]`.  

- [ ] **T017** [US‑4] Regress galaxy properties on the misalignment angles while controlling for halo mass.  
  - **Script**: `code/analysis/alignment_regression.py` (uses `statsmodels.OLS`).  
  - **Output**: `data/processed/alignment_correlations.csv` conforming to `analysis_result_schema.schema.yaml`.  
  - **Verification**: `code/tests/test_analysis.py::test_alignment_regression_schema` passes; the file includes `effect_size` and `ci_lower/ci_upper`.  

- [ ] **T018** [US‑4] Add a summary section on misalignment results to the final report.  
  - **File**: Append to `outputs/reports/final_report.md` a markdown block with regression coefficients, significance flags, and a brief scientific interpretation.  
  - **Verification**: The report contains the heading “## Orientation Mis‑alignment Results” and lists at least one numeric coefficient.  

## Phase 5 – Polishing, reproducibility & hand‑off  

- [ ] **T019** [US‑0] Update documentation to reflect the full pipeline commands.  
  - **Files**: `docs/quickstart.md` (example `python -m code.main --run-all`) and `README.md` (project overview).  
  - **Verification**: Both files contain the exact command string; `grep "python -m code.main --run-all"` returns a match in each.  

- [ ] **T020** [US‑0] Run code formatters and linters; commit any auto‑fixed changes.  
  - **Commands**: `ruff format .`, `ruff check .`, `black --check .`.  
  - **Verification**: All three commands exit with code 0.  

- [ ] **T021** [US‑0] Profile the streaming pipeline; if peak RAM exceeds 6 GB replace any `np.linalg.eig` calls with `np.linalg.svd` to stay within the GitHub‑Actions limits.  
  - **Report**: `outputs/reports/profiling_report.md` lists peak memory usage and any code changes made.  
  - **Verification**: The report exists and shows `Peak RAM ≤ 6 GB`.  

- [ ] **T022** [US‑0] Add edge‑case unit tests for (a) singular inertia tensors, (b) extreme SFR outliers, and (c) haloes where the central galaxy is not the most massive subhalo.  
  - **Tests**: `code/tests/test_edge_cases.py` with three test functions.  
  - **Verification**: `pytest code/tests/test_edge_cases.py` runs with all tests passing.  

- [ ] **T023** [US‑0] Execute the minimal end‑to‑end pipeline on a single streamed chunk and assert that `halo_shapes.csv` and `galaxy_properties.csv` each contain at least one row.  
  - **Script**: `scripts/validate_minimal_pipeline.sh`.  
  - **Verification**: The script exits with code 0 and prints “PASS” for both files.  

- [ ] **T024** [US‑0] Generate the final research report linking all tables and figures.  
  - **Tool**: `code/report/generate_report.py` reads the CSV artefacts and produces `outputs/reports/final_report.md` (markdown) and a placeholder PDF `outputs/reports/final_report.pdf`.  
  - **Verification**: The markdown file contains sections for “Data Ingestion”, “Statistical Analysis”, “Sensitivity”, “Cross‑Dataset Validation”, and “Orientation Mis‑alignment”.  

- [ ] **T025** [US‑0] Run a global compliance check that every generated CSV/JSON/MD file includes the required `associational_only=true` flag.  
  - **Script**: `code/utils/verification.py` → `outputs/reports/metadata_compliance_report.md`.  
  - **Verification**: The report lists any violations; a clean run must state “All files contain the required flag”.  

## Phase 6 – Additional tasks to satisfy all review concerns  

- [ ] **T026** [US‑2] Create explicit shape‑binning step (Prolate, Triaxial, Spherical) after halo shape computation.  
  - **Script**: Extend `code/processing/shape_metrics.py` with `assign_shape_bin` that writes the `shape_bin` column to `data/processed/halo_shapes.csv`.  
  - **Verification**: `csvstat data/processed/halo_shapes.csv` shows a categorical `shape_bin` column with only the three allowed values.  

- [ ] **T027** [US‑2] Implement non‑parametric statistical tests and generate `data/processed/binning_tests.csv`.  
  - **Modules**: Add full implementations of Kruskal‑Wallis, Mann‑Whitney U, and Kolmogorov‑Smirnov in `code/analysis/stats.py`.  
  - **Verification**: Schema validation test passes; the CSV contains a `threshold_set` column set to “0.5,0.8”.  

- [ ] **T028** [US‑2] Implement linear regression controlling for halo mass and output `data/processed/regression_results.csv`.  
  - **Modules**: `code/analysis/regression.py` uses `statsmodels.OLS` with predictors `triaxiality`, `b_a_ratio`, and `mass_total`.  
  - **Verification**: Regression output conforms to `analysis_result_schema.schema.yaml`.  

- [ ] **T029** [US‑2] Compute Spearman correlation between halo triaxiality and galaxy SFR; write `data/processed/spearman_correlation.csv`.  
  - **Script**: `code/analysis/correlation.py` produces a single‑row CSV with `rho`, `p_value`, and `associational_only=true`.  
  - **Verification**: `pytest code/tests/test_correlation.py::test_spearman_output_schema` passes.  

- [ ] **T030** [US‑3] When Millennium‑II data is available, compute reproducibility metric comparing correlation coefficients between TNG‑100 and Millennium‑II; output `data/processed/reproducibility_metric.csv`.  
  - **Script**: `code/analysis/reproducibility.py` calculates absolute differences and signs, records “Not Measurable” when data missing.  
  - **Verification**: Reported metric conforms to a simple CSV schema and is referenced in the final report.  

- [ ] **T031** [US‑0] Profile total runtime and peak RAM; write `outputs/reports/profiling_report.md`.  
  - **Implementation**: Wrap the main pipeline in a timing/`resource` monitor; ensure peak RAM ≤ 6 GB.  
  - **Verification**: The report file exists and contains the measured values.  

- [ ] **T032** [US‑2] Verify that `outputs/reports/null_hypothesis.log` contains all Bonferroni‑adjusted p‑values < 0.01.  
  - **Verification script**: `code/utils/verification.py` scans the log and fails if any qualifying entry is missing.  

- [ ] **T033** [US‑0] Create lint/format configuration files (`.ruff.toml` and `pyproject.toml`).  
  - **Files**: `.ruff.toml` with `[tool.ruff]` core rules; `pyproject.toml` with `[tool.black] line-length = 88`.  
  - **Verification**: `ruff check .` and `black --check .` both exit with code 0.  

- [ ] **T034** [US‑0] Generate directory‑tree verification files (`data_dir_tree.txt` and `output_dir_tree.txt`) to prove hierarchy creation.  
  - **Verification**: Presence of both files and that they contain the expected directory listings.  

- [ ] **T035** [US‑1] Scaffold ingestion script `code/ingestion/tng_loader.py` and initial `data/metadata.yaml`.  
  - **Verification**: Script imports without error; metadata file exists with at least one checksum entry (placeholder).  

- [ ] **T036** [US‑1] Scaffold processing modules `code/processing/inertia_tensor.py` and `code/processing/shape_metrics.py`.  
  - **Verification**: Modules import; running a tiny synthetic halo produces a valid row in `halo_shapes.csv`.  

- [ ] **T037** [US‑1] Scaffold analysis modules `code/analysis/stats.py`, `code/analysis/regression.py`, `code/analysis/sensitivity.py`, and `code/analysis/alignment_regression.py`.  
  - **Verification**: Each module imports and can be called with minimal synthetic data to produce the corresponding CSV output.  

- [ ] **T038** [US‑0] Create aggregation script `code/analysis/aggregate_results.py` and generate `data/processed/statistical_results.csv`.  
  - **Verification**: Merged file exists and contains rows from both input result tables.  

- [ ] **T039** [US‑0] Update documentation (`docs/quickstart.md` and `README.md`) with the exact command `python -m code.main --run-all`.  
  - **Verification**: Grep for the command string succeeds in both files.  

- [ ] **T040** [US‑0] Scaffold report generation script `code/report/generate_report.py` and produce placeholder `outputs/reports/final_report.md` and `final_report.pdf`.  
  - **Verification**: Both artifacts exist; the markdown contains the required section headings.  

- [ ] **T041** [US‑0] Create verification utility `code/utils/verification.py` that checks the `associational_only=true` flag across all generated CSV/JSON/MD files and writes `outputs/reports/metadata_compliance_report.md`.  
  - **Verification**: Running the utility produces a report stating “All files contain the required flag” when appropriate.  
