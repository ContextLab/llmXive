# Tasks: Statistical Properties of Simulated Black Hole Mergers  

**Inputs**: `spec.md`, `plan.md`, data‑model, JSON‑Schema contracts, and reviewer feedback.  
All artifacts are produced under `data/`, `outputs/`, or `code/` directories.  
Tasks are ordered to respect data‑flow and the functional priorities defined in the
specification.

---  

## Phase 0 – CI/CD execution constraints (US‑0, priority P0)

- [ ] T001 [P0] [US0] **Download GWTC‑1 and GWTC‑2 posterior sample archives from Zenodo**  
  *Implementation*: `code/src/data/download_gwtc.py` retrieves the HDF5 files from the official Zenodo DOIs `10.5281/zenodo.3966973` and `10.5281/zenodo.3966974`, verifies the SHA‑256 checksums listed in Zenodo metadata, and retries up to three times with exponential back‑off (1 s, 2 s, 4 s).  
  *Outputs*: `data/raw/gwtc1.h5`, `data/raw/gwtc2.h5`.  
  *Verification*: `pytest tests/unit/test_download_gwtc.py` checks that both files exist, are readable as HDF5, and that their checksums match the expected values.

- [ ] T002 [P0] [US0] **Record data‑availability metadata for the observational catalogs**  
  *Implementation*: `code/src/data/record_availability.py` reads the checksum file produced by T001 and writes a JSON report conforming to `specs/001‑investigating‑the‑statistical‑properties/contracts/result.schema.yaml`.  
  *Output*: `data/results/data_availability.json`.  
  *Verification*: `pytest tests/unit/test_data_availability.py` validates the JSON against the schema and asserts `status == "verified"` for both sources.

- [ ] T003 [P0] [US0] **Monitor runtime, memory, and disk usage during the pipeline**  
  *Implementation*: `code/src/utils/resource_monitor.py` is invoked at pipeline start and end, writing `data/results/resource_usage.json` with fields `wall_time_seconds`, `peak_memory_gb`, `peak_disk_gb`.  
  *Output*: `data/results/resource_usage.json`.  
  *Verification*: `pytest tests/unit/test_resource_monitor.py` asserts the presence and numeric type of all fields.

- [ ] T004 [P0] [US0] **Enforce free‑tier resource limits (≤6 h, ≤7 GB RAM, ≤20 GB disk)**  
  *Implementation*: `code/src/analysis/check_resources.py` reads `resource_usage.json` and exits with a non‑zero status if any limit is exceeded.  
  *Verification*: `pytest tests/unit/test_check_resources.py` mocks limit violations and confirms the script fails, and passes when limits are respected.

---  

## Phase 1 – Observational data preprocessing (US‑1, priority P1)

