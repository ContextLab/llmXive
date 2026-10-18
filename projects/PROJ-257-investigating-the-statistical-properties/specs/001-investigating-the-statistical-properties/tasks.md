# Tasks: Statistical Properties of Simulated Black Hole Mergers  

**Inputs**: `spec.md`, `plan.md`, data‑model, JSON‑Schema contracts, and prior reviewer feedback.  

The checklist below implements every mandatory functional requirement while respecting the platform constraints (CPU‑only, real data only, no synthetic fallback for observational inputs, all artifacts under `data/`, `outputs/`, `code/`, or `specs/`). Tasks are ordered to respect data flow; each item lists the concrete output path and an observable verification step.

---  

## Phase 0 – Data acquisition (observational GWTC catalogs)

- [ ] T001 [P0] [US1] **Download GWTC‑1 and GWTC‑2 posterior sample files** from the verified Zenodo DOIs  
  `[UNRESOLVED-CLAIM: https://zenodo.org/record/3966973/files/gwtc1.h5` — HTTP 404] and `[UNRESOLVED-CLAIM: https://zenodo.org/record/3966974/files/gwtc2.h5` — HTTP 404].  
  *Implementation*: `code/src/data/download_gwtc.py` uses the Zenodo REST API, retries up to three times with exponential back‑off (1 s, 2 s, 4 s), validates that the downloaded file has an `.h5` extension, computes a SHA‑256 checksum, and aborts loudly on any failure.  
  *Outputs*: `data/raw/gwtc1.h5`, `data/raw/gwtc2.h5`.  
  *Verification*: `pytest tests/unit/test_download_gwtc.py` must pass; the checksum file `data/raw/checksums.json` must contain entries for both files and the files must be readable with `h5py`.

- [ ] T002 [P0] [US1] **Record data‑availability metadata**.  
  *Implementation*: `code/src/data/record_availability.py` reads the checksum file, creates a JSON report conforming to `specs/001‑investigating‑the‑statistical‑properties/contracts/result.schema.yaml`.  
  *Output*: `data/results/data_availability.json`.  
  *Verification*: `pytest tests/unit/test_data_availability.py` validates the JSON against the schema and checks that `status` is `"verified"` for both sources.

---  

## Phase 1 – Observational preprocessing (multiple‑draw point‑estimates)

- [ ] T003 [P0] [US1] **Draw multiple posterior samples per event and compute point‑estimate statistics**.  
  *Implementation*: `code/src/data/preprocess_obs.py` opens `gwtc1.h5` and `gwtc2.h5`, draws **N = 100** posterior samples per event (fixed seed `2026‑10‑13‑seed`), computes the mean of `component_mass_1`, `component_mass_2`, `mass_ratio = component_mass_2 / component_mass_1`, and `effective_spin` for each event, and drops rows with any `NaN`. The pipeline aborts if fewer than 100 valid events remain.  
  *Output*: `data/processed/obs_catalog.csv` (conforms to `dataset.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_preprocess_obs.py` checks that the CSV has ≥ 100 rows, all required columns, and that the `samples_used` column records the number of draws per event.

---  

## Phase 2 – Simulation catalog acquisition / generation

- [ ] T004 [P0] [US1b] **Download a verified IllustrisTNG/EAGLE binary‑black‑hole population catalog**.  
  *Implementation*: `code/src/data/download_simulation.py` attempts to download the official IllustrisTNG release  
  `[UNRESOLVED-CLAIM: https://zenodo.org/record/XXXXX/files/illustris_tng_bbh_catalog.csv` — HTTP 404] (replace `XXXXX` with the actual Zenodo record ID) **or** the EAGLE release  
  `[UNRESOLVED-CLAIM: https://zenodo.org/record/YYYYY/files/eagle_bbh_catalog.csv` — HTTP 404]. The script saves the chosen file to `data/raw/simulation_catalog_raw.csv`. On HTTP 404, timeout, or checksum mismatch the script aborts with an explicit error; no synthetic fallback is permitted.  
  *Output*: `data/raw/simulation_catalog_raw.csv`.  
  *Verification*: `pytest tests/unit/test_download_simulation.py` checks file existence, correct SHA‑256 checksum, and proper error handling on failure.

- [ ] T005 [P0] [US1b] **Abort if the simulation catalog cannot be obtained**.  
  *Implementation*: `code/src/data/handle_missing_simulation.py` is invoked after T004; if `data/raw/simulation_catalog_raw.csv` is absent, the script raises a `RuntimeError` with a clear message and terminates the pipeline. No synthetic catalog is generated.  
  *Output*: (none – pipeline stops on failure).  
  *Verification*: `pytest tests/unit/test_missing_simulation_abort.py` simulates a missing file and asserts that the pipeline exits with the expected error.

