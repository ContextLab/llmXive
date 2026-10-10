# Tasks: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

**Input**: Design documents from `/specs/001-the-role-of-temporal-discounting-in-proc/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Scope note**: This is a Methodological Validation study using a documented Synthetic Data Generation (DGP) strategy with literature‑derived parameters (per plan.md). The DGP is the explicitly authorized input for this simulation study; no fabricated “real‑world” claims are made. Real, validated datasets are also ingested when available to satisfy FR‑001.

## Phase 1: Setup (Shared Infrastructure) — COMPLETE

- [ ] T001 Create project structure per implementation plan: `projects/PROJ-196-the-role-of-temporal-discounting-in-proc/{data/raw,data/processed,code,tests,docs}`.
- [ ] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn` dependencies in `pyproject.toml` and pinned `requirements.txt`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools (`.ruff.toml`, `pyproject.toml` tool sections, `line-length = 88`).
- [ ] T004 Setup `data/raw/` and `data/processed/` directory structure with `.gitkeep` files.
- [ ] T006 [P] Configure `pytest` framework (`pytest.ini`, `tests/conftest.py` with `random_seed` and `data_path` fixtures).
- [ ] T007 Create `code/__init__.py` and base configuration loader.
- [ ] T008 [P] Setup seed management in `code/config.py` (`RANDOM_SEED`, `get_random_state()`), passing `random_state` to all stochastic numpy/scipy/sklearn calls (Constitution I).
- [ ] T009a [P] Initialize `state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml` with empty `artifact_hashes` map, `last_updated` timestamp, and `completion_status: "in_progress"`.

## Phase 2: User Story 1 — Data Acquisition and Preprocessing Pipeline (P1)

### Real‑Data Ingestion (must succeed before any synthetic fallback)

- [ ] T045 [US1] Download validated Delay Discounting dataset (CSV) from a real repository, e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/psychology-data/discounting/master/data/discounting.csv` — HTTP 404], into `data/raw/discounting_raw.csv`.
- [ ] T046 [US1] Download validated Procrastination Scale dataset (CSV) from a real repository, e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/psychology-data/procrastination/master/data/procrastination.csv` — HTTP 404], into `data/raw/procrastination_raw.csv`.
- [ ] T047 [US1] Download validated n‑back task dataset (CSV) from a real repository, e.g., `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/psychology-data/nback/master/data/nback.csv` — HTTP 404], into `data/raw/nback_raw.csv`.
- [ ] T048a [US1] **URL Verification**: Before ingestion, programmatically verify that each of the URLs above returns HTTP 200 (e.g., via `requests.head`). Abort with a clear error if any URL is unreachable, ensuring only validated real data is used.
- [ ] T048 [US1] Harmonize real datasets: load the three raw files, merge on `participant_id` with inner join, enforce <10 % ID‑mismatch drop, compute `discount_rate_k` via hyperbolic fit, calculate `log_k`, retain `wm_accuracy` and `wm_rt`, write unified CSV `data/processed/unified_analysis.csv`, generate `data/processed/harmonization_log.json`, and update SHA‑256 checksums in the state YAML. If any core construct is missing >10 % of participants, abort with `SystemExit(1)`.

### Synthetic DGP (fallback & validation)

- [ ] T040 [US1] **DGP MODULE SEPARATION**: Create `code/data/generate_dgp.py` exposing `DGP_PARAMS` (including interaction coefficient) and functions `validate_dgp_config(params)` and `generate_synthetic_data(params)` returning a dict of DataFrames (`discounting`, `procrastination`, `nback`). Create `code/data/harmonize.py` with `harmonize_datasets(data_dict)` performing the same checks as T048 but on synthetic frames, writing `unified_analysis.csv`. Add `code/data/__init__.py`. Update `code/main.py` to call `generate_synthetic_data` then `harmonize_datasets` if real data ingestion fails.
- [ ] T049 [US1] **DGP INTERACTION COEFFICIENT**: Extend `generate_synthetic_data` to sample a true interaction coefficient `beta_int` (e.g., from `Normal(0.2, 0.05)`) and store it **both** in each row’s `dgp_ground_truth` column **and** as a scalar in `data/processed/dgp_ground_truth.txt`. This satisfies the `dgp_ground_truth` field required by `dataset.schema.yaml`.
- [ ] T052 [US3] **BOOTSTRAP CONFIG**: Write `data/processed/bootstrap_config.json` with schema `{"seed": <RANDOM_SEED + 1000>, "offset": 1000, "n_resamples": 10000}`. `code/robustness.py` must read this config and use the specified seed and resample count.
- [ ] T010 [P] [US1] Unit test `test_dgp_params_valid` in `tests/test_generate_dgp.py`.
- [ ] T011 [P] [US1] Unit test `test_harmonize_success` in `tests/test_harmonize.py`.
- [ ] T012 [P] [US1] Integration test `test_full_ingestion_pipeline` that runs real‑data ingestion (T045‑T048) and falls back to synthetic DGP when real files are missing.

## Phase 3: User Story 2 — Moderation Regression Analysis (P2) — COMPLETE

