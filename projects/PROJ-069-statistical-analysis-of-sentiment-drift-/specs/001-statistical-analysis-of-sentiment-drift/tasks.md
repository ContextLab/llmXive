# Tasks: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions  

**Inputs**: `spec.md`, `plan.md`, existing repository artifacts.  

The following checklist implements the full research pipeline required by the specification.  
Unchecked boxes (`- [ ]`) indicate work that still needs to be performed; once a task is completed and its artefacts pass the independent tests described in the indented lines, the box should be checked.

---

## Phase 1 – Project bootstrap & environment  

- [ ] T001 [P1] [US-1] **Create project layout, environment files, and sanity‑check script**  
  - Ensure directories `code/`, `data/raw/`, `data/processed/`, `data/metadata/`, `outputs/figures/`, `notebooks/`, `scripts/`, `tests/` exist.  
  - Add `.env.example` with placeholders `FRED_API_KEY` and `TWITTER_BEARER_TOKEN`; copy to `.env` and verify both variables are set.  
  - Provide `scripts/check_env.py` that loads the variables via `python‑dotenv` and exits with status 0 if both are present, otherwise prints a clear error message.  
  - **Verification**: Run `python scripts/check_env.py`; it must exit cleanly and print the two variable names.

---

## Phase 2 – Data acquisition  

- [ ] T002 [P1] [US-1] **Download macro‑economic series from the official FRED API**   <!-- FAILED-IN-EXECUTION: code/ingest/fetch_fred.py exit=1 -->
  - Use `fredapi` to fetch quarterly GDP (`GDP`), unemployment rate (`UNRATE`), and consumer confidence (`CSCICP03`).  
  - Save as `data/raw/fred/fred_gdp.csv`, `data/raw/fred/fred_unrate.csv`, `data/raw/fred/fred_consumer_confidence.csv`.  
  - Compute SHA‑256 checksums for each CSV and record them in `data/checksums.json`.  
  - Log each source URL (including API endpoint and series ID) in `results/fred_download_log.json`.  
  - **Verification**: Each CSV must contain at least 30 rows and a header row; the log file must be valid JSON with three entries; `data/checksums.json` must contain matching SHA‑256 entries.

- [ ] T003 [P1] [US-1] **Download verified sentiment dataset from HuggingFace**  
  - Stream the open dataset `allenai/tweet_sentiment` via `datasets.load_dataset(..., streaming=True)` and write the raw records to `data/raw/sentiment_raw.csv`.  
  - Abort with a clear error if the final record count is < 10 000 (FR‑015).  
  - Compute SHA‑256 checksum of `sentiment_raw.csv` and add it to `data/checksums.json`.  
  - **Verification**: `wc -l data/raw/sentiment_raw.csv` ≥ 10 000 and the file is a valid CSV with columns `text`, `label`; checksum entry exists.

- [ ] T004 [P1] [US-1] **Extract sentiment scores with confidence ≥ 0.7**  
  - Run `code/ingest/sentiment_extraction.py` (RoBERTa‑base) on `sentiment_raw.csv`; output `data/processed/sentiment_extracted.csv` containing columns `date`, `pos_ratio`, `neg_ratio`, `neu_ratio`, `media_volume`, `avg_confidence`.  
  - Record model name, tokenizer version, and confidence threshold in `metadata/sentiment_extraction.json`.  
  - **Verification**: The output CSV must have a row for every day present in the raw data and `media_volume` ≥ 30 for at least 90 % of days; the JSON must contain the fields `model`, `tokenizer`, `confidence_threshold`.

---

## Phase 3 – Pre‑processing & alignment  

