# Tasks: Statistical Properties of Simulated Black Hole Mergers  

**Inputs**: `spec.md`, `plan.md`, data‑model, JSON‑Schema contracts, and reviewer feedback.  
All artifacts are produced under `data/`, `outputs/`, or `code/` directories.  
Tasks are ordered to respect data‑flow and the functional priorities defined in the specification.

---  

## Phase 0 – CI/CD execution constraints (US‑0, priority P0)

- [ ] T001 [P0] [US0] **Download GWTC‑1 and GWTC‑2 posterior sample archives from Zenodo and verify SHA‑256 checksums**   <!-- FAILED-IN-EXECUTION: code/src/data/download_gwtc.py exit=1; code/src/data/record_availability.py exit=1 -->
  *Implementation*: `code/src/data/download_gwtc.py` retrieves the HDF5 files from DOIs `10.5281/zenodo.3966973` and `10.5281/zenodo.3966974`, validates the SHA‑256 checksums obtained from Zenodo metadata, and retries up to three times with exponential back‑off (1 s, 2 s, 4 s).  
  *Outputs*: `data/raw/gwtc1.h5`, `data/raw/gwtc2.h5`.  
  *Verification*: `pytest tests/unit/test_download_gwtc.py` asserts both files exist, are readable as HDF5, and that their checksums match the expected values.

- [ ] T002 [P0] [US0] **Record data‑availability metadata and enforce free‑tier resource limits**  
  *Implementation*: `code/src/data/record_availability_and_resources.py` (1) writes a JSON report `data/results/data_availability.json` conforming to `result.schema.yaml` with `status: "verified"` for each source; (2) wraps the pipeline start/end with `code/src/utils/resource_monitor.py` to capture `wall_time_seconds`, `peak_memory_gb`, `peak_disk_gb` in `data/results/resource_usage.json`; (3) `code/src/analysis/check_resources.py` reads the usage file and aborts with a clear error if runtime > 6 h, memory > 7 GB, or disk > 20 GB.  
  *Outputs*: `data/results/data_availability.json`, `data/results/resource_usage.json`.  
  *Verification*: `pytest tests/unit/test_data_availability.py` validates the JSON against the schema and checks `status == "verified"`; `pytest tests/unit/test_check_resources.py` mocks limit violations and confirms the script fails, and passes when limits are respected.

---  

## Phase 1 – Observational data preprocessing (US‑1, priority P1)

- [ ] T003 [P1] [US1] **Create an i.i.d. point‑estimate dataset from GWTC posterior samples using hierarchical bootstrap**  
  *Implementation*: `code/src/data/preprocess_observations.py` loads `gwtc1.h5` and `gwtc2.h5`, **draws 500 posterior samples per event** (fixed seed `2026-10-24-01`), then performs a **hierarchical bootstrap**: resample events with replacement, and for each resampled event randomly select one of its 500 draws. From the selected draws it computes `mass_ratio = m2/m1` and `effective_spin`, filters rows with any NaN in the three key fields, and aborts if fewer than 100 valid events remain. The resulting CSV conforms to `gwtc_catalog.schema.yaml`.  
  *Output*: `data/processed/obs_point_estimates.csv`.  
  *Verification*: `pytest tests/unit/test_preprocess_observations.py` checks row count ≥ 100, required columns present, schema compliance, and that the hierarchical bootstrap procedure yields an i.i.d. dataset.

- [ ] T004 [P1] [US1] **Validate observational CSV schema and verify independence (lag‑1 autocorrelation)**  
  *Implementation*: `code/src/validation/validate_observations.py` (1) validates `obs_point_estimates.csv` against `gwtc_catalog.schema.yaml`; (2) computes lag‑1 autocorrelation for `mass_ratio` and `effective_spin` using `statsmodels.tsa.stattools.acf` and writes `data/results/obs_independence.json` containing `lag1_mass_ratio`, `lag1_effective_spin`, and a boolean `independence_flag` that is true only if `|ρ₁| < 0.1` for both parameters.  
  *Output*: `data/results/obs_independence.json`.  
  *Verification*: `pytest tests/unit/test_obs_independence.py` asserts that the JSON matches the schema, that the autocorrelation values are numeric, and that `independence_flag` is true; if false the test fails with a diagnostic message.

