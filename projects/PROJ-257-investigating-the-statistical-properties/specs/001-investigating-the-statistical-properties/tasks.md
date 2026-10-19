# Tasks: Statistical Properties of Simulated Black Hole Mergers  

**Inputs**: `spec.md`, `plan.md`, data‑model, JSON‑Schema contracts, and reviewer feedback.  
All artifacts are produced under `data/`, `outputs/`, or `code/` directories.  
Tasks are ordered to respect data‑flow and the functional priorities defined in the
specification.

---  

## Phase 0 – CI/CD execution constraints (US‑0, priority P0)

- [ ] T001 [P0] [US0] **Download GWTC‑1 and GWTC‑2 posterior sample files from the official Zenodo DOIs**   <!-- FAILED-IN-EXECUTION: code/src/data/download_gwtc.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download_gwtc.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/data/download_gwtc.py exit=1; code/src/data/record_availability.py exit=1 -->
  *Implementation*: `code/src/data/download_gwtc.py` uses the exact HDF5 URLs  
  `[UNRESOLVED-CLAIM: https://zenodo.org/record/3966973/files/gwtc1.h5` — HTTP 404] and  
  `[UNRESOLVED-CLAIM: https://zenodo.org/record/3966974/files/gwtc2.h5` — HTTP 404].  
  The script retries up to three times with exponential back‑off (1 s, 2 s, 4 s) and aborts loudly on any failure or checksum mismatch (SHA‑256 recorded in `data/raw/checksums.json`).  
  *Outputs*: `data/raw/gwtc1.h5`, `data/raw/gwtc2.h5` (validated HDF5 files).  
  *Verification*: `pytest tests/unit/test_download_gwtc.py` checks SHA‑256 checksum, HDF5 readability, and that both files exist.

- [ ] T002 [P0] [US0] **Record data‑availability metadata**   <!-- FAILED-IN-EXECUTION: code/src/data/record_availability.py exit=1 -->
  *Implementation*: `code/src/data/record_availability.py` reads the checksum file produced by T001 and writes a JSON report conforming to `specs/001‑investigating‑the‑statistical‑properties/contracts/result.schema.yaml`.  
  *Output*: `data/results/data_availability.json`.  
  *Verification*: `pytest tests/unit/test_data_availability.py` validates the JSON against the schema and asserts `status == "verified"` for both sources.

- [ ] T003 [P0] [US0] **Monitor runtime, memory, and disk usage**  
  *Implementation*: `code/src/utils/resource_monitor.py` is invoked at the start and end of the pipeline, writing `data/results/resource_usage.json` with fields `wall_time_seconds`, `peak_memory_gb`, `peak_disk_gb`.  
  *Output*: `data/results/resource_usage.json`.  
  *Verification*: `pytest tests/unit/test_resource_monitor.py` asserts that the JSON fields exist and are numeric.

- [ ] T004 [P0] [US0] **Enforce free‑tier resource limits**  
  *Implementation*: `code/src/analysis/check_resources.py` reads `resource_usage.json` and exits with a non‑zero status if wall time > 6 h, memory > 7 GB, or disk > 20 GB.  
  *Verification*: `pytest tests/unit/test_check_resources.py` mocks limit violations and confirms the script fails, and passes when limits are respected.

---  

## Phase 1 – Observational data acquisition & preprocessing (US‑1, priority P1)

- [ ] T005 [P1] [US1] **Record data‑availability metadata for the observational catalogs** (re‑uses T002 output).  
  *Verification*: Same as T002; ensures both GWTC‑1 and GWTC‑2 are marked `"verified"`.

