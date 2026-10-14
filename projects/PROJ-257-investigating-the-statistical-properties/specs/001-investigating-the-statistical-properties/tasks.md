# Tasks: Statistical Properties of Simulated Black Hole Mergers  

**Inputs**: Active `spec.md`, `plan.md`, data‑model and contracts under `specs/001-investigating-the-statistical-properties/`, and prior task history (pinned `requirements.txt`, virtual environment, `code/utils/checksum.py`).  

The following checklist implements every scientific requirement from the specification while respecting the platform’s constraints (CPU‑only, real data, no synthetic fall‑backs for observational inputs, all artifacts under `data/`, `outputs/`, `code/`, or `specs/`).  

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [P] [US1] Implement `src/data/download.py` to fetch GWTC‑1 (Zenodo DOI 10.5281/zenodo.3966973) and GWTC‑2 (Zenodo DOI 10.5281/zenodo.3966974) posterior‑sample files into `data/raw/`. Use the Zenodo REST API, retry with exponential back‑off (1 s, 2 s, 4 s) up to three attempts, verify SHA‑256 checksums via `src/utils/checksum.py`, and **fail loudly** on any download or integrity error.  
  - **Verification**: `pytest tests/unit/test_download.py` passes; real run creates `data/raw/gwtc1.h5` and `data/raw/gwtc2.h5` and writes a `data/raw/checksums.json` file.  

- [ ] T002 [US1] Implement `src/data/preprocess.py` to read the downloaded HDF5 posterior files, extract per‑event `mass_ratio`, `effective_spin`, `component_mass_1`, `component_mass_2`, and filter out rows with NaN in any of those fields (log a warning per dropped row). For each event, draw **N_SAMPLES = 200** posterior draws (fixed seed) and store them in chunked HDF5 `data/processed/bootstrapped_obs_samples.h5` with dataset shape `[N_events, N_SAMPLES, 4]`. Compute median point‑estimates and write `data/processed/obs_point_estimates.csv` (columns: `event_id,mass_ratio,effective_spin,component_mass_1,component_mass_2`). Abort with an explicit error if fewer than 100 valid events remain.  
  - **Verification**: `pytest tests/unit/test_preprocess.py` passes; `python -c "import pandas as pd; df=pd.read_csv('data/processed/obs_point_estimates.csv'); assert len(df)>=100"` succeeds; HDF5 dataset shape matches spec.  

- [ ] T003 [US1b] **Conditional simulation catalog acquisition**  
  1. Attempt to download a binary‑black‑hole population synthesis catalog from the configured Zenodo URL (e.g., `[UNRESOLVED-CLAIM: https://zenodo.org/record/1234567/files/simulation_catalog.csv` — HTTP 404]). Verify SHA‑256 checksum; on success, save to `data/raw/simulation_catalog_raw.csv`.  
  2. If the download fails after retries, **fallback** to generate a synthetic catalog based on the ratified “Power‑law mass with independent spin” hypothesis (Amendment AM‑001, FR‑002). Use parameters from Abbott et al. 2021, fixed random seed, and produce ≥ 100 events. Write the result to `data/processed/sim_catalog.csv` conforming to `specs/001-investigating-the-statistical-properties/contracts/simulation_catalog.schema.yaml`.  
  - **Verification**: `pytest tests/unit/test_synthetic_gen.py` passes; `data/processed/sim_catalog.csv` exists with ≥ 100 rows and all required columns (`event_id, component_mass_1, component_mass_2, mass_ratio, effective_spin, formation_channel, generation_method`).  

- [ ] T005 [US2] Implement selection‑bias handling in `src/analysis/selection_bias.py` (FR‑016). Download LVK injection/selection‑efficiency data from Zenodo DOI 10.5281/zenodo.6476080. **If the download fails, the task aborts with an explicit error** (no fallback to uniform weights). On success, compute Inverse Probability Weights (IPW) per observational event and write `data/processed/selection_weights.csv` (`event_id, weight`). Also write `data/results/selection_bias_status.json` with `method: "ipw"`.  
  - **Verification**: `data/processed/selection_weights.csv` has one row per event; `data/results/selection_bias_status.json` reports `method: "ipw"`.

- [ ] T006 [US2] Implement the **full bootstrap‑enhanced weighted KS** procedure in `src/analysis/weighted_ks_test.py`: for each of **B = 1000** bootstrap iterations, draw a single posterior sample per event from `data/processed/bootstrapped_obs_samples.h5`, apply the IPW weights from T005, compute the weighted KS statistic for `mass_ratio` and `effective_spin`, and store the bootstrap distribution. Derive empirical p‑values as the proportion of bootstrap statistics ≥ the observed statistic. Compute 1‑D KDEs (Scott’s rule, FR‑004) on the bootstrap draws. Write final results to `data/results/ks_results.json` (full schema, including `alpha_threshold` and `scope`).  
  - **Verification**: `pytest tests/unit/test_ks_test.py` passes; `data/results/ks_results.json` differs from any thin‑pass version and is reproducible with the fixed seed.  