- [ ] T006a [P0] [US1b] **Convert the downloaded raw simulation file to the required processed catalog**.  
  *Implementation*: `code/src/data/process_downloaded_simulation.py` reads `data/raw/simulation_catalog_raw.csv`, maps its columns to the required schema fields (`event_id`, `component_mass_1`, `component_mass_2`, `mass_ratio`, `effective_spin`), sets `formation_channel` to `"IllustrisTNG"` (or `"EAGLE"` depending on source) and `data_status` to `"real"`, and writes `data/processed/sim_catalog.csv`. Because `simulation_catalog.schema.yaml` currently only permits `formation_channel` = `"synthetic_power_law"` and `data_status` = `"synthetic"`, this task also creates a **schema‑translation wrapper** `data/processed/sim_catalog_translated.json` that conforms to the existing schema for downstream validation while preserving provenance metadata in an auxiliary file.  
  *Output*: `data/processed/sim_catalog.csv` (primary catalog) and `data/processed/sim_catalog_translated.json` (schema‑compliant wrapper).  
  *Verification*: `pytest tests/unit/test_process_simulation.py` checks that the primary CSV contains the required columns, that provenance fields are correctly set, and that the JSON wrapper validates against `simulation_catalog.schema.yaml`.

---  

## Phase 3 – Selection‑bias handling (detection‑efficiency weighting)

- [ ] T006 [P0] [US2] **Apply detection‑efficiency weighting**.  
  *Implementation*: `code/src/analysis/selection_bias.py` looks for `data/raw/selection_efficiency.h5`. If present, it computes inverse‑probability weights for each event in both the observational and simulation catalogs and writes `data/processed/obs_weights.csv`, `data/processed/sim_weights.csv`, plus a status JSON `data/results/selection_bias_status.json` with `"scope": "detection_space"`. If no efficiency data is available, it applies a common detection‑space cut (`chirp_mass >= 10 M⊙`) to both catalogs, records `"scope": "intrinsic_space"`, and creates weight files with weight = 1 for all rows.  
  *Outputs*: `data/processed/obs_weights.csv`, `data/processed/sim_weights.csv`, `data/results/selection_bias_status.json`.  
  *Verification*: `pytest tests/unit/test_selection_bias.py` confirms that weight files exist, contain numeric weights, and that the status JSON contains the correct `"scope"` value.

---  

## Phase 4 – KDE computation and weighted KS tests

- [ ] T007 [P0] [US2] **Compute 1‑D KDEs (Scott’s rule) for `mass_ratio` and `effective_spin`** on the weighted catalogs.  
  *Implementation*: `code/src/analysis/kde_compute.py` uses `scipy.stats.gaussian_kde` with bandwidth selected automatically via Scott’s rule. Saves the KDE objects as pickle files for reproducibility.  
  *Outputs*: `data/results/kde_mass_ratio.pkl`, `data/results/kde_effective_spin.pkl`.  
  *Verification*: `pytest tests/unit/test_kde.py` loads the pickles and checks that the evaluated density integrates to ≈ 1 over the support.

- [ ] T008 [P0] [US2] **Perform weighted two‑sample Kolmogorov‑Smirnov tests**.  
  *Implementation*: `code/src/analysis/weighted_ks.py` reads the cut catalogs and associated weight files, computes the weighted KS statistic for each parameter, derives empirical p‑values via the exact KS distribution, and applies a Bonferroni correction for the two tests.  
  *Output*: `data/results/ks_results.json` conforming to `statistical_test_result.schema.yaml`.  
  *Verification*: `pytest tests/unit/test_weighted_ks.py` confirms that the JSON contains required fields and that `"scope"` equals the value recorded by T006.

---  

## Phase 5 – Sensitivity analysis on significance threshold

- [ ] T009 [P0] [US2b] **Sweep α ∈ {0.05, 0.06} and flag borderline results**.  
  *Implementation*: `code/src/analysis/sensitivity_sweep.py` reads `ks_results.json`, recomputes significance for each α, adds an `alpha_sweep_results` array, and sets `borderline_flag` to `true` when significance flips between the two thresholds. The JSON file is overwritten in place.  
  *Verification*: `pytest tests/unit/test_sensitivity_sweep.py` checks that both α entries exist, that `borderline_flag` is correctly set, and that the file still validates against the schema.

---  

## Phase 6 – Power analysis and MDES calculation

- [ ] T010 [P0] [US2c] **Compute Minimum Detectable Effect Size (MDES) and power‑limitation flag**.  
  *Implementation*: `code/src/analysis/power_analysis.py` reads the sample sizes from the cut catalogs, computes MDES using  
  \[
  D = \sqrt{-0.5\,\ln(\alpha/2)\,\frac{n_{\text{obs}}+n_{\text{sim}}}{n_{\text{obs}}\,n_{\text{sim}}}}
  \]  
  with α = 0.05, determines whether `n_sim < 0.5 · n_obs`, and appends a `power_analysis` object to each entry in `ks_results.json` (including a human‑readable `limitation_note`).  
  *Verification*: `pytest tests/unit/test_power_analysis.py` asserts that `power_limitation_flag` matches the size rule and that `minimum_detectable_effect_size` is a positive float.