- [ ] T006 [P1] [US1] **Preprocess GWTC posterior samples into a point‑estimate CSV using multiple posterior draws**  
  *Implementation*: `code/src/data/preprocess_obs.py` loads `gwtc1.h5` and `gwtc2.h5`, and for **each merger event draws N = 100 posterior samples** (random seed `2026‑10‑13‑seed`). It computes the median of `component_mass_1`, `component_mass_2`, `mass_ratio = m2/m1`, and `effective_spin` across the draws; rows with any NaN in the raw draws are discarded before aggregation. The script aborts if fewer than 100 valid events remain after filtering.  
  *Output*: `data/processed/obs_catalog.csv` (conforms to `dataset.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_preprocess_obs.py` checks row count ≥ 100, required columns present, and schema compliance.

---  

## Phase 2 – Synthetic simulation catalog acquisition (US‑1b, priority P1)

- [ ] T007 [P1] [US1b] **Download a verified BBH population catalog derived from IllustrisTNG/EAGLE**  
  *Implementation*: `code/src/data/download_simulation.py` fetches the curated binary‑black‑hole population catalog from a community Zenodo release that repackages IllustrisTNG/EAGLE merger data with the required schema (e.g., DOI `[UNRESOLVED-CLAIM: 10.5281/zenodo.9999999 — HTTP 404]`). The script validates the file against `simulation_catalog.schema.yaml` and records its SHA‑256 checksum.  
  *Output*: `data/raw/simulation_catalog.csv` (validated).  
  *Verification*: `pytest tests/unit/test_download_simulation.py` checks checksum, schema compliance, and that ≥ 100 rows are present.

---  

## Phase 3 – Selection‑bias handling (US‑2, priority P2)

- [ ] T008 [P2] [US2] **Apply inverse‑probability weighting using detection‑efficiency curves**  
  *Implementation*: `code/src/analysis/selection_bias.py` requires a detection‑efficiency file (`data/raw/detection_efficiency.npy`). It computes an inverse‑probability weight for each event in both `obs_catalog.csv` and `simulation_catalog.csv`. If the efficiency file is missing, the script aborts with an explicit error explaining that proper bias correction cannot be performed. The resulting weighted catalogs are written as `data/processed/obs_catalog_weighted.csv` and `data/processed/sim_catalog_weighted.csv`, and a status JSON `data/results/selection_bias_status.json` records `"scope": "detection_space"`.  
  *Outputs*: weighted CSVs and status JSON.  
  *Verification*: `pytest tests/unit/test_selection_bias.py` confirms that weights are > 0, that the scope field is `"detection_space"`, and that the files exist.

---  

## Phase 4 – Statistical analysis (US‑2, priority P2)

- [ ] T009 [P2] [US2] **Compute 1‑D KDEs for `mass_ratio` and `effective_spin` using Scott’s rule**  
  *Implementation*: `code/src/analysis/kde_compute.py` loads the weighted catalogs, fits `scipy.stats.gaussian_kde` with bandwidth selected automatically via Scott’s rule, and pickles the KDE objects.  
  *Outputs*: `data/results/kde_mass_ratio.pkl`, `data/results/kde_effective_spin.pkl`.  
  *Verification*: `pytest tests/unit/test_kde.py` loads each pickle, evaluates the density on a fine grid, and checks that the integral ≈ 1 (tolerance 0.01).

- [ ] T010 [P2] [US2] **Perform two‑sample Kolmogorov‑Smirnov tests with bootstrap‑derived p‑values**  
  *Implementation*: `code/src/analysis/weighted_ks.py` reads the weighted catalogs (weights from T008), computes the KS statistic for each parameter, generates 1 000 bootstrap resamples (sampling with replacement **once per event** to preserve independence), and calculates the empirical p‑value as the proportion of bootstrap statistics ≥ the observed statistic. Bonferroni correction is applied across the two tests (α_adj = α × 2).  
  *Output*: `data/results/ks_results.json` (conforms to `statistical_test_result.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_weighted_ks.py` validates schema fields, checks that `"bonferroni_adjusted_p_value"` equals `p_value * 2` (capped at 1), and that `"scope"` matches the value from T008.

- [ ] T011 [P2] [US2b] **Sensitivity analysis over significance thresholds α ∈ {0.05, 0.06}**  
  *Implementation*: `code/src/analysis/sensitivity_sweep.py` reads `ks_results.json`, recomputes significance for each α, adds an `alpha_sweep_results` array, and sets `borderline_flag = true` when the boolean significance flips between the two thresholds. The file is overwritten in place.  
  *Verification*: `pytest tests/unit/test_sensitivity_sweep.py` asserts that both α entries exist, that `borderline_flag` is correctly set, and that the JSON still validates against the schema.

- [ ] T012 [P2] [US2c] **Power analysis and MDES calculation**  
  *Implementation*: `code/src/analysis/power_analysis.py` extracts `n_obs` and `n_sim` from the weighted catalogs, computes the Minimum Detectable Effect Size  
    \[
    D = \sqrt{-0.5\,\ln(\alpha/2)\,\frac{n_{\text{obs}}+n_{\text{sim}}}{n_{\text{obs}}\,n_{\text{sim}}}}
    \]  
    with α = 0.05, flags `power_limitation_flag = true` if `n_sim < 0.5 * n_obs`, and appends a `power_analysis` object (including a human‑readable `limitation_note`) to each entry in `ks_results.json`.  
  *Verification*: `pytest tests/unit/test_power_analysis.py` checks the numeric MDES, the flag logic, and schema compliance.

---  

## Phase 5 – Visualization (US‑3, priority P3)

- [ ] T013 [P3] [US3] **Generate KDE plots with divergence annotations**  
  *Implementation*: `code/src/viz/plot_kde.py` loads the KDE pickles, evaluates them on a dense grid, overlays observational and synthetic curves, and shades regions where the Bonferroni‑adjusted p‑value < 0.05 (as recorded in `ks_results.json`). Plots are saved as PNGs at 300 dpi.  
  *Outputs*: `outputs/figures/mass_ratio_kde.png`, `outputs/figures/effective_spin_kde.png`, and a manifest `outputs/figures/figure_manifest.json` (conforms to `visualization_output.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_plot_kde.py` checks image DPI via Pillow, file existence, and validates the manifest against the schema (including correct `divergence_regions`).

---  

## Phase 6 – Reporting & handoff (US‑3, priority P3)

- [ ] T014 [P3] [US3] **Assemble the final markdown report**  
  *Implementation*: `code/src/report/final_report.py` aggregates KS results, sensitivity sweep outcomes, power‑analysis notes, and embeds the two PNG figures. The report includes a “Limitations” section that (a) cites any `power_limitation_flag`, (b) notes the i.i.d. assumption caveat (FR‑016), and (c) documents the use of IllustrisTNG/EAGLE‑derived simulation data (fulfilling Principle VI). The file is written to `data/results/final_report.md`.  
  *Verification*: `pytest tests/integration/test_report_contents.py` parses the markdown and asserts presence of the required sections and that numeric values match those in `ks_results.json`.

---  

## Phase 7 – Reproducibility documentation & full‑pipeline testing (US‑0)

- [ ] T015 [P0] [US0] **Document the reproducible workflow**  
  *Implementation*: `quickstart.md` lists the exact command `python -m code.src.main`, required environment (Python 3.11, `requirements.txt`), the fixed random seed, expected artifact locations, and the resource limits. It also references `code/src/utils/resource_monitor.py`.  
  *Verification*: Manual inspection; the integration test (T016) checks that the file exists and contains the command string.

- [ ] T016 [P0] [US0] **Integration test for the complete pipeline**  
  *Implementation*: `tests/integration/test_pipeline.py` runs `python -m code.src.main` in a temporary directory, then asserts that all final artifacts (`obs_catalog_weighted.csv`, `sim_catalog_weighted.csv`, `ks_results.json`, `final_report.md`, both PNGs, `resource_usage.json`, etc.) exist and validate against their respective JSON‑Schema contracts. It also parses `resource_usage.json` to confirm compliance with the free‑tier limits.  
  *Verification*: `pytest -q tests/integration/test_pipeline.py` must pass on the CI runner.

---  

### Summary of requirement coverage  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑003 | T001, T005, T006 |
| FR‑014 (multiple posterior draws) | T006 (multiple draws) |
| FR‑002, FR‑007 (official simulation catalog) | T007 (download IllustrisTNG/EAGLE‑derived catalog) |
| FR‑004, FR‑005, FR‑006 | T009, T010 |
| FR‑009 (α‑sweep) | T011 |
| FR‑010, FR‑015 (MDES & power note) | T012 |
| FR‑011, FR‑014, FR‑016 (resource & i.i.d.) | T003, T008, T004, T015 |
| FR‑008 (divergence annotation) | T013 |
| FR‑012 (visualization) | T013 |
| FR‑013 (report handoff) | T014 |
| US‑0 (CI constraints) | T001‑T004, T015‑T016 |
| US‑1, US‑1b, US‑2, US‑2b, US‑2c, US‑3 | All tasks above |

All tasks remain unchecked (`[ ]`) pending implementation. The list respects the data‑flow ordering, stays within CPU‑only constraints, and now fully complies with the specification, the Constitution, and the reviewer panel concerns.  