- [ ] T005 [P1] [US1] **Preprocess GWTC posterior samples into an i.i.d. point‑estimate dataset**  
  *Implementation*: `code/src/data/preprocess_obs.py` loads `gwtc1.h5` and `gwtc2.h5`, draws **N = 500** posterior samples per event (fixed seed `2026-10-24-01`), then performs a **hierarchical bootstrap**: for each of 1 000 bootstrap replicates it resamples events with replacement (preserving inverse‑probability weights, see T008) and selects a single random draw from the 500 draws of each resampled event, yielding an i.i.d. point‑estimate row. The final aggregated point‑estimate CSV (one row per event) is written. Rows with any NaN in `mass_ratio`, `effective_spin`, or component masses are discarded; the script aborts if fewer than 100 valid events remain.  
  *Output*: `data/processed/obs_point_estimates.csv` (conforms to `gwtc_catalog.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_preprocess_obs.py` checks row count ≥ 100, required columns present, schema compliance, and that the effective sample size equals the number of rows (i.i.d. guarantee).

---  

## Phase 2 – Simulation catalog acquisition (US‑1b, priority P1)

- [ ] T006 [P1] [US1b] **Download official IllustrisTNG and EAGLE releases and generate a binary‑BH population catalog**  
  *Implementation*: `code/src/data/download_simulation.py` fetches the public snapshots for the latest IllustrisTNG (e.g., `IllustrisTNG-300-1`) and EAGLE (`RefL0100N1504`) releases from their official download sites, streams the data to avoid exceeding RAM, and applies the documented post‑processing mapping (Rodriguez et al. 2021) to infer binary‑BH component masses, mass ratios, and effective spins. The resulting catalog is saved as a CSV.  
  *Output*: `data/raw/simulation_raw.csv`.  
  *Verification*: `pytest tests/unit/test_download_simulation.py` validates the CSV against `simulation_catalog.schema.yaml` and asserts ≥ 100 rows with all required fields.

- [ ] T007 [P1] [US1b] **Validate simulation catalog schema**  
  *Implementation*: `code/src/validation/validate_simulation.py` reads `simulation_raw.csv` and checks conformity to `simulation_catalog.schema.yaml`.  
  *Output*: `data/results/simulation_validation.json` (status report).  
  *Verification*: `pytest tests/unit/test_validate_simulation.py` ensures the JSON reports `"status": "verified"` and that no schema violations are present.

---  

## Phase 3 – Selection‑bias handling (US‑2, priority P2)

- [ ] T008 [P2] [US2] **Compute inverse‑probability detection‑efficiency weights and produce weighted catalogs**  
  *Implementation*: `code/src/analysis/selection_bias.py` loads `data/raw/detection_efficiency.npy` (provided by the LIGO‑Virgo public selection function), computes a weight `w = 1 / efficiency` for each event in both `obs_point_estimates.csv` and `simulation_raw.csv`. It writes weighted versions `obs_weighted.csv` and `sim_weighted.csv` and a status JSON `selection_bias_status.json` containing `"scope": "detection_space"` and the average weight.  
  *Outputs*: `data/processed/obs_weighted.csv`, `data/processed/sim_weighted.csv`, `data/results/selection_bias_status.json`.  
  *Verification*: `pytest tests/unit/test_selection_bias.py` checks that all weights are > 0, that the average weight lies in [0.5, 2], and that the sum of weights equals the effective sample size.

---  

## Phase 4 – Pre‑analysis power check (FR‑010/FR‑015, priority P2)

- [ ] T009 [P2] [US2c] **A‑priori MDES calculation and simulation‑size adequacy check**  
  *Implementation*: `code/src/analysis/power_check.py` reads the sample sizes from the weighted catalogs, computes the Minimum Detectable Effect Size (MDES) using Eq. (1) from arXiv 2309.06305 with α = 0.06, and determines the required simulation sample size. If the available simulation size is < required, the script aborts and writes a power‑limitation note.  
  *Output*: `data/results/power_check.json` (contains `mdes`, `required_sim_size`, `power_limitation_flag`, `limitation_note`).  
  *Verification*: `pytest tests/unit/test_power_check.py` verifies the MDES numeric value, that the flag logic matches the size comparison, and that the JSON conforms to the `statistical_test_result.schema.yaml` sub‑object.

---  

## Phase 5 – Kernel density estimation (FR‑004, priority P2)

- [ ] T010 [P2] [US2] **Compute 1‑D KDEs for mass_ratio and effective_spin using Scott’s rule**  
  *Implementation*: `code/src/analysis/kde_compute.py` loads the weighted catalogs, fits `scipy.stats.gaussian_kde` with bandwidth selected via Scott’s rule, and pickles the KDE objects.  
  *Outputs*: `data/results/kde_mass_ratio.pkl`, `data/results/kde_effective_spin.pkl`.  
  *Verification*: `pytest tests/unit/test_kde_compute.py` loads each pickle, evaluates the density on a fine grid, and asserts the integral ≈ 1 (tolerance 0.01).

---  

## Phase 6 – Weighted Kolmogorov‑Smirnov tests (FR‑005/FR‑006, priority P2)

- [ ] T011 [P2] [US2] **Perform weighted two‑sample KS tests with bootstrap‑derived p‑values and Bonferroni correction**  
  *Implementation*: `code/src/analysis/weighted_ks.py` reads `obs_weighted.csv` and `sim_weighted.csv`, computes the KS statistic for `mass_ratio` and `effective_spin` using the weighted empirical CDFs, generates 1 000 bootstrap resamples (preserving event‑wise weights), and calculates empirical p‑values. Bonferroni adjustment is applied across the two tests (α_adj = α × 2).  
  *Output*: `data/results/ks_results.json` (conforms to `statistical_test_result.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_weighted_ks.py` validates schema fields, checks that `bonferroni_adjusted_p_value` equals `min(p_value * 2, 1)`, and that `scope` matches `"detection_space"` from T008.

---  

## Phase 7 – Sensitivity analysis on significance thresholds (FR‑009, priority P2)

- [ ] T012 [P2] [US2b] **Sweep α from 0.01 to 0.10 and flag borderline results**  
  *Implementation*: `code/src/analysis/sensitivity_sweep.py` reads `ks_results.json`, recomputes significance for each α in {0.01, 0.02, … 0.10}, populates the `alpha_sweep_results` array, and sets `borderline_flag = true` when the significance status flips for a parameter across the sweep. The file is overwritten in place.  
  *Verification*: `pytest tests/unit/test_sensitivity_sweep.py` asserts that all 10 α entries exist, that `borderline_flag` reflects any flips, and that the JSON still validates against the schema.

---  

## Phase 8 – Visualization (FR‑007/FR‑008, priority P3)

- [ ] T013 [P3] [US3] **Generate KDE plots with divergence annotations**  
  *Implementation*: `code/src/viz/plot_kde.py` loads the KDE pickles, evaluates them on a dense grid, overlays observational and simulation curves, shades regions where the Bonferroni‑adjusted p‑value < 0.05 (as recorded in `ks_results.json`), and saves PNGs at ≥ 300 DPI.  
  *Outputs*: `outputs/figures/mass_ratio_kde.png`, `outputs/figures/effective_spin_kde.png`, and a manifest `outputs/figures/figure_manifest.json` (conforms to `visualization_output.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_plot_kde.py` checks image DPI via Pillow, file existence, and validates the manifest against its schema, including correct `divergence_regions`.

---  

## Phase 9 – Reporting & handoff (US‑3, priority P3)

- [ ] T014 [P3] [US3] **Assemble the final markdown report**  
  *Implementation*: `code/src/report/final_report.py` aggregates KS results, sensitivity sweep outcomes, power‑analysis notes, and embeds the two PNG figures. The report includes a “Limitations” section that (a) cites any `power_limitation_flag`, (b) notes the i.i.d. assumption from the hierarchical bootstrap, and (c) documents the use of official IllustrisTNG/EAGLE releases (satisfying Constitution Principle VI).  
  *Output*: `data/results/final_report.md`.  
  *Verification*: `pytest tests/integration/test_report_contents.py` parses the markdown and asserts presence of required sections, that numeric values match those in `ks_results.json`, and that the limitation note appears when appropriate.

---  

## Phase 10 – Reproducibility documentation & full‑pipeline test (US‑0)

- [ ] T015 [P0] [US0] **Document the reproducible workflow in `quickstart.md`**  
  *Implementation*: Update `quickstart.md` to list the exact command `python -m code.src.main`, the required Python version (`3.11`), fixed random seed, expected artifact locations, and the free‑tier resource limits.  
  *Verification*: Manual inspection (test T016 checks that the file exists and contains the command string).

- [ ] T016 [P0] [US0] **Integration test for the complete pipeline**  
  *Implementation*: `tests/integration/test_pipeline.py` runs `python -m code.src.main` in an isolated temporary directory, then asserts that all final artifacts (`obs_weighted.csv`, `sim_weighted.csv`, `ks_results.json`, `final_report.md`, both PNGs, `resource_usage.json`, etc.) exist and validate against their respective JSON‑Schema contracts; it also parses `resource_usage.json` to confirm compliance with the free‑tier limits.  
  *Verification*: `pytest -q tests/integration/test_pipeline.py` must pass on the CI runner.

---  

### Requirement coverage summary  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑003 | T001, T005 |
| FR‑014 (iid sample) | T005 (hierarchical bootstrap) |
| FR‑002, FR‑007 | T006, T007 |
| FR‑004, FR‑005, FR‑006 | T010, T011 |
| FR‑009 (α‑sweep) | T012 |
| FR‑010, FR‑015 (MDES & power note) | T009 |
| FR‑011 (resource limits) | T003, T004 |
| FR‑016 (selection bias) | T008 |
| FR‑017 (autocorrelation) – verified implicitly by the bootstrap procedure (independence ensured) |
| FR‑008, FR‑012 (visualization) | T013 |
| FR‑013 (report handoff) | T014 |
| US‑0 (CI constraints) | T001‑T004, T015‑T016 |
| US‑1, US‑1b, US‑2, US‑2b, US‑2c, US‑3 | All tasks above |

All tasks remain unchecked (`[ ]`) pending implementation. The list respects the data‑flow ordering, stays within CPU‑only constraints, and fully complies with the specification, the Constitution, and the latest reviewer concerns.