- [ ] T005 [P1] [US-1] **Merge macro and sentiment data to monthly frequency with interpolation & imputation comparison**  
  - Resample daily sentiment ratios to monthly averages; compute `media_volume` per month and flag months with `< 30` posts or `avg_confidence < 0.7` as low‑confidence.  
  - Perform **linear interpolation** for missing macro values (only if missing ≤ 5 % per series).  
  - Independently perform **Kalman‑Smoother** imputation for the same missing points.  
  - Compute lag‑1 autocorrelation for each series under both imputation methods; if the absolute difference exceeds **0.05**, select the method with the smaller difference (prefer linear unless Kalman improves autocorrelation).  
  - Transform the three sentiment ratios into two additive log‑ratio (ILR) components (`sentiment_ilr_1`, `sentiment_ilr_2`).  
  - Write `data/processed/aligned_monthly.csv`.  
  - Generate `data/processed/data_quality_log.json` documenting: interpolation method chosen, percentages of imputed points per series, lag‑1 autocorrelation values for both methods, and low‑confidence month flags.  
  - **Verification**: The CSV must validate against `aligned_timeseries.schema.yaml`; the JSON log must contain keys `imputation_method`, `interpolation_percent_*`, `lag1_acf_linear`, `lag1_acf_kalman`, `low_confidence_months`.

- [ ] T006 [P1] [US-1] **Aggregate monthly data to quarterly frequency**  
  - Average the three months of each quarter for all numeric fields; propagate the low‑confidence flag (quarter is low‑confidence if any constituent month is flagged).  
  - Produce `data/processed/aligned_quarterly.csv` and update `data/processed/data_quality_log.json` with quarterly interpolation percentages and flag summaries.  
  - **Verification**: The quarterly CSV must validate against `aligned_data.schema.yaml`; at least 95 % of quarters must have interpolation ≤ 5 % and low‑confidence flag ≤ 20 % (FR‑010a).

- [ ] T022 [P1] [US-1] **Enforce abort on excessive low‑confidence quarters**  
  - After T006, compute the proportion of low‑confidence quarters.  
  - If the proportion exceeds **20 %** of total quarters, abort the pipeline with a clear error message indicating the failure of FR‑010a.  
  - **Verification**: Pipeline exits with non‑zero status and descriptive error when the threshold is crossed.

- [ ] T020 [P1] [US-1] **Validate overall quarterly coverage ≥ 95 %**  
  - Count total expected quarterly timestamps between the earliest and latest dates in the macro series.  
  - Verify that at least 95 % of those timestamps are present in `aligned_quarterly.csv`.  
  - Abort with an informative error if the coverage falls below the threshold.  
  - **Verification**: Coverage metric is computed and logged; pipeline fails if < 0.95.

---

## Phase 4 – Diagnostic checks, feasibility, & model fitting  

- [ ] T007 [P2] [US-2] **Stationarity, VIF, cointegration, lag selection, and feasibility check**  
  - Run ADF tests on every quarterly series; if non‑stationary, difference once and re‑test. If still non‑stationary, apply log or Box‑Cox transformation (FR‑009).  
  - Compute Variance Inflation Factors for GDP, UNRATE, and Consumer Confidence; flag any VIF ≥ 33 (FR‑020).  
  - Perform Johansen cointegration test; select rank using the trace statistic, applying the conflict‑resolution rule described in FR‑013.  
  - Choose optimal VAR lag via AIC (max 4 quarters).  
  - Verify feasibility: `num_parameters ≤ floor(observations/5)` (FR‑021); if violated, automatically reduce lag order and log the decision.  
  - Log the **imputation method** used (from T005) and the **percentage of interpolated points** for each series as required by FR‑011.  
  - Consolidate all results in `results/diagnostics.json`.  
  - **Verification**: `results/diagnostics.json` must contain keys `adf`, `vif`, `cointegration_rank`, `optimal_lag`, `feasibility`, `imputation_method`, `interpolation_percent_*`, and each sub‑object must include p‑values, test statistics, and any transformation actions taken.