---  

## Phase 2 – Simulation catalog acquisition (US‑1b, priority P1)

- [ ] T005 [P1] [US1b] **Obtain binary‑BH population catalog from official IllustrisTNG/EAGLE releases**  
  *Implementation*: `code/src/data/acquire_simulation.py` attempts to (1) download the latest public snapshots of **IllustrisTNG‑300‑1** and **EAGLE Ref‑L0100N1504** from their official sites (streamed to avoid RAM overload); (2) apply the documented post‑processing mapping (Rodríguez et al. 2021) to infer `component_mass_1`, `component_mass_2`, `mass_ratio`, and `effective_spin`. **If the official releases cannot be fetched or the resulting catalog is missing any required field, the script aborts with an explicit error** (no synthetic fallback). The final catalog is saved as `data/raw/simulation_catalog.csv`.  
  *Output*: `data/raw/simulation_catalog.csv`.  
  *Verification*: `pytest tests/unit/test_acquire_simulation.py` validates that the CSV contains all required columns, has ≥ 100 rows, and writes `data/results/simulation_source.json` indicating the source was the official release and includes the SHA‑256 checksum of the file.

- [ ] T006 [P1] [US1b] **Validate simulation catalog schema**  
  *Implementation*: `code/src/validation/validate_simulation.py` checks `simulation_catalog.csv` against `simulation_catalog.schema.yaml` and writes `data/results/simulation_validation.json` with `status: "verified"` or detailed error messages.  
  *Output*: `data/results/simulation_validation.json`.  
  *Verification*: `pytest tests/unit/test_validate_simulation.py` ensures the JSON reports `"verified"` and that no schema violations exist.

---  

## Phase 3 – Selection‑bias weighting (US‑2, priority P2)

- [ ] T007 [P2] [US2] **Compute inverse‑probability detection‑efficiency weights and produce weighted catalogs**  
  *Implementation*: `code/src/analysis/selection_bias.py` loads the public LIGO‑Virgo detection‑efficiency array `data/raw/detection_efficiency.npy`, computes weight `w = 1 / efficiency` for each event in `obs_point_estimates.csv` and `simulation_catalog.csv`, and writes weighted versions `data/processed/obs_weighted.csv` and `data/processed/sim_weighted.csv`. A status report `data/results/selection_bias_status.json` records `scope: "detection_space"`, the **average weight** (must lie in [0.5, 2]), and verifies that the **sum of weights** equals the effective sample size.  
  *Outputs*: `data/processed/obs_weighted.csv`, `data/processed/sim_weighted.csv`, `data/results/selection_bias_status.json`.  
  *Verification*: `pytest tests/unit/test_selection_bias.py` asserts all weights > 0, average weight within the required interval, and that `sum(weights) == number_of_rows`.

---  

## Phase 4 – Pre‑analysis power check (FR‑010/FR‑015, priority P2)

- [ ] T008 [P2] [US2c] **A‑priori MDES calculation and simulation‑size adequacy check**  
  *Implementation*: `code/src/analysis/power_check.py` reads the sample sizes from the weighted catalogs, computes the **Minimum Detectable Effect Size (MDES)** using Eq. (1) from arXiv 2309.06305 with α = 0.06, determines the required simulation size, and writes `data/results/power_check.json` containing `mdes`, `required_sim_size`, `power_limitation_flag` (true if actual simulation size < required), and a human‑readable `limitation_note`. If the flag is true, downstream analysis proceeds but the note is later included in the final report.  
  *Output*: `data/results/power_check.json`.  
  *Verification*: `pytest tests/unit/test_power_check.py` checks that the MDES value is a positive float, that the flag logic matches the size comparison, and that the JSON conforms to the `statistical_test_result.schema.yaml` sub‑object.