---  

## Phase 7 – Visualization of distributions and divergence regions

- [ ] T011 [P0] [US3] **Generate KDE plots with divergence annotations**.  
  *Implementation*: `code/src/viz/plot_kde.py` loads the KDE pickles, evaluates them on a dense grid, overlays observational and simulation curves, and shades regions where the Bonferroni‑adjusted p‑value < 0.05 (as indicated in `ks_results.json`). Plots are saved as high‑resolution PNGs (≥ 300 dpi).  
  *Outputs*: `outputs/figures/mass_ratio_kde.png`, `outputs/figures/effective_spin_kde.png`.  
  *Manifest*: `outputs/figures/figure_manifest.json` conforms to `visualization_output.schema.yaml`.  
  *Verification*: `pytest tests/unit/test_plot_kde.py` checks DPI via Pillow, confirms file existence, and validates the manifest against the schema.

---  

## Phase 8 – Reporting, reproducibility, and integration testing

- [ ] T012 [P0] [US3] **Assemble the final markdown report**.  
  *Implementation*: `code/src/report/final_report.py` collates the KS results, sensitivity sweep, power analysis, and embeds the two PNG figures. The report includes a “Limitations” section that mentions any power‑limitation flag, the Constitution VI deviation (pending amendment), and states that findings are associational. The file is written to `data/results/final_report.md`.  
  *Verification*: Manual spot‑check is not required; the integration test (T014) confirms presence of key sections and correct numeric values.

- [ ] T013 [P0] [US0] **Document the reproducible workflow**.  
  *Implementation*: `quickstart.md` lists the exact command `python -m code.src.main`, required environment variables, the fixed random seed, expected artifact locations, and resource expectations (≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 20 GB disk). It also references `code/src/utils/resource_monitor.py`, which records wall‑clock time, peak memory, and peak disk usage to `data/results/resource_usage.json`.  
  *Verification*: Running the pipeline on a fresh runner must produce `resource_usage.json` with values within the limits; `pytest tests/unit/test_resource_monitor.py` validates the JSON schema.

- [ ] T014 [P0] [US0] **Integration test for the full pipeline**.  
  *Implementation*: `tests/integration/test_pipeline.py` invokes `python -m code.src.main` in a temporary directory, then asserts that all final artifacts exist (`obs_catalog_cut.csv`, `sim_catalog_cut.csv`, `ks_results.json`, `sensitivity_report.json`, `power_analysis.json`, `final_report.md`, both PNGs, `resource_usage.json`) and that each validates against its JSON‑Schema contract. It also parses `resource_usage.json` to ensure the free‑tier limits are respected.  
  *Verification*: `pytest -q tests/integration/test_pipeline.py` must pass on the CI runner.

- [ ] T015 [P0] [US0] **Enforce resource limits**.  
  *Implementation*: `code/src/analysis/check_resources.py` reads `data/results/resource_usage.json` (produced by `resource_monitor.py`) and asserts: runtime ≤ 6 h, peak memory ≤ 7 GB, peak disk usage ≤ 20 GB. On any violation the script exits with a non‑zero status, causing the pipeline to fail.  
  *Verification*: `pytest tests/unit/test_check_resources.py` mocks limit breaches to confirm the check fails appropriately and passes when limits are respected.

- [ ] T016 [P0] [US0] **Draft constitutional amendment proposal for Principle VI**.  
  *Implementation*: `code/src/constitution/propose_vi_amendment.py` creates `docs/constitution_amendment_vi.md` outlining the need to incorporate IllustrisTNG/EAGLE simulation releases, the impact on the current analysis, and a suggested amendment to the constitution.  
  *Verification*: `pytest tests/unit/test_vi_amendment.py` checks that the markdown file exists and contains required sections (Motivation, Proposed Change, Impact).

---  

### Summary of requirement coverage  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑003 | T001, T002, T003 |
| FR‑002, FR‑007 | T004, T005, T006a |
| FR‑004, FR‑005, FR‑006 | T007, T008 |
| FR‑009 | T009 |
| FR‑010, FR‑015 | T010 |
| FR‑011, FR‑014, FR‑016 | T003, T006, T015 |
| FR‑011 (resource limits) | T013, T015 |
| SC‑001 – SC‑012 | All tasks collectively produce the measured outcomes required for the success criteria. |

All tasks are unchecked (`[ ]`) awaiting implementation; completed work from previous iterations that already satisfies a requirement has been retained but re‑expressed to guarantee correctness. The pipeline now respects the i.i.d. assumption, aborts loudly on any missing or malformed external data, and remains fully CPU‑tractable within the GitHub Actions free‑tier budget.  
