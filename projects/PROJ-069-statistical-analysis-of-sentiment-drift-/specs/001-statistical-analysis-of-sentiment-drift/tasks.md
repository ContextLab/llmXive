# Tasks: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions  

**Input**: `spec.md`, `plan.md`, `existing artifacts in the repository`.  

### Phase 1 – Project Bootstrap  

- [ ] T001 Initialize the standard project directory layout (`code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `outputs/`, `notebooks/`, `scripts/`). – **file(s)**: `scripts/init_dirs.sh`  
- [ ] T002 Create a template environment file `.env.example` with placeholders for `FRED_API_KEY` and `TWITTER_BEARER_TOKEN`; copy it to a real `.env`, verify that both variables are present, and run a lightweight sanity check that `code/data_ingestion.py` can read them. – **file(s)**: `.env.example`, `.env`, `tests/integration/test_env_loading.py`  
- [ ] T017 Compute SHA‑256 checksums for all files under `data/raw/` after they are downloaded and write a manifest `data/checksums.json`. – **file(s)**: `data/checksums.json`  

### Phase 2 – Data Acquisition (User Story 1)  

- [ ] T003 Download the three macro‑economic series from the official FRED API (GDP → `data/raw/fred_gdp.csv`, Unemployment → `data/raw/fred_unrate.csv`, Consumer Confidence → `data/raw/fred_consumer_confidence.csv`). – **file(s)**: `code/data_ingestion.py`  
- [ ] T018 Log the exact source URL for each macro series download (required by FR‑018) and append the URLs to `results/download_log.json`. – **file(s)**: `results/download_log.json`  
- [ ] T004 Download sentiment scores from the Twitter Academic Research API (requires a valid bearer token), store the raw CSV as `data/raw/twitter_sentiment.csv`. – **file(s)**: `code/data_ingestion.py`  
- [ ] T019 Verify that the downloaded Twitter sentiment dataset contains **≥ 10 000** records; abort with a clear error if the check fails (FR‑015). – **file(s)**: `code/validation.py`  

### Phase 3 – Pre‑processing & Alignment (User Story 1)  

- [ ] T005 Resample daily Twitter sentiment to **monthly** positive/negative/neutral ratios, compute `media_volume`, flag months with `< 30` tweets or average confidence < 0.7 as low‑confidence, transform the three ratios into two additive log‑ratio (ILR) components, linearly interpolate any missing macro values (only if missing ≤ 5 % per series), record interpolation percentages and the method used, and write the merged monthly file `data/processed/aligned_monthly.csv`. Then aggregate the monthly rows to **quarterly** frequency (averaging the three months per quarter), propagate the low‑confidence flag, and write `data/processed/aligned_quarterly.csv` together with a provenance log `data/processed/data_quality_log.json`. – **file(s)**: `code/preprocessing.py`, `data/processed/aligned_monthly.csv`, `data/processed/aligned_quarterly.csv`, `data/processed/data_quality_log.json`  
- [ ] T020 Compare linear interpolation with a Kalman‑Smoother model‑based imputation for each macro series; compute the lag‑1 autocorrelation difference. If the absolute difference exceeds **0.05**, adopt the Kalman‑Smoother method and rewrite the aligned files accordingly, logging the chosen method in `results/imputation_choice.json`. (FR‑017) – **file(s)**: `code/imputation_comparison.py`, `results/imputation_choice.json`  
- [ ] T022 Abort the pipeline if the proportion of low‑confidence quarters in `aligned_quarterly.csv` exceeds **20 %**; log the proportion and raise a `LowConfidenceError`. (FR‑010a) – **file(s)**: `code/preprocessing.py`  

### Phase 4 – Diagnostic Checks (User Story 2)  

- [ ] T006 Run Augmented‑Dickey‑Fuller (ADF) tests on every series in the quarterly file; if a series remains non‑stationary after first differencing, automatically apply a log or Box‑Cox transformation and re‑test. Compute Variance Inflation Factors for the three macro predictors, flag any with VIF ≥ 33, run the Johansen cointegration test (select rank by the trace statistic with the conflict‑resolution rule from the spec), determine the optimal VAR lag order via AIC (maximum 4 quarters), **perform the feasibility check that the total number of VAR parameters ≤ (observations / 5)**, and consolidate all diagnostics (ADF p‑values, transformation actions, VIF values, cointegration rank, selected lag, feasibility outcome, imputation method logs) into `results/diagnostics.json`. – **file(s)**: `code/modeling.py`, `results/diagnostics.json`  
- [ ] T021 Run VAR feasibility check (FR‑021) using `code/power_analysis.py`; compute the maximum allowable VAR parameters as floor(observations/5). If the current parameter count exceeds this limit, either reduce the lag order automatically or abort with a clear error, and log the outcome in `results/feasibility_check.json`. – **file(s)**: `code/power_analysis.py`, `results/feasibility_check.json`  
- [ ] T007 Using the diagnostics from T006 (and feasibility outcome from T021), fit the appropriate model (VAR if cointegration rank = 0, otherwise VECM) with the selected lag, serialize the fitted object to `results/model_fit.pkl`, and produce a summary `results/model_stats.json` that includes model type, optimal lag, cointegration rank, and bidirectional Granger‑causality F‑statistics and p‑values for all six direction pairs (sentiment ↔ GDP, unemployment, consumer confidence). – **file(s)**: `code/modeling.py`, `results/model_fit.pkl`, `results/model_stats.json`  

### Phase 5 – Model Fitting & Granger Causality (User Story 2)  

*(Note: T007 now incorporates the feasibility outcome; no additional tasks required here.)*  

### Phase 6 – Robustness Validation (User Story 3)  

- [ ] T008 Perform a Moving Block Bootstrap on the **monthly** aligned data (`data/processed/aligned_monthly.csv`) with 1 000 iterations, block length = 1 quarter (≈ 13 weeks), compute 95 % confidence intervals for each VAR coefficient, and verify that the interval width for the key `sentiment → GDP` coefficient is ≤ 20 % of the point estimate. Store the bootstrap output and pass/fail flag in `results/bootstrap_validation.json`. – **file(s)**: `code/validation.py`, `results/bootstrap_validation.json`  
- [ ] T009 Conduct the sensitivity analysis defined in the spec: for masking proportions **0.05**, **0.10**, and **0.15**, randomly mask the quarterly dataset, re‑interpolate, re‑run the full modeling pipeline (T006–T007), compute the absolute shift in each Granger‑causality p‑value, and assert that every shift ≤ 0.01. Summarize the results in `results/sensitivity_analysis.json`. – **file(s)**: `code/validation.py`, `results/sensitivity_analysis.json`  
- [ ] T010 Execute a rolling‑origin forecast: hold out the most recent 8 quarters, re‑fit the model on each expanding window, forecast the hold‑out period, and report RMSE and MAE in `results/forecast_validation.json`. – **file(s)**: `code/validation.py`, `results/forecast_validation.json`  

### Phase 7 – Recession Metadata & Visualisation (User Story 3)  

- [ ] T011 Download the official NBER recession dates CSV (`[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/datasets/nber-business-cycle-dating/master/data/nber-cycles.csv` — HTTP 404]), convert it to JSON, and store as `data/metadata/recession_periods.json`. – **file(s)**: `code/visualization.py`, `data/metadata/recession_periods.json`  
- [ ] T023 Run PELT change‑point detection (using `ruptures` with BIC penalty and minimum segment length = 2 quarters) on each additive log‑ratio sentiment component, compute the proportion of detected breakpoints that fall within ±1 quarter of NBER recession start/end dates, and write `results/pelt_breakpoints.json` containing the breakpoints and the alignment metric (must be ≥ 80 % per SC‑014). – **file(s)**: `code/pelt_breakpoints.py`, `results/pelt_breakpoints.json`  
- [ ] T012 Generate the required visual artefacts:  
  * Time‑series plot of sentiment components and macro variables with recession shading (PNG + PDF).  
  * Impulse‑response function plots for each VAR/VECM coefficient.  
  * Cross‑correlation heatmap.  
  All figures are written to `outputs/figures/` with appropriate filenames. – **file(s)**: `code/visualization.py`, `outputs/figures/time_series.png`, `outputs/figures/irf_sentiment_gdp.png`, `outputs/figures/cross_corr_heatmap.png`  

### Phase 8 – Reproducible Notebook & Report (User Story 3)  

- [ ] T013 Assemble a fully reproducible Jupyter notebook `notebooks/sentiment_drift_analysis.ipynb` that sequentially runs every script from T003 to T012, displays all figures, and embeds a narrative discussion of results, including explicit statements about Granger‑causality interpretation (per FR‑019). – **file(s)**: `notebooks/sentiment_drift_analysis.ipynb`  
- [ ] T014 Convert the notebook to a PDF report `outputs/report.pdf` using `nbconvert` with a custom LaTeX template that preserves figure captions and recession shading. – **file(s)**: `outputs/report.pdf`  

### Phase 9 – Reproducibility Checks & Handoff  

- [ ] T015 Provide a `scripts/quickstart.sh` that (i) creates a virtual environment, (ii) installs `requirements.txt`, (iii) runs the notebook, and (iv) checks that all expected artefacts (`aligned_quarterly.csv`, `model_stats.json`, `bootstrap_validation.json`, `report.pdf`, figure files) exist. – **file(s)**: `scripts/quickstart.sh`  
- [ ] T024 Add an integration test `tests/integration/test_quickstart.sh` that executes `quickstart.sh` and asserts the presence and integrity (via checksum) of each expected artefact. – **file(s)**: `tests/integration/test_quickstart.sh`  
- [ ] T016 Add contract‑based unit tests for every JSON schema in `specs/001-statistical-analysis-of-sentiment-drift/contracts/` and explicitly map each test to its originating functional requirement (e.g., FR‑004 → `test_model_result_schema.py`). – **file(s)**: `tests/contract/test_aligned_quarterly_schema.py`, `tests/contract/test_model_result_schema.py`, `tests/contract/test_model_results_schema.py`  

## Verification Mapping  

| Spec Requirement | Task(s) that satisfy it |
|------------------|--------------------------|
| FR‑001, FR‑002, FR‑015, FR‑018 | T003, T004, T018 |
| FR‑010a, FR‑011 | T005, T022 |
| FR‑017 | T020 |
| FR‑003, FR‑009, FR‑013, FR‑021 | T006, T021 |
| FR‑004, FR‑020 | T006 (VIF) & T007 (Granger) |
| FR‑014 | T011, T023 |
| FR‑022 | T008 |
| FR‑012 | T009 |
| FR‑006 | T010 |
| FR‑005, FR‑007 | T012, T013, T014 |
| SC‑001 … SC‑014 | Covered by the corresponding validation tasks (T006‑T010, T012‑T014, T023) |
| SC‑014 (≥ 80 % breakpoint alignment) | T023 |
| SC‑006 (masking proportion thresholds) | T009 (uses concrete 0.05‑0.15) |
| SC‑004 (bootstrap CI width) | T008 |
| SC‑005 (recession shading) | T012 |
| SC‑001 (significance) | T007 |
| SC‑003 (reproducibility) | T013, T015, T024 |
| SC‑002 (data completeness) | T003, T004, T005, T017 |
| SC‑014 (breakpoint‑recession metric) | T023 |

---  

*All tasks are unchecked (`- [ ]`) to indicate they remain to be executed. Completed work from prior iterations should be reflected by checking the appropriate boxes once the artefacts exist and pass their tests.*  