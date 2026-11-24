# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-the-role-of-temporal-discounting-in-proc/contracts/`.  

The goal is to deliver a fully‑reproducible end‑to‑end pipeline that  

1. ingests real data from the three validated sources (Delay Discounting, Procrastination Scale, n‑back task);  
2. fits hyperbolic discounting models;  
3. runs a moderated OLS regression;  
4. performs bootstrap‑based robustness checks and sensitivity sweeps;  
5. logs exclusions and diagnostics loudly, and  
6. writes all required artifacts that conform to the JSON schemas.  

---

## Phase 1 – Project scaffolding & early sanity check  

- [ ] **T001** Create project layout (`projects/PROJ-196-the-role-of-temporal-discounting-in-proc/`) with sub‑folders `data/raw`, `data/processed`, `code`, `tests`, `docs`.  
  - *Verification*: `tests/test_scaffolding.py::test_directories_exist` passes.  

- [X] **T002** Add `requirements.txt` and `pyproject.toml` pinning exact library versions (`pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.12.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`).  
  - *Verification*: `tests/test_environment.py::test_requirements_pinned` passes.  

- [X] **T003** Create `code/config.py` exposing `RANDOM_SEED = 20241010` and helper `def get_random_state(offset=0): return np.random.RandomState(RANDOM_SEED + offset)`.  
  - *Verification*: `tests/test_config.py::test_random_seed_exposed` passes.  

---

## Phase 2 – Data acquisition, harmonisation & core‑construct check  

- [ ] **T004** Implement `code/ingestion.py` with:   <!-- ATOMIZE: requested -->
  1. `verify_urls(urls: List[str]) -> None` that raises `RuntimeError` on any non‑200 HEAD response.  
  2. `load_and_harmonize()` that (a) downloads the three raw files into `data/raw/`, (b) loads them, (c) inner‑joins on `participant_id` (abort if > 10 % rows lost), (d) fits a hyperbolic model per participant using `scipy.optimize.curve_fit` (records `fit_status`), (e) computes `log_k`, mean‑centers `log_k` and `wm_accuracy`, (f) creates the interaction term, (g) writes `data/processed/unified_analysis.csv`, (h) writes `data/processed/harmonization_log.json`, (i) writes `data/processed/excluded_participants.csv` (participants with failed fits), (j) writes `data/processed/halt_log.json` if any core construct column is missing or contains NaNs, and (k) updates the project's `state/...yaml` with SHA‑256 hashes of the new files.  
  - *Verification*: `tests/test_ingestion.py::test_full_real_ingestion_success`, `tests/test_halt_on_missing_core.py::test_halt_log_created`, `tests/test_state_update.py::test_hashes_recorded` pass.  

- [X] **T009** Create `code/model/config.json` containing:  

  ```json
  {
    "outcome": "procrastination_score",
    "predictors": ["log_k", "wm_accuracy"],
    "interaction": true,
    "covariates": ["age", "gender", "education"]
  }
  ```  

  - *Verification*: File exists and is valid JSON; `code/modeling.py` loads it without error.  

- [ ] **T007** Create `code/main.py` orchestrator that:   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  1. Calls `ingestion.verify_urls()` on the three official URLs.  
  2. If any URL check fails, aborts with a clear error (no synthetic fallback).  
  3. Otherwise runs `load_and_harmonize()`.  
  4. Proceeds to modelling, robustness, and assembly steps (see later phases).  
  - *Verification*: `tests/test_main_abort_on_url_failure.py::test_abort_without_fallback` passes.  

---

## Phase 3 – Moderated regression analysis  

- [ ] **T008** Implement `code/modeling.py` with three functions:  
  1. `prepare_design_matrix(df)` – mean‑centers `log_k` and `wm_accuracy`, creates `interaction = centered_log_k * centered_wm_accuracy`, returns design matrix.  
  2. `calculate_vif(df, predictors) -> Dict[str, float]` – computes VIF for each predictor and flags any > 5.  
  3. `fit_ols(df, config_path)` – reads `code/model/config.json`, fits OLS (`statsmodels.api.OLS`) with outcome `procrastination_score` and predictors (main effects + interaction + optional covariates). Writes: `data/processed/ols_summary.json`, `coefficients.json`, `p_values.json`, `vif_report.json`, and pickles the fitted model to `data/processed/ols_model.pkl`.  
  - *Verification*: `tests/test_modeling.py::test_full_ols_pipeline`, `tests/test_vif_threshold.py::test_all_vif_below_5` pass.  

---

## Phase 4 – Robustness & sensitivity analysis  

- [ ] **T010** Create `data/processed/bootstrap_config.json` with deterministic seed information:  

  ```json
  {
    "seed": 20241010,
    "offset": 1000,
    "n_resamples": 5000
  }
  ```  

  - *Verification*: `tests/test_bootstrap_config.py::test_schema_validation` passes.  

- [ ] **T011** Implement `code/robustness.py` functions:  
  1. `bootstrap_interaction(df, config_path)` – reads the bootstrap config, builds a `RandomState` via `get_random_state(offset=config["offset"])`, performs `n_resamples` row‑wise resamples, refits the OLS each time, stores the interaction coefficient, computes the 95 % percentile CI, and writes `data/processed/bootstrap_ci.json` (`lower`, `upper`).  
  - *Verification*: `tests/test_robustness.py::test_bootstrap_resampling_generates_95ci` passes.  

- [ ] **T012** Add sensitivity sweep utilities to `code/robustness.py`:  
  - `sensitivity_grid(df)` – returns a list of threshold dictionaries for WM accuracy (median ± 0.05·SD, ± 0.10·SD) and `log_k` (same scheme).  
  - `run_sensitivity(df)` – iterates over the grid points, fits OLS for each, records the interaction p‑value, writes `data/processed/sensitivity_sweep_raw.json` (list of dicts) and `data/processed/pvalue_variation.json` (`min`, `max`, `std`), and writes a boolean `stability_flag` indicating whether > 50 % of swept p‑values cross 0.05.  
  - *Verification*: `tests/test_robustness.py::test_sensitivity_threshold_sweep`, `tests/test_sensitivity_stability.py::test_stability_flag` pass.  

---

## Phase 5 – Diagnostics visualisation  

- [ ] **T013** Implement `code/visualizations/plot_diagnostics.py` that loads the pickled OLS model (`data/processed/ols_model.pkl`) and creates three PNGs saved under `data/processed/diagnostics/`: `residuals.png`, `qq_plot.png`, `scale_location.png`. It also runs standard tests (Shapiro‑Wilk, Breusch‑Pagan, Cook’s distance) and writes `data/processed/model_diagnostics_report.json` with boolean flags `residuals_normality`, `homoscedasticity`, `influential_points`.  
  - *Verification*: `tests/test_visualizations.py::test_diagnostics_plots_created` passes.  

---

## Phase 6 – Final results assembly & resource accounting  

- [ ] **T014** Create `code/results/assemble_results.py` with `build_analysis_results()` that merges: OLS summary, coefficients, p‑values, interaction effect, VIF scores, bootstrap CI, sensitivity variation, stability flag, exclusion summary (`excluded_count` from `excluded_participants.csv`), and resource usage (see T015). The function writes `data/processed/analysis_results.json` that validates against `contracts/output.schema.yaml`.  
  - *Verification*: `tests/test_results.py::test_analysis_results_schema` passes.  

- [ ] **T015** Implement `code/monitoring.py` with `record_resource_usage()` that records total CPU time (seconds) and peak memory (MB) to `data/processed/resource_usage.json`. `code/main.py` calls this after the full pipeline and updates the state YAML with hashes for all `data/processed/*` files.  
  - *Verification*: CI step asserts `resource_usage.json` exists and the state YAML contains matching hashes.  

---

## Phase 7 – Independent entry‑points for each user story  