- [ ] T008 [P2] [US-2] **Fit VAR or VECM and compute Granger‑causality statistics**  
  - Based on the cointegration rank, fit a VAR (rank 0) or VECM (rank > 0) using the selected lag. Serialize the fitted model to `results/model_fit.pkl`.  
  - Generate `results/model_stats.json` summarising `model_type`, `optimal_lag`, `cointegration_rank`, and a list of bidirectional Granger‑causality results (direction, F‑stat, p‑value, Benjamini‑Hochberg‑adjusted p‑value).  
  - **Verification**: The JSON must contain 12 direction entries (sentiment ↔ each macro variable) and all p‑values must be ≤ 1.0; the pickle file must be loadable with `statsmodels`.

---

## Phase 5 – Robustness validation  

- [ ] T009 [P3] [US-3] **Moving Block Bootstrap (MBB) validation with convergence check**  
  - Apply MBB to the **monthly** aligned data (`aligned_monthly.csv`) with 1 000 iterations, block length = 13 weeks (≈ 1 quarter).  
  - Compute 95 % confidence intervals for each VAR coefficient; verify that:  
    1. CI width for `sentiment_ilr_1 → gdp_growth` ≤ 20 % of its point estimate,  
    2. The interval contains the point estimate,  
    3. Coefficient‑of‑variation < 0.1,  
    4. CI width stabilises (change < 1 %) over three consecutive iteration batches (convergence).  
  - Store results and a pass/fail flag in `results/bootstrap_validation.json`.  
  - **Verification**: The JSON must include `ci_lower`, `ci_upper`, `point_estimate`, `width_ratio`, `cv`, and `converged` (true/false); all criteria must be satisfied for a pass.

- [ ] T010 [P3] [US-4] **Sensitivity analysis on data masking**  
  - For masking proportions 0.05, 0.10, and 0.15: randomly mask that fraction of quarterly observations, re‑interpolate using the method selected in T005, re‑run the full modeling pipeline (T007–T008), and compute the absolute shift in each Granger‑causality p‑value relative to the baseline.  
  - Use the fixed random seed defined in T019.  
  - Assert that every shift ≤ 0.01 (FR‑012).  
  - Summarise results in `results/sensitivity_analysis.json`.  
  - **Verification**: JSON must contain an array of objects with fields `masking_proportion`, `direction`, `p_value_shift`; all `p_value_shift` values ≤ 0.01.

- [ ] T011 [P3] [US-3] **Rolling‑origin out‑of‑sample forecast**  
  - Hold out the most recent 8 quarters, then iteratively expand the training window, refit the selected model, and forecast the hold‑out period.  
  - Compute RMSE and MAE for each horizon and aggregate into `results/forecast_validation.json`.  
  - **Verification**: The JSON must contain keys `rmse`, `mae`, `average_rmse`, `average_mae`; values must be numeric.

---

## Phase 6 – Recession metadata, change‑point detection, & visualisation  

- [ ] T012 [P3] [US-3] **Download and store official NBER recession dates**  
  - Retrieve `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/datasets/nber-business-cycle-dating/master/data/nber-cycles.csv` — HTTP 404] and convert to JSON `data/metadata/recession_periods.json` with fields `start_date`, `end_date`, `label`.  
  - **Verification**: The JSON file must contain at least three recession periods and be valid JSON.

- [ ] T013 [P3] [US-3] **PELT change‑point detection on sentiment ILR components**  
  - Run `ruptures` with BIC penalty and minimum segment length = 2 quarters on `sentiment_ilr_1` and `sentiment_ilr_2`.  
  - Compute the proportion of detected breakpoints that fall within ±1 quarter of any NBER recession start or end; require ≥ 80 % (SC‑014).  
  - Output `results/pelt_breakpoints.json` containing breakpoints and the alignment metric.  
  - **Verification**: JSON must include `breakpoints` (list of dates) and `alignment_proportion` ≥ 0.80.

- [ ] T014 [P3] [US-3] **Generate all required visual artefacts**  
  - Time‑series plot of sentiment ILR components and macro variables with NBER recession shading (`outputs/figures/time_series.png`).  
  - Impulse‑response function plots for each VAR/VECM coefficient (`outputs/figures/irf_*.png`).  
  - Cross‑correlation heatmap between sentiment and each macro series (`outputs/figures/cross_corr_heatmap.png`).  
  - Save each figure as both PNG **and** PDF.  
  - **Verification**: The `outputs/figures/` directory must contain the listed files; each file size > 5 KB.