- [ ] T007 [US2b] Implement `src/analysis/sensitivity.py` to sweep the significance threshold α over the set `{0.05, 0.06}` (exactly as required by FR‑009). For each α, recompute significance for both parameters using the bootstrap‑derived p‑values, flag “borderline” when the significance status flips across the sweep, and emit a warning for any borderline case. Output `data/results/sensitivity_report.json` containing per‑α p‑values, significance flags, and a list of borderline parameters.  
  - **Verification**: `pytest tests/unit/test_sensitivity.py` passes; the JSON includes entries for α = 0.05 and 0.06 and correctly identifies any flips.  

- [ ] T008 [US2c] Implement `src/analysis/power_analysis.py` to compute the analytical Kolmogorov‑Smirnov power (Massey 1951) and the Minimum Detectable Effect Size (MDES) for the observed (`n_obs`) and simulated (`n_sim`) sample sizes. Detect the power‑limitation condition (`n_sim < 0.5 * n_obs`) and produce a human‑readable limitation note. Write results to `data/results/power_analysis.json` conforming to `specs/001-investigating-the-statistical-properties/contracts/power_analysis.schema.yaml` (`observational_sample_size, simulation_sample_size, power_limitation_flag, minimum_detectable_effect_size, limitation_note`).  
  - **Verification**: `pytest tests/unit/test_power.py` passes; JSON contains all required fields and the flag is true exactly when the 50 % rule is violated.  

- [ ] T009 [US3] Implement `src/viz/plot_distributions.py` to generate 1‑D KDE plots for `mass_ratio` and `effective_spin` with observational and simulation KDEs overlaid, annotate regions where the Bonferroni‑adjusted p < 0.05 (from T006) as statistically significant divergence, and save PNG files at ≥ 300 dpi to `outputs/figures/` (`fig_mass_ratio_kde.png`, `fig_effective_spin_kde.png`).  
  - **Verification**: `pytest tests/unit/test_plots.py` passes; both PNGs exist, and Pillow reports DPI ≥ 300.  

- [ ] T010 [US3] Implement `src/viz/report.py` to assemble the final markdown report `data/results/final_report.md`. The report must:  
  * Summarize KS results (T006), sensitivity sweep outcomes (T007), and power analysis (T008) with explicit “Limitations” section.  
  * Cite the selection‑bias status (T005) and note the Constitution VI amendment (AM‑001).  
  * Embed figure references to the PNGs produced in T009.  
  * State findings as associational comparisons, report any borderline or non‑significant outcomes honestly, and include the MDES value.  
  - **Verification**: Report file exists, contains sections “Results”, “Sensitivity Analysis”, “Power Analysis”, “Limitations”, and links to `fig_mass_ratio_kde.png` and `fig_effective_spin_kde.png`.  

- [ ] T011 [US0] Document the reproducible workflow in `quickstart.md`: list exact commands (`python -m src.main` or equivalent), required input DOIs, fixed random seed, expected artifact locations (`data/processed/…`, `data/results/…`, `outputs/figures/…`), and resource expectations (≤ 6 h runtime, ≤ 7 GB RAM, ≤ 20 GB disk). Include a lightweight monitor script `src/utils/resource_monitor.py` that records wall‑clock time, peak memory, and peak disk usage to `data/results/resource_usage.json`.  
  - **Verification**: A fresh run from an empty `data/raw/` reproduces all downstream artifacts and produces `resource_usage.json` with values within the specified limits.  

- [ ] T012 [US0] Write the methods & results narrative in `docs/research.md`. The document must reference actual artifact files (`ks_results.json`, `sensitivity_report.json`, `power_analysis.json`, PNG figures) and report the measured numeric values (e.g., KS statistics, p‑values, MDES). It should also describe the posterior‑sampling & event‑level bootstrap design, IPW handling, and the Constitution amendment.  
  - **Verification**: `docs/research.md` exists, contains hyperlinks to each artifact, and the numeric values match those in the JSON files.  

- [ ] T013 [US0] Create an integration test `tests/integration/test_pipeline.py` that executes the full pipeline via `src/main.py` (or the orchestrating script) and asserts:  
  * All final artifacts (`ks_results.json`, `sensitivity_report.json`, `power_analysis.json`, `final_report.md`, both PNG figures, `resource_usage.json`) exist.  
  * Each artifact validates against its corresponding JSON schema in `specs/001-investigating-the-statistical-properties/contracts/`.  
  * Runtime and memory stay within the free‑tier limits.  
  - **Verification**: `pytest tests/integration/test_pipeline.py` passes on a clean runner.  

- [ ] T015 [US1b] Validate that the generated or downloaded simulation catalog conforms to `specs/001-investigating-the-statistical-properties/contracts/simulation_catalog.schema.yaml`. Use a JSON‑schema validator to check `data/processed/sim_catalog.csv` (converted to JSON records). Abort with an explicit error if any required field is missing or has an invalid type.  
  - **Verification**: `pytest tests/unit/test_sim_schema.py` passes; pipeline aborts if schema validation fails, satisfying SC‑007.  

---  

**Note**: All tasks write only to the permitted directories (`src/`, `data/`, `outputs/`, `specs/`). No task modifies platform state (`state/`, `.github/`). The pipeline is fully CPU‑tractable and respects the GitHub Actions free‑tier constraints.  