- [ ] **T016** `code/run_us1.py` – Executes ingestion/harmonisation (real‑data only) and stops after writing `unified_analysis.csv` and `harmonization_log.json`.  
  - *Verification*: `tests/test_us1.py::test_us1_end_to_end` passes.  

- [ ] **T017** `code/run_us2.py` – Loads `unified_analysis.csv`, runs the moderated OLS regression, and produces all regression artifacts.  
  - *Verification*: `tests/test_us2.py::test_us2_regression` passes.  

- [ ] **T018** `code/run_us3.py` – Takes OLS results, runs bootstrap + sensitivity analyses, outputs CI, sweep files, and the `stability_flag`.  
  - *Verification*: `tests/test_us3.py::test_us3_robustness` passes.  

- [ ] **T019** `code/run_us4.py` – Generates exclusion logs (`excluded_participants.csv`) and performs the “halt‑loud” core‑construct check, aborting with a clear error message if any required column is missing or contains NaNs.  
  - *Verification*: `tests/test_us4.py::test_us4_exclusions` passes.  

- [ ] **T020** `code/run_us5.py` – Loads the OLS model and creates diagnostic visualisations without re‑running the regression.  
  - *Verification*: `tests/test_us5.py::test_us5_diagnostics` passes.  

- [ ] **T021** `code/run_us6.py` – Assembles the final `analysis_results.json` from any combination of prior JSON artifacts.  
  - *Verification*: `tests/test_us6.py::test_us6_assembly` passes.  

---

## Phase 8 – Scientific success‑criteria verification  

- [ ] **T022** `tests/test_sc001.py::test_interaction_significant` – Reads `analysis_results.json` and asserts `interaction_significant == true`.  

- [ ] **T023** `tests/test_sc002.py::test_bootstrap_ci_nonzero` – Asserts that when `interaction_significant` is true, the bootstrap CI does **not** contain zero (`lower > 0` or `upper < 0`).  

- [ ] **T024** `tests/test_sc004.py::test_sensitivity_stability` – Computes the proportion of sensitivity‑sweep p‑values crossing the 0.05 threshold; asserts the stability flag is `false` when > 50 % cross.  

- [ ] **T025** `tests/test_sc005.py::test_resource_limits` – Loads `resource_usage.json` and asserts `cpu_time_seconds <= 21600` (6 h) **and** `peak_memory_mb <= 7000`.  

---

## Phase 9 – Contract generation & validation (Phase 0‑1)  

- [ ] **T026** Copy `specs/001-the-role-of-temporal-discounting-in-proc/contracts/dataset.schema.yaml` to project root `contracts/dataset.schema.yaml`.  

- [ ] **T027** Copy `specs/001-the-role-of-temporal-discounting-in-proc/contracts/output.schema.yaml` to `contracts/output.schema.yaml`.  

- [ ] **T028** Run `jsonschema` validation against a sample `unified_analysis.csv` and the generated `analysis_results.json`.  
  - *Verification*: `tests/test_contracts.py::test_schema_validation` passes.  

---

### Dependency map (spec → task)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (ingest three datasets) | T004 |
| FR‑002 (hyperbolic fit) | T004 |
| FR‑003 (WM metrics) | T004 |
| FR‑004 (moderated OLS) | T008, T009 |
| FR‑005 (VIF) | T008 |
| FR‑006 (bootstrap CI) | T011 |
| FR‑007 (sensitivity sweeps) | T012 |
| FR‑008 (halt on missing constructs) | T004, T019 |
| FR‑009 (≤10 % ID loss) | T004 |
| FR‑010 (runtime & memory limits) | T015, T025 |
| SC‑001 (interaction significance) | T022 |
| SC‑002 (bootstrap CI non‑zero) | T023 |
| SC‑003 (VIF < 5) | T008 |
| SC‑004 (sensitivity stability) | T012 |
| SC‑005 (resource limits) | T025 |
| Additional verification (diagnostics, exclusion, DGP recovery) | T013, T014, T018, T021 |

All tasks are presented as unchecked boxes; the verifier will mark them as completed once the corresponding artifacts and tests pass.  