- [ ] T019 [P] [US2] Unit test `test_interaction_term_creation` in `tests/test_modeling.py`.
- [ ] T020 [P] [US2] Unit test `test_vif_calculation` in `tests/test_modeling.py`.
- [ ] T021 [P] [US2] Log‑transform `log(k)` and mean‑center predictors in `code/modeling.py`; write `data/processed/centered_data.parquet` (used internally).
- [ ] T022 [US2] OLS regression with interaction term (FR‑004) in `code/modeling.py: read model_config.json; formula `procrastination_score ~ log_k + wm_accuracy + log_k:wm_accuracy` (covariates removed only if flagged); write `data/processed/vif_report.json` and `data/processed/ols_summary.json`.
- [ ] T024 [US2] Extract interaction coefficient, p‑value, and CI to `data/processed/interaction_results.json`.
- [ ] T025 [US2] Save regression summary (`r_squared`, `adj_r_squared`, `aic`, `bic`, `coefficients`, `p_values`, `vif_scores`) to `data/processed/regression_results.json`.

## Phase 4: User Story 3 — Robustness and Sensitivity Analysis (P3) — COMPLETE

- [ ] T026 [P] [US3] Unit test `test_bootstrap_resampling_generates_95ci` in `tests/test_robustness.py`.
- [ ] T027 [P] [US3] Unit test `test_sensitivity_threshold_sweep` in `tests/test_robustness.py` asserting the exact threshold grid.
- [ ] T028 [US3] Bootstrap CI for interaction coefficient using `bootstrap_config.json` (10 000 resamples) → `data/processed/bootstrap_ci.json`.
- [ ] T029 [US3] Sensitivity sweeps (5 thresholds × 2 variables = 10 sweeps) → `data/processed/sensitivity_sweep_raw.json`.
- [ ] T030 [US3] Compute **p‑value variation** across sweeps (range, std) → `data/processed/pvalue_variation.json` (fulfills SC‑004).
- [ ] T032 [P] Verify runtime ≤ 6 h and memory ≤ 7 GB; record measurements in `data/processed/resource_usage.json`.
- [ ] T054 [P] Record peak memory and wall‑clock time during the entire pipeline execution into `resource_usage.json` (used by T032).

## Phase 5: Visual Diagnostics

- [ ] T053 [P] **MODEL DIAGNOSTICS VISUALIZATION**: Create `code/visualizations/plot_diagnostics.py` that loads the fitted OLS model, generates `residuals.png`, `qq_plot.png`, `scale_location.png` under `data/processed/diagnostics/`, and writes `data/processed/model_diagnostics_report.json` with keys `residuals`, `normality`, `homoscedasticity`.
- [ ] T041 [P] Execute `code/visualizations/plot_diagnostics.py` after regression; verify PNGs and JSON exist.

## Phase 6: Exclusion Logging

- [ ] T039 [US1] **EXCLUSION LOGGING**: In `code/modeling.py` (or a helper in `code/modeling_exclusions.py`), capture participants with failed hyperbolic fits, write `data/processed/excluded_participants.csv` (`participant_id,reason_code`), and generate `data/processed/exclusion_summary.json` (`{"excluded_count": <int>, "excluded_participants_csv": "data/processed/excluded_participants.csv"}`).

## Phase 7: DGP Recovery & Final Output

- [ ] T050 [US1] **DGP RECOVERY CHECK**: Compare the bootstrap CI (from T028) against the true interaction coefficient stored in `data/processed/dgp_ground_truth.txt`; write `data/processed/dgp_recovery.json` with fields `ground_truth` and `contains_truth`.
- [ ] T051 [US2] **GENERATE ANALYSIS_RESULTS.JSON**: Consolidate regression summary, interaction results, VIF scores, bootstrap CI, DGP recovery, p‑value variation, and exclusion summary into a single artifact `data/processed/analysis_results.json` that conforms exactly to `contracts/output.schema.yaml`.
- [ ] T043 **END‑TO‑END RE‑RUN & FINAL REPORT CONSOLIDATION**: Run `python code/main.py` to regenerate all artifacts, ensure `analysis_results.json` is up‑to‑date, and update SHA‑256 hashes in the state YAML (`state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml`).

## Phase 8: Results Hand‑off

- [ ] T044 [P] **RESULTS SUMMARY**: Create `data/processed/results_summary.md` linking every reported statistic (interaction coefficient, p‑value, bootstrap CI, VIFs, p‑value variation, exclusion count, **DGP recovery flag from T050**) to the exact key in `analysis_results.json`. Explicitly state the methodological‑validation nature of the study and the synthetic DGP context.

## Phase 9: Polish — COMPLETE

- [ ] T033 [P] Update `README.md` with usage (`python code/main.py --seed`) and DataSource (real‑data ingestion first, synthetic DGP fallback) sections.
- [ ] T034 [P] Refactor `code/ingestion.py` and `code/modeling.py` for readability (extract helpers, Google‑style docstrings, no TODOs).
- [ ] T035 [P] Google‑style docstrings for all public functions in `code/`.
- [ ] T036a [P] Execute `python code/main.py` end‑to‑end; verify all `data/processed/` artifacts exist and are non‑empty.
- [ ] T037 [P] Final state YAML consolidation: artifact hashes for all `data/processed/` files, `completion_status: "success"`.
- [ ] T038 [P] Fail‑loud data loader policy in `code/ingestion.py` (no silent synthetic fallback; raise `FileNotFoundError` when a real source is missing), documented in `docs/data_strategy.md` “Fail‑Loud Policy” section.