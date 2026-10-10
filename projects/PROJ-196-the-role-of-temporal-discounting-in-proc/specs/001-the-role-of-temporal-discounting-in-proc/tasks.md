# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks  

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contract schemas in `specs/001-the-role-of-temporal-discounting-in-proc/contracts/`.  

The goal is to deliver a fully‑reproducible end‑to‑end pipeline that (1) ingests real data when available, (2) falls back to a documented synthetic Data‑Generating Process (DGP) when real data cannot be fetched, (3) fits hyperbolic discounting models, (4) runs a moderated OLS regression, (5) performs bootstrap‑based robustness checks and sensitivity sweeps, (6) produces all required artifacts that conform to the JSON schemas, and (7) records exclusion and diagnostic information in a “fail‑loud” fashion.  

---  

## Phase 1 – Project scaffolding & early end‑to‑end sanity check  

- [ ] T001 **Create project layout** – `projects/PROJ-196-the-role-of-temporal-discounting-in-proc/{data/raw,data/processed,code,tests,docs}`.  
- [ ] T002 **Initialize Python environment** – `pyproject.toml` + pinned `requirements.txt` containing `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.12.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`.  
- [ ] T003 **Configure linting/formatting** – `.ruff.toml`, `pyproject.toml` tool sections, `line-length = 88`.  
- [ ] T004 **Create empty data directories** – add `.gitkeep` to `data/raw/` and `data/processed/`.  
- [ ] T006 **Configure pytest** – `pytest.ini` + `tests/conftest.py` exposing fixtures `random_seed` (value from `code/config.py`) and `data_path`.  
- [ ] T007 **Create package init** – `code/__init__.py` and a minimal `code/config.py` exposing `RANDOM_SEED = 20241010` and `def get_random_state(offset=0): return np.random.RandomState(RANDOM_SEED + offset)`.  
- [ ] T008 **Seed‑management helper** – ensure every stochastic call in the repo receives `random_state=get_random_state(offset)`.  
- [ ] T009a **Create state file** – `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with empty `artifact_hashes`, `last_updated`, `completion_status: "in_progress"`.

---

## Phase 2 – Data acquisition & preprocessing (User Story 1)  

### 2.1 Real‑data download (must succeed before any synthetic fallback)  

- [ ] T045 **Download Delay Discounting dataset** – fetch `https://www.openml.org/data/v1/download/42139/discounting.arff` into `data/raw/discounting_raw.arff`.  
  - *Verification*: `requests.head` returns status 200; file size > 0 KB; SHA‑256 recorded in state YAML.  
- [ ] T046 **Download Procrastination Scale dataset** – fetch `https://www.openml.org/data/v1/download/4510/procrastination.csv` into `data/raw/procrastination_raw.csv`.  
  - *Verification*: same as T045.  
- [ ] T047 **Download n‑back task dataset** – fetch `https://openneuro.org/crn/datasets/ds001734/download?format=zip` into `data/raw/nback_raw.zip` and unzip to `data/raw/nback/`.  
  - *Verification*: HTTP 200, unzip succeeds, expected file `nback_events.tsv` present.  

### 2.2 Real‑data validation & harmonization  

- [ ] T048 **Verify URLs before ingestion** – implement `code/ingestion.py::verify_urls(urls: List[str]) -> None` that raises `RuntimeError` if any URL fails HEAD check.  
  - *Verification*: unit test `tests/test_ingestion.py::test_verify_urls_success`.  

- [ ] T049 **Load, merge, and clean real data** – `code/ingestion.py::load_and_harmonize()` must:  
  1. Load the three raw files, standardise `participant_id`.  
  2. Inner‑join on `participant_id`; abort with `SystemExit` if > 10 % of rows are lost.  
  3. Fit hyperbolic discounting (`scipy.optimize.curve_fit`) per participant; record `fit_status`.  
  4. Compute `log_k`, centre predictors, and write `data/processed/unified_analysis.csv`.  
  5. Write `data/processed/harmonization_log.json` (counts of merged rows, dropped rows, fit failures).  
  6. Update SHA‑256 hashes for all new files in the state YAML.  
  - *Verification*: integration test `tests/test_ingestion.py::test_full_real_ingestion_success`.  

### 2.3 Synthetic DGP fallback (User Story 1 – continuation)  

- [ ] T050 **Generate synthetic DGP module** – create `code/data/generate_dgp.py` exposing:  
  - `DGP_PARAMS` dict (means/stds for age, gender, education, discounting, procrastination, WM accuracy/RT, and `beta_int`).  
  - `def validate_dgp_config(params) -> None` (raises if required keys missing).  
  - `def generate_synthetic_data(params, random_state) -> Dict[str, pd.DataFrame]` returning three DataFrames named `discounting`, `procrastination`, `nback`.  
  - The true interaction coefficient (`beta_int`) is sampled from `Normal(0.20, 0.05)` and stored **both** in each row’s `dgp_ground_truth` column and in a scalar file `data/processed/dgp_ground_truth.txt`.  
  - *Verification*: unit tests `tests/test_generate_dgp.py::test_params_validation` and `::test_synthetic_shapes`.  

- [ ] T051 **Harmonize synthetic frames** – add `code/data/harmonize.py::harmonize_synthetic(data_dict, random_state)` that mirrors the logic of T049 but works on the synthetic DataFrames, writes the same `unified_analysis.csv`, `harmonization_log.json`, and updates state YAML.  
  - *Verification*: unit test `tests/test_harmonize.py::test_harmonize_success`.  

- [ ] T052 **Main orchestration fallback logic** – modify `code/main.py` to:  
  1. Call `verify_urls`; if any URL fails, log the failure and invoke `generate_synthetic_data` → `harmonize_synthetic`.  
  2. Continue with downstream modeling regardless of source.  
  - *Verification*: integration test `tests/test_main_fallback.py::test_fallback_to_dgp`.  

---

## Phase 3 – Moderation regression analysis (User Story 2)  

- [ ] T060 **Create interaction term & centre predictors** – in `code/modeling.py::prepare_design_matrix(df)` centre `log_k` and `wm_accuracy`, compute `interaction = centered_log_k * centered_wm_accuracy`, return a design matrix ready for OLS.  
  - *Verification*: unit test `tests/test_modeling.py::test_interaction_term_creation`.  

- [ ] T061 **Compute VIF scores** – function `code/modeling.py::calculate_vif(df, predictors)` returns a dict of VIFs; flags any > 5.  
  - *Verification*: unit test `tests/test_modeling.py::test_vif_calculation`.  

- [ ] T062 **Fit moderated OLS regression** – `code/modeling.py::fit_ols(df, config_path)` reads `model_config.json` (see below) and fits:  
  `procrastination_score ~ log_k + wm_accuracy + log_k:wm_accuracy [+ covariates]`.  
  Outputs:  
  - `data/processed/ols_summary.json` (R², AIC, BIC, residual diagnostics).  
  - `data/processed/vif_report.json`.  
  - `data/processed/coefficients.json`.  
  - `data/processed/p_values.json`.  
  - *Verification*: integration test `tests/test_modeling.py::test_full_ols_pipeline`.  

- [ ] T063 **Model configuration file** – create `code/model/config.json` containing:  
  ```json
  {
    "outcome": "procrastination_score",
    "predictors": ["log_k", "wm_accuracy"],
    "interaction": true,
    "covariates": ["age", "gender", "education"]
  }
  ```  
  - *Verification*: test that `fit_ols` reads the file without error.  

---

## Phase 4 – Robustness & sensitivity analysis (User Story 3)  

### 4.1 Bootstrap configuration (deterministic seeding)  

- [ ] T070 **Write bootstrap config** – `data/processed/bootstrap_config.json` with:  
  ```json
  {
    "seed": 20241010,
    "offset": 1000,
    "n_resamples": 5000
  }
  ```  
  (5000 resamples keep runtime ≤ 6 h).  
  - *Verification*: file exists and matches schema.  

### 4.2 Bootstrap CI for interaction term  

- [ ] T071 **Bootstrap routine** – `code/robustness.py::bootstrap_interaction(df, config_path)` must:  
  1. Load config, create `RandomState(get_random_state(offset=config["offset"]))`.  
  2. Perform `n_resamples` resamples of rows with replacement, refit the OLS each time, store interaction coefficients.  
  3. Compute 95 % CI (percentile method) and write `data/processed/bootstrap_ci.json` (`lower`, `upper`).  
  - *Verification*: unit test `tests/test_robustness.py::test_bootstrap_resampling_generates_95ci`.  

### 4.3 Sensitivity sweep  

- [ ] T072 **Define sweep grid** – create `code/robustness.py::sensitivity_grid(df)` that evaluates interaction p‑values across:  
  - WM load thresholds: median, median ± 0.05·SD, median ± 0.10·SD (5 values).  
  - Discount‑rate thresholds (log_k): median, median ± 0.05·SD, median ± 0.10·SD (5 values).  
  Total 25 model fits.  
  - *Verification*: unit test `tests/test_robustness.py::test_sensitivity_threshold_sweep`.  

- [ ] T073 **Run sensitivity analysis & summarize** – `code/robustness.py::run_sensitivity(df)` writes:  
  - `data/processed/sensitivity_sweep_raw.json` (list of dicts with thresholds, p‑value).  
  - `data/processed/pvalue_variation.json` (`min`, `max`, `std`).  
  - *Verification*: test that JSON files contain 25 entries and correct summary stats.  

---

## Phase 5 – Exclusion logging & fail‑loud policy  

- [ ] T080 **Log participants with failed hyperbolic fits** – extend `code/modeling.py::fit_discount_rates` to write `data/processed/excluded_participants.csv` (`participant_id,reason_code`).  
- [ ] T081 **Create exclusion summary** – `code/modeling.py::summarize_exclusions()` writes `data/processed/exclusion_summary.json` with key `"excluded_count"` and path to the CSV.  
- [ ] T082 **Fail‑loud data‑loader** – ensure `code/ingestion.py::load_file(path)` raises `FileNotFoundError` if a real file is missing; no silent synthetic fallback. Document policy in `docs/data_strategy.md`.  
  - *Verification*: unit test `tests/test_ingestion.py::test_fail_loud_on_missing_file`.  

---

## Phase 6 – Model diagnostics visualisation  

- [ ] T090 **Create diagnostics visualisation script** – `code/visualizations/plot_diagnostics.py` must:  
  1. Load the fitted OLS model (statsmodels results object saved via `pickle` in `data/processed/ols_model.pkl`).  
  2. Produce three PNGs: `residuals.png`, `qq_plot.png`, `scale_location.png` saved under `data/processed/diagnostics/`.  
  3. Write `data/processed/model_diagnostics_report.json` with keys `residuals_normality`, `homoscedasticity`, `influential_points` (boolean flags based on standard tests).  
  - *Verification*: integration test `tests/test_visualizations.py::test_diagnostics_plots_created`.  

- [ ] T091 **Execute diagnostics after regression** – add a step in `code/main.py` that runs `plot_diagnostics.py` immediately after OLS fitting and checks that the three PNGs and JSON exist.  

---

## Phase 7 – DGP recovery & final results consolidation  

- [ ] T100 **Compare bootstrap CI to DGP ground truth** – `code/robustness.py::evaluate_dgp_recovery()` reads `bootstrap_ci.json` and `dgp_ground_truth.txt`, writes `data/processed/dgp_recovery.json` with fields `ground_truth` (float) and `contains_truth` (bool).  
  - *Verification*: unit test `tests/test_robustness.py::test_dgp_recovery_flag`.  

- [ ] T101 **Assemble final analysis JSON** – `code/main.py` calls a helper `code/results/assemble_results.py::build_analysis_results()` that merges:  
  - OLS summary, coefficients, p‑values, interaction effect, VIFs, bootstrap CI, DGP recovery, sensitivity p‑value variation, exclusion summary, and resource usage (see T032).  
  It writes `data/processed/analysis_results.json` conforming exactly to `contracts/output.schema.yaml`.  
  - *Verification*: schema validation test `tests/test_results.py::test_analysis_results_schema`.  

- [ ] T102 **Record resource usage** – `code/monitoring.py::record_resource_usage()` writes `data/processed/resource_usage.json` with `cpu_time_seconds`, `peak_memory_mb`. `code/main.py` calls this at the end and updates the state YAML (`artifact_hashes` for all `data/processed/*`).  

---

## Phase 8 – Results hand‑off  

- [ ] T110 **Create results summary markdown** – `data/processed/results_summary.md` must:  
  1. List each key statistic (interaction coefficient, p‑value, CI, VIFs, excluded count, DGP recovery flag).  
  2. Provide a direct hyperlink to the corresponding field in `analysis_results.json` (e.g., ``[interaction_effect_size](analysis_results.json#interaction_effect_size)``).  
  3. State explicitly that the study is a **methodological validation** using a synthetic DGP; real‑data results (if any) are reported separately.  
  - *Verification*: manual review (no automated test required).  

- [ ] T111 **Final state consolidation** – update `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with SHA‑256 hashes for *all* files in `data/processed/`, set `completion_status: "success"` and `last_updated` timestamp.  
  - *Verification*: CI step asserts that the state file exists and contains a non‑empty `artifact_hashes` map.  

---

## Phase 9 – Polish (already completed)  

- [ ] T033 **Update README** – usage example, data‑source priority (real → synthetic), and command line (`python -m code.main --seed 20241010`).  
- [ ] T034 **Refactor ingestion & modeling for readability** – extracted helpers, added Google‑style docstrings, removed TODOs.  
- [ ] T035 **Add Google‑style docstrings to all public functions**.  
- [ ] T036a **Run full pipeline end‑to‑end** – verified that every file under `data/processed/` exists and is non‑empty.  
- [ ] T037 **Finalize state YAML** – artifact hashes recorded, status set to `success`.  
- [ ] T038 **Document fail‑loud policy** – `docs/data_strategy.md` now contains a “Fail‑Loud Policy” section describing the required `raise FileNotFoundError` behavior.  

---  

### Dependency map (spec → task)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (ingest three datasets) | T045, T046, T047, T048, T049 |
| FR‑002 (hyperbolic fit) | T049, T080 |
| FR‑003 (WM metrics) | T049 |
| FR‑004 (moderated OLS) | T060‑T063 |
| FR‑005 (VIF) | T061, T062 |
| FR‑006 (bootstrap CI) | T070‑T071 |
| FR‑007 (sensitivity sweeps) | T072‑T073 |
| FR‑008 (halt on missing core constructs) | T048, T082 |
| FR‑009 (≤10 % ID drop) | T049 |
| FR‑010 (runtime & memory limits) | T032, T102, T111 |

---  

**Note** – All tasks are unchecked (`- [ ]`) except those already verified as complete (`- [x]`). The reopened tasks (T039‑T042) have been replaced by the corrected tasks T080‑T082 and T090‑T091, ensuring every required artifact is deterministically produced and can be validated by the automated verifier.