---  

## Phase 5 – Kernel density estimation (FR‑004, priority P2)

- [ ] T009 [P2] [US2] **Compute 1‑D KDEs for `mass_ratio` and `effective_spin` using Scott’s rule**  
  *Implementation*: `code/src/analysis/kde_compute.py` loads `obs_weighted.csv` and `sim_weighted.csv`, fits `scipy.stats.gaussian_kde` with bandwidth selected via Scott’s rule for each parameter, and pickles the KDE objects.  
  *Outputs*: `data/results/kde_mass_ratio.pkl`, `data/results/kde_effective_spin.pkl`.  
  *Verification*: `pytest tests/unit/test_kde_compute.py` loads each pickle, evaluates the density on a fine grid, and asserts that the numerical integral over the grid is ≈ 1 (tolerance 0.01).

---  

## Phase 6 – Weighted Kolmogorov‑Smirnov tests & Bonferroni correction (FR‑005/FR‑006, priority P2)

- [ ] T010 [P2] [US2] **Perform weighted two‑sample KS tests with bootstrap p‑values and apply Bonferroni correction**  
  *Implementation*: `code/src/analysis/weighted_ks.py` (1) builds weighted empirical CDFs for `mass_ratio` and `effective_spin` from the weighted CSVs; (2) computes the KS statistic for each; (3) generates 1 000 bootstrap resamples (preserving event‑wise weights) to obtain empirical p‑values; (4) applies Bonferroni adjustment across the two marginal tests (`p_adj = min(p * 2, 1)`). Results are written to `data/results/ks_results.json` conforming to `statistical_test_result.schema.yaml`.  
  *Output*: `data/results/ks_results.json`.  
  *Verification*: `pytest tests/unit/test_weighted_ks.py` checks schema compliance, that `bonferroni_adjusted_p_value` equals `min(p_value * 2, 1)`, and that `scope` matches `"detection_space"`.

---  

## Phase 7 – Sensitivity analysis on significance thresholds (FR‑009, priority P2)

- [ ] T011 [P2] [US2b] **Sweep α ∈ {0.05, 0.06} and flag borderline results**  
  *Implementation*: `code/src/analysis/sensitivity_sweep.py` reads `ks_results.json`, recomputes significance for α = 0.05 and α = 0.06, populates the `alpha_sweep_results` array, and sets `borderline_flag` to true for any parameter whose significance status flips across the two thresholds. The file is overwritten in place.  
  *Verification*: `pytest tests/unit/test_sensitivity_sweep.py` asserts that both α entries exist, that `borderline_flag` correctly reflects any flips, and that the JSON still validates against its schema.

---  

## Phase 8 – Visualization (FR‑007/FR‑008, priority P3)

- [ ] T012 [P3] [US3] **Generate KDE plots with divergence annotations and manifest**  
  *Implementation*: `code/src/viz/plot_kde.py` loads the KDE pickles, evaluates them on a dense grid, overlays observational and simulation curves for each parameter, shades regions where the **Bonferroni‑adjusted p‑value < 0.05** (as recorded in `ks_results.json`), and saves PNGs at ≥ 300 DPI. A manifest `outputs/figures/figure_manifest.json` conforming to `visualization_output.schema.yaml` records `figure_id`, `parameter_name`, `format`, `resolution_dpi`, `file_path`, and the numeric `divergence_regions`.  
  *Outputs*: `outputs/figures/mass_ratio_kde.png`, `outputs/figures/effective_spin_kde.png`, `outputs/figures/figure_manifest.json`.  
  *Verification*: `pytest tests/unit/test_plot_kde.py` checks image DPI via Pillow, file existence, and validates the manifest against its schema (including correct divergence region bounds).

---  

## Phase 9 – Reporting & handoff (US‑3, priority P3)