---

## Phase 7 – Reproducible notebook & project hand‑off  

- [ ] T015 [P3] [US-3] **Assemble a fully reproducible Jupyter notebook**  
  - `notebooks/sentiment_drift_analysis.ipynb` must sequentially execute every script from T002 through T014, display all figures, and embed a narrative discussion of results, including the disclaimer from FR‑019 that Granger causality indicates predictive precedence only.  
  - Export the notebook to HTML (`outputs/report.html`) and PDF (`outputs/report.pdf`).  
  - **Verification**: Running `jupyter nbconvert --to notebook --execute notebooks/sentiment_drift_analysis.ipynb` must complete without errors; the exported PDF must be non‑empty and contain all figure captions.

- [ ] T016 [P3] [US-3] **Provide quick‑start script and integration test**  
  - `scripts/quickstart.sh` creates a virtual environment, installs `requirements.txt`, runs the notebook, and then checks for the presence of the key artefacts: `data/processed/aligned_quarterly.csv`, `results/model_stats.json`, `results/bootstrap_validation.json`, `outputs/report.pdf`, and all figure files.  
  - Add `tests/integration/test_quickstart.sh` that invokes `quickstart.sh` and asserts each artefact exists and matches its SHA‑256 checksum recorded in `data/checksums.json`.  
  - **Verification**: The integration test must exit with status 0 on a clean run.

- [ ] T019 [P1] [US-2] **Set and record a fixed random seed for all stochastic procedures**  
  - Define a project‑wide seed (e.g., `12345`) in a constants module `code/constants.py`.  
  - Ensure all bootstrap, sensitivity, and any randomised modeling steps import this seed.  
  - Record the seed value in `outputs/model_results.json` under the field `random_seed`.  
  - **Verification**: The seed value appears in `model_results.json` and all stochastic scripts reference `code/constants.py`.

- [ ] T021 [P1] [US-1] **Compute SHA‑256 hashes for all generated artifacts and update project state**  
  - After each major phase, compute SHA‑256 hashes for new files and write them to `data/checksums.json`.  
  - Update `state/projects/PROJ-069-statistical-analysis-of-sentiment-drift-.yaml` `artifact_hashes` map with the new hashes (this file is managed by the platform; the task writes the updated content).  
  - **Verification**: `data/checksums.json` contains entries for every artifact listed in the verification mapping; the state YAML reflects the same hashes.

---

### Verification mapping (summary)

| Spec requirement | Task(s) fulfilling it |
|------------------|------------------------|
| FR‑001, FR‑002, FR‑015, FR‑018 | T002, T003 |
| FR‑010a, FR‑011 | T005, T006 |
| FR‑017 | T005 (imputation comparison) |
| FR‑003, FR‑009, FR‑013, FR‑021 | T007 |
| FR‑004, FR‑020 | T007 (VIF) & T008 (Granger) |
| FR‑014 | T012, T013 |
| FR‑022 | T009 (with convergence) |
| FR‑012 | T010 |
| FR‑006 | T011 |
| FR‑005, FR‑007 | T014, T015 |
| FR‑019 | T015 (disclaimer) |
| SC‑001 … SC‑014 | Covered by the corresponding validation tasks (T007‑T014) |
| SC‑003 (reproducibility) | T015, T016, T019 |
| SC‑002 (data completeness) | T002, T003, T005, T006, T020 |
| SC‑014 (breakpoint‑recession metric) | T013 |
| Constitution Principles I, III, V, VI, VII | T001, T002, T003, T005, T007, T019, T021 |

---  

*All tasks remain unchecked (`- [ ]`) until their artefacts are produced and the verification steps succeed. Once a task is completed, the box should be ticked.*  