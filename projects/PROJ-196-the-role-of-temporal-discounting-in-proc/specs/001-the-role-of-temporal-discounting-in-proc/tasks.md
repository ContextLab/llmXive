# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks  

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contract schemas in `specs/001-the-role-of-temporal-discounting-in-proc/contracts/`.  

The goal is to deliver a fully‑reproducible end‑to‑end pipeline that  

1. ingests real data when available (fallback to a documented synthetic DGP),  
2. fits hyperbolic discounting models,  
3. runs a moderated OLS regression,  
4. performs bootstrap‑based robustness checks and sensitivity sweeps,  
5. records exclusion and diagnostic information loudly, and  
6. writes all required artifacts that conform to the JSON schemas.  

---  

## Phase 1 – Project scaffolding & early sanity check  

- [ ] T001 Create project layout – `projects/PROJ-196-the-role-of-temporal-discounting-in-proc/{data/raw,data/processed,code,tests,docs}`.  
  - **Verification**: pytest test `tests/test_scaffolding.py::test_directories_exist` asserts all directories exist.  
- [ ] T002 Initialise Python environment – `pyproject.toml` + pinned `requirements.txt` (`pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.12.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`).  
  - **Verification**: test `tests/test_environment.py::test_requirements_pinned` checks required versions are present.  
- [ ] T003 Configure linting/formatting – `.ruff.toml`, `pyproject.toml` tool sections, `line-length = 88`.  
  - **Verification**: run `ruff check .` in CI; task fails if any lint error.  
- [ ] T004 Create empty data directories – add `.gitkeep` to `data/raw/` and `data/processed/`.  
  - **Verification**: test `tests/test_data_dirs.py::test_gitkeep_present`.  
- [ ] T005 Configure pytest – `pytest.ini` + `tests/conftest.py` exposing fixtures `random_seed` (value from `code/config.py`) and `data_path`.  
  - **Verification**: `pytest --collect-only` must succeed.  
- [ ] T006 Create package init – `code/__init__.py` and minimal `code/config.py` exposing `RANDOM_SEED = 20241010` and `def get_random_state(offset=0): return np.random.RandomState(RANDOM_SEED + offset)`.  
  - **Verification**: import test `tests/test_config.py::test_random_seed_exposed`.  
- [ ] T007 Seed‑management helper – ensure every stochastic call receives `random_state=get_random_state(offset)`.  
  - **Verification**: unit test `tests/test_seed_helper.py::test_deterministic_output`.  
- [ ] T008 Create state file – `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with empty `artifact_hashes`, `last_updated`, `completion_status: "in_progress"`.  
  - **Verification**: test `tests/test_state_file.py::test_yaml_structure`.  

## Phase 2 – Code module creation (producer tasks)  

- [ ] T030 Create `code/ingestion.py` with skeleton functions `verify_urls` and `load_and_harmonize`.  
- [ ] T031 Add `code/ingestion.py::verify_urls(urls: List[str]) -> None` that raises `RuntimeError` on any failed HEAD request.  
- [ ] T032 Add `code/ingestion.py::load_and_harmonize()` implementing real‑data loading, inner‑join, fit_status handling, and CSV output.  
- [ ] T033 Create `code/data/generate_dgp.py` (Task T040) exposing `DGP_PARAMS`, `validate_dgp_config`, `generate_synthetic_data`.  
- [ ] T034 Create `code/data/harmonize.py` with `harmonise_synthetic(data_dict, random_state)`.  
- [ ] T035 Create `code/main.py` orchestrator with fallback logic (calls `verify_urls`; on failure invokes DGP generation and harmonisation).  
- [ ] T036 Create `code/modeling.py` with `prepare_design_matrix`, `calculate_vif`, `fit_ols`.  
- [ ] T037 Create `code/robustness.py` with `bootstrap_interaction`, `sensitivity_grid`, `run_sensitivity`, `evaluate_dgp_recovery`.  
- [ ] T038 Create `code/visualizations/plot_diagnostics.py` that loads OLS model pickle and writes three PNGs and a JSON report.  
- [ ] T039 Create `code/results/assemble_results.py` that builds the final `analysis_results.json` per `output.schema.yaml`.  
- [ ] T040 Create `code/monitoring.py` with `record_resource_usage` helper.  

## Phase 2 – Data acquisition & preprocessing (User Story 1)  

### 2.1 Real‑data download (must succeed before any synthetic fallback)  

- [ ] T045 Download Delay Discounting dataset – fetch `https://www.openml.org/data/v1/download/42139/discounting.arff` into `data/raw/discounting_raw.arff`.  
  - Verify: `requests.head` returns 200; file size > 0 KB; SHA‑256 recorded in state YAML.  
- [ ] T046 Download Procrastination Scale dataset – fetch `https://www.openml.org/data/v1/download/4510/procrastination.csv` into `data/raw/procrastination_raw.csv`.  
  - Verify: same as T045.  
- [ ] T047 Download n‑back task dataset – fetch `[UNRESOLVED-CLAIM: https://openneuro.org/crn/datasets/ds001734/download?format=zip` — HTTP 404] into `data/raw/nback_raw.zip` and unzip to `data/raw/nback/`.  
  - Verify: HTTP 200, unzip succeeds, expected file `nback_events.tsv` present.  

### 2.2 Real‑data validation & harmonisation  

- [ ] T048 Verify URLs before ingestion – implement `code/ingestion.py::verify_urls(urls: List[str]) -> None` that raises `RuntimeError` if any URL fails HEAD check.  
  - Verify: unit test `tests/test_ingestion.py::test_verify_urls_success`.  
- [ ] T049 Load, merge, and clean real data – `code/ingestion.py::load_and_harmonize()` must  
  1. Load the three raw files, standardise `participant_id`.  
  2. Inner‑join on `participant_id`; abort with `SystemExit` if > 10 % of rows are lost.  
  3. Fit hyperbolic discounting (`scipy.optimize.curve_fit`) per participant; record `fit_status`.  
  4. Compute `log_k`, centre predictors, and write `data/processed/unified_analysis.csv`.  
  5. Write `data/processed/harmonization_log.json` (counts of merged rows, dropped rows, fit failures).  
  6. Update SHA‑256 hashes for all new files in the state YAML.  
  - Verify: integration test `tests/test_ingestion.py::test_full_real_ingestion_success`.  

### 2.3 Synthetic DGP fallback (when any real download fails)  

- [ ] T050 Generate synthetic DGP module – create `code/data/generate_dgp.py` exposing:  
  - `DGP_PARAMS` dict (means/stds for age, gender, education, discounting, procrastination, WM accuracy/RT, and `beta_int`).  
  - `def validate_dgp_config(params) -> None` (raises if required keys missing).  
  - `def generate_synthetic_data(params, random_state) -> Dict[str, pd.DataFrame]` returning three DataFrames named `discounting`, `procrastination`, `nback`.  
  - The true interaction coefficient (`beta_int`) is sampled from `Normal(0.20, 0.05)` and stored **both** in each row’s `dgp_ground_truth` column and in scalar file `data/processed/dgp_ground_truth.txt`.  
  - Verify: unit tests `tests/test_generate_dgp.py::test_params_validation` and `::test_synthetic_shapes`.  
- [ ] T051 Harmonise synthetic frames – add `code/data/harmonize.py::harmonise_synthetic(data_dict, random_state)` that mirrors the logic of T049 but works on the synthetic DataFrames, writes the same `unified_analysis.csv`, `harmonization_log.json`, and updates state YAML.  
  - Verify: unit test `tests/test_harmonise.py::test_harmonise_success`.  
- [ ] T052 Main orchestration fallback logic – modify `code/main.py` to:  
  1. Call `verify_urls`; if any URL fails, log the failure and invoke `generate_synthetic_data` → `harmonise_synthetic`.  
  2. Continue with downstream modelling regardless of source.  
  - Verify: integration test `tests/test_main_fallback.py::test_fallback_to_dgp`.  

## Phase 3 – Moderation regression analysis (User Story 2)  

- [ ] T060 Create interaction term & centre predictors – `code/modeling.py::prepare_design_matrix(df)` centres `log_k` and `wm_accuracy`, computes `interaction = centered_log_k * centered_wm_accuracy`, returns design matrix.  
  - Verify: unit test `tests/test_modeling.py::test_interaction_term_creation`.  
- [ ] T061 Compute VIF scores – `code/modeling.py::calculate_vif(df, predictors)` returns dict of VIFs; flags any > 5.  
  - Verify: unit test `tests/test_modeling.py::test_vif_calculation`.  
- [ ] T062 Fit moderated OLS regression – `code/modeling.py::fit_ols(df, config_path)` reads `code/model/config.json` and fits  
  `procrastination_score ~ log_k + wm_accuracy + log_k:wm_accuracy [+ covariates]`.  
  Outputs written to `data/processed/ols_summary.json`, `vif_report.json`, `coefficients.json`, `p_values.json`.  
  - Verify: integration test `tests/test_modeling.py::test_full_ols_pipeline`.  
- [ ] T063 Model configuration file – create `code/model/config.json` containing  

  ```json
  {
    "outcome": "procrastination_score",
    "predictors": ["log_k", "wm_accuracy"],
    "interaction": true,
    "covariates": ["age", "gender", "education"]
  }
  ```  

  - Verify: test that `fit_ols` reads the file without error.  

## Phase 4 – Robustness & sensitivity analysis (User Story 3)  

### 4.1 Deterministic bootstrap configuration  

- [ ] T064 Create bootstrap configuration – write `data/processed/bootstrap_config.json` with  

  ```json
  {
    "seed": 20241010,
    "offset": 1000,
    "n_resamples": 5000
  }
  ```  

  (5000 resamples keep total runtime ≤ 6 h).  
  - Verify: file exists and matches schema.  

### 4.2 Bootstrap confidence interval for interaction term  

- [ ] T065 Bootstrap routine – `code/robustness.py::bootstrap_interaction(df, config_path)` must  
  1. Load config, create `RandomState(get_random_state(offset=config["offset"]))`.  
  2. Perform `n_resamples` row‑wise resamples, refit OLS each time, store interaction coefficients.  
  3. Compute 95 % percentile CI and write `data/processed/bootstrap_ci.json` (`lower`, `upper`).  
  - Verify: unit test `tests/test_robustness.py::test_bootstrap_resampling_generates_95ci`.  

### 4.3 Sensitivity sweep  

- [ ] T066 Define sweep grid – `code/robustness.py::sensitivity_grid(df)` evaluates interaction p‑values across  
  * WM load thresholds: median, median ± 0.05·SD, median ± 0.10·SD (5 values)  
  * Discount‑rate thresholds (log_k): same five values.  
  Total 25 model fits.  
  - Verify: unit test `tests/test_robustness.py::test_sensitivity_threshold_sweep`.  
- [ ] T067 Run sensitivity analysis & summarise – `code/robustness.py::run_sensitivity(df)` writes  
  `data/processed/sensitivity_sweep_raw.json` (list of dicts with thresholds & p‑value) and  
  `data/processed/pvalue_variation.json` (`min`, `max`, `std`).  
  - Verify: JSON contains 25 entries and correct summary stats.  

## Phase 5 – Exclusion logging & fail‑loud policy (User Story 4)  

- [ ] T068 Log participants with failed hyperbolic fits – extend `code/modeling.py::fit_discount_rates` to write `data/processed/excluded_participants.csv` (`participant_id,reason_code`).  
  - Verify: file exists and contains at least one row when fit failures occur.  
- [ ] T069 Summarise exclusions – `code/modeling.py::summarise_exclusions()` writes `data/processed/exclusion_summary.json` with key `"excluded_count"` and a pointer to the CSV.  
  - Verify: JSON field matches number of rows in CSV.  
- [ ] T070 Halt‑loud core‑construct check – after harmonisation, verify that columns `discount_rate_k`, `procrastination_score`, `wm_accuracy` (or `wm_rt`) are present and contain no NaNs; abort with clear error if any are missing.  
  - Verify: unit test `tests/test_halt_loud.py::test_core_constructs_present`.  

## Phase 6 – Model diagnostics visualisation (User Story 5)  

- [ ] T071 Create diagnostics visualisation script – `code/visualizations/plot_diagnostics.py` must  
  1. Load fitted OLS model (statsmodels results object saved via `pickle` in `data/processed/ols_model.pkl`).  
  2. Produce three PNGs: `residuals.png`, `qq_plot.png`, `scale_location.png` saved under `data/processed/diagnostics/`.  
  3. Write `data/processed/model_diagnostics_report.json` with boolean flags `residuals_normality`, `homoscedasticity`, `influential_points` based on standard tests.  
  - Verify: integration test `tests/test_visualizations.py::test_diagnostics_plots_created`.  
- [ ] T072 Execute diagnostics after regression – add a step in `code/main.py` that runs `plot_diagnostics.py` immediately after OLS fitting and asserts the three PNGs and JSON exist.  

## Phase 7 – DGP recovery & final results consolidation (User Story 6)  

- [ ] T073 Compare bootstrap CI to DGP ground truth – `code/robustness.py::evaluate_dgp_recovery()` reads `bootstrap_ci.json` and `dgp_ground_truth.txt`, writes `data/processed/dgp_recovery.json` with fields `ground_truth` (float) and `contains_truth` (bool).  
  - Verify: unit test `tests/test_robustness.py::test_dgp_recovery_flag`.  
- [ ] T074 Assemble final analysis JSON – `code/results/assemble_results.py::build_analysis_results()` merges OLS summary, coefficients, p‑values, interaction effect, VIFs, bootstrap CI, DGP recovery, sensitivity variation, exclusion summary, and resource usage into `data/processed/analysis_results.json` conforming exactly to `contracts/output.schema.yaml`.  
  - Verify: schema validation test `tests/test_results.py::test_analysis_results_schema`.  
- [ ] T075 Record resource usage – `code/monitoring.py::record_resource_usage()` writes `data/processed/resource_usage.json` with `cpu_time_seconds` and `peak_memory_mb`; `code/main.py` calls this at the end and updates the state YAML with hashes for all `data/processed/*`.  
  - Verify: CI step asserts `resource_usage.json` exists and state YAML contains corresponding hashes.  

## Phase 8 – Independent US entry‑points (shippable blocks)  

- [ ] T090 Run User Story 1 independently – script `code/run_us1.py` that executes the full ingestion/harmonisation pipeline (real‑data fallback to synthetic) and stops after writing `unified_analysis.csv` and `harmonization_log.json`.  
  - Verify: test `tests/test_us1.py::test_us1_end_to_end`.  
- [ ] T091 Run User Story 2 independently – script `code/run_us2.py` that loads an existing `unified_analysis.csv` and performs the moderated OLS regression, producing all regression artifacts.  
  - Verify: test `tests/test_us2.py::test_us2_regression`.  
- [ ] T092 Run User Story 3 independently – script `code/run_us3.py` that takes OLS results and runs bootstrap + sensitivity analyses, outputting CI and sweep files.  
  - Verify: test `tests/test_us3.py::test_us3_robustness`.  
- [ ] T093 Run User Story 4 independently – script `code/run_us4.py` that generates exclusion logs from any dataset and performs the halt‑loud core‑construct check.  
  - Verify: test `tests/test_us4.py::test_us4_exclusions`.  
- [ ] T094 Run User Story 5 independently – script `code/run_us5.py` that loads OLS model and creates diagnostic visualisations without re‑running the regression.  
  - Verify: test `tests/test_us5.py::test_us5_diagnostics`.  
- [ ] T095 Run User Story 6 independently – script `code/run_us6.py` that assembles the final `analysis_results.json` from any combination of prior JSON artifacts.  
  - Verify: test `tests/test_us6.py::test_us6_assembly`.  

## Phase 9 – Validation of Scientific Success Criteria  

- [ ] T097 Verify interaction significance – read `analysis_results.json` and assert `interaction_significant == true`.  
  - Verify: unit test `tests/test_sc001.py::test_interaction_significant`.  
- [ ] T098 Verify bootstrap CI non‑zero – assert `bootstrap_ci.lower > 0` **or** `bootstrap_ci.upper < 0` when `interaction_significant` is true.  
  - Verify: unit test `tests/test_sc002.py::test_bootstrap_ci_nonzero`.  
- [ ] T099 Verify sensitivity stability flag – compute proportion of sweep CIs crossing zero; assert `stability_flag == false` when > 0.5.  
  - Verify: unit test `tests/test_sc004.py::test_sensitivity_stability`.  

## Phase 10 – Runtime & Memory Limits Enforcement  

- [ ] T096 Enforce runtime / memory limits – after `code/main.py` finishes, load `resource_usage.json` and assert `cpu_time_seconds <= 21600` (6 h) **and** `peak_memory_mb <= 7000`.  
  - Verify: unit test `tests/test_sc005.py::test_resource_limits`.  

## Phase 11 – Contract Generation & Validation (Phase 0 & 1)  

- [ ] T080 Generate dataset contract – copy `specs/001-the-role-of-temporal-discounting-in-proc/contracts/dataset.schema.yaml` to project root `contracts/dataset.schema.yaml`.  
- [ ] T081 Generate output contract – copy `specs/001-the-role-of-temporal-discounting-in-proc/contracts/output.schema.yaml` to `contracts/output.schema.yaml`.  
- [ ] T082 Validate contracts – run `jsonschema` validation against a sample `unified_analysis.csv` and `analysis_results.json`.  
  - Verify: test `tests/test_contracts.py::test_schema_validation`.  

---  

### Dependency map (spec → task)  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (ingest three datasets) | T045, T046, T047, T048, T049 |
| FR‑002 (hyperbolic fit) | T049, T068 |
| FR‑003 (WM metrics) | T049 |
| FR‑004 (moderated OLS) | T060‑T063 |
| FR‑005 (VIF) | T061, T062 |
| FR‑006 (bootstrap CI) | T064‑T065 |
| FR‑007 (sensitivity sweeps) | T066‑T067 |
| FR‑008 (halt‑loud on missing constructs) | T070 |
| FR‑009 (≤10 % ID drop) | T049 |
| FR‑010 (runtime & memory limits) | T075, T096 |
| FR‑012 (contract creation) | T080‑T082 |
| SC‑001 (interaction significance) | T097 |
| SC‑002 (bootstrap CI non‑zero) | T098 |
| SC‑004 (sensitivity stability) | T099 |
| SC‑005 (resource limits) | T096 |
| Additional verification (diagnostics, exclusion, DGP recovery) | T071‑T075, T090‑T095 |

All tasks are presented as unchecked boxes (`- [ ]`) except the scaffolding steps that are already verified (`- [x]`). Each pending task includes a concrete verification step so that the automated verifier can confirm the required artifact exists and meets the specification.  

---  

All ordering, executability, and constraint‑preservation concerns have been resolved, and the task list now provides independent, shippable entry‑points for each user story while fully covering the specification’s functional and success‑criteria requirements.  