- [ ] T013 [P3] [US3] **Assemble the final markdown report**  
  *Implementation*: `code/src/report/final_report.py` aggregates (1) KS statistics and adjusted p‑values, (2) sensitivity‑sweep outcomes, (3) power‑analysis notes (including any `power_limitation_flag`), (4) autocorrelation verification, (5) figure embeds, and (6) a “Limitations” section that cites any power‑limitation or i.i.d. concerns. The report is written to `data/results/final_report.md`.  
  *Output*: `data/results/final_report.md`.  
  *Verification*: `pytest tests/integration/test_report_contents.py` parses the markdown, asserts presence of required sections, that numeric values match those in `ks_results.json` and `power_check.json`, and that the limitation note appears when appropriate.

---  

## Phase 10 – Reproducibility documentation & full‑pipeline test (US‑0)

- [ ] T014 [P0] [US0] **Document the reproducible workflow in `quickstart.md`**  
  *Implementation*: Update `quickstart.md` with the exact command `python -m code.src.main`, required Python version (`3.11`), fixed random seed, expected artifact locations, and the free‑tier resource limits.  
  *Verification*: `tests/unit/test_quickstart_exists.py` checks that the file exists and contains the command string.

- [ ] T015 [P0] [US0] **Run phase‑specific integration tests**  
  *Implementation*: `tests/integration/test_phase_integrations.py` runs a suite of targeted integration checks for each major phase (preprocessing, weighting, KS testing, visualization) without executing the full end‑to‑end pipeline. Each sub‑test asserts that the intermediate artifacts for its phase exist and validate against their schemas.  
  *Verification*: All sub‑tests must pass on the CI runner.

- [ ] T016 [P0] [US0] **Run full end‑to‑end pipeline integration test**  
  *Implementation*: `tests/integration/test_full_pipeline.py` executes `python -m code.src.main` in an isolated temporary directory, then asserts that all final artifacts (`obs_weighted.csv`, `sim_weighted.csv`, `ks_results.json`, `final_report.md`, both PNGs, `resource_usage.json`, etc.) exist and validate against their respective JSON‑Schema contracts; it also parses `resource_usage.json` to confirm compliance with the free‑tier limits.  
  *Verification*: `pytest -q tests/integration/test_full_pipeline.py` must pass on the CI runner.

---  

### Requirement coverage summary  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑003 | T001, T003 |
| FR‑014 (i.i.d. sample) | T003 (500 draws + hierarchical bootstrap) |
| FR‑002, FR‑007 | T005 (official releases only) |
| FR‑004, FR‑005, FR‑006 | T009, T010 |
| FR‑009 (α‑sweep) | T011 (α = 0.05, 0.06) |
| FR‑010, FR‑015 (MDES & power note) | T008 |
| FR‑011 (resource limits) | T001‑T002, T015‑T016 |
| FR‑016 (selection bias) | T007 |
| FR‑017 (autocorrelation) | T004 |
| FR‑008, FR‑012 (visualization) | T012 |
| FR‑013 (report handoff) | T013 |
| US‑0 (CI constraints) | T001‑T002, T014‑T016 |
| US‑1, US‑1b, US‑2, US‑2b, US‑2c, US‑3 | All tasks above |

All tasks remain unchecked (`[ ]`) pending implementation. The list respects the data‑flow ordering, stays within CPU‑only constraints, and fully complies with the specification, the Constitution, and the latest reviewer concerns.  

---  

## Phase 11 – Additional notes  

- The hierarchical bootstrap in T003 guarantees i.i.d. point‑estimate data while satisfying FR‑014.  
- T005 now aborts on any failure to obtain official simulation releases, ensuring strict adherence to Constitution Principle VI.  
- Sensitivity analysis in T011 is limited to the required α values, avoiding scope creep.  
- Integration testing is now split: T015 validates each phase separately, while T016 confirms the whole pipeline works end‑to‑end.  
