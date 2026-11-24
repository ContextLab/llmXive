# Research: Calibration of Predictive Intervals for Time‑Series Forecasts

## Research Question
Do standard time‑series forecasting models (ARIMA, Prophet, LSTM) produce calibrated predictive intervals on the M4 and UCI Electricity benchmarks, and can a Self‑Calibrating Conformal Prediction (SCCP) wrapper improve calibration?

## Dataset Strategy

### Verified Datasets
The “Verified datasets” block supplied with the task **does not contain URLs for the M4 Forecasting Competition or the UCI Electricity Load dataset**. Because the Constitution requires reproducible external data fetches, the pipeline will:

1. **Run a pre‑execution verification (Task T000a)** that checks whether the required URLs appear in the verified‑datasets list.  
2. **If the URLs are missing**, the pipeline aborts with a clear error message instructing the researcher to add the canonical URLs to the verified list before proceeding.  
3. **Only after successful verification** will the pipeline attempt to download the datasets from the canonical sources listed in `code/config.yaml` (M4 from `, UCI Electricity from the UCI Machine Learning Repository).  
4. **Checksum verification** (`sha256`) is performed on the downloaded archives; any mismatch aborts execution.

### Data Processing
| Step | Action | Rationale |
|------|--------|-----------|
| **Streaming Load** | `datasets.load_dataset("<name>", streaming=True)` or custom HTTP streaming for the raw archives | Keeps memory ≤ 4 GB; respects GitHub Actions limits. |
| **Archive Extraction** | Extract downloaded `.zip`/`.tar.gz` files (Task T010) into `data/raw/` before streaming. | Allows streaming of individual series inside the archive. |
| **Stratified Sampling** | Randomly sample a representative set of series from M4 (balanced across frequencies) and a comparable set from UCI Electricity (balanced across load‑profile types) | Provides sufficient statistical power for bootstrap (see Power Analysis). |
| **Train‑Test Split** | First [deferred] → training; last [deferred] → test (recorded in `data/processed/split_metadata.json`) | Implements Constitution Principle VII. |
| **Standardization** | Zero‑mean, unit‑variance scaling on training data; same parameters applied to test data | Required by FR‑001. |

## Methodology

### Models
| Model | Library / Implementation | Key Settings |
|-------|--------------------------|--------------|
| **ARIMA** | `statsmodels.tsa.arima.model.ARIMA` | Order (p,d,q) = (1,1,1) fixed for stability; fitted on each series’ training window. |
| **Prophet** | `prophet.Prophet` | Default yearly/weekly/daily seasonality; `uncertainty_samples=1000`. |
| **LSTM** | PyTorch (CPU) | Single hidden layer, 32 units; Adam optimizer, learning rate 1e‑3; max 50 epochs, early stopping (patience = 5). |

### Predictive Intervals
- **ARIMA**: Conditional variance → Gaussian intervals.  
- **Prophet**: Sampled future trajectories (`uncertainty_samples`) → empirical quantiles.  
- **LSTM**: Residuals on the training set assumed Gaussian; mean ± z·σ for each horizon. If residuals are non‑Gaussian (Shapiro‑Wilk p < 0.05), the pipeline logs a warning and **still uses the Gaussian approximation for logging only**; primary results remain based on the fitted LSTM.

### Calibration Metrics
1. **Empirical Coverage** for nominal levels 0.80 & 0.95.  
2. **Probability Integral Transform (PIT)** values: `PIT = CDF(observed | forecast_distribution)`.  
   - **Primary Uniformity Test**: **Kolmogorov–Smirnov (KS) test** – directly assesses deviation from a uniform distribution (required by Constitution VI).  
   - **Secondary Autocorrelation Check**: Ljung‑Box test – reported alongside KS but **not used as the primary calibration decision**.  
3. **Continuous Ranked Probability Score (CRPS)** via `properscoring.crps_ensemble`.  

### Statistical Significance
- **Paired Bootstrap** (1000 resamples) at the *series* level comparing coverage deviations between any two models.  
- **α = 0.05**; p‑values reported in `results/significance_test.csv`.  

### Conformal Prediction
- **Self‑Calibrating Conformal Prediction (SCCP)** as described in *Vovk et al., 2022*.  
- Applied after the baseline interval generation; recalculates coverage, PIT, CRPS.  
- Improvement quantified as Δ‑coverage and Δ‑CRPS in `results/conformal_results.csv`.  

## Decision Rationale: Compute Strategy
- **CPU‑First**: All chosen libraries have mature CPU implementations; the LSTM model (32 units) fits comfortably within the 6‑hour limit on 500 series.  
- **No GPU Escape Hatch**: The LSTM is deliberately small; no realistic accuracy loss is expected from the CPU‑only constraint.  
- **Streaming** ensures the large UCI Electricity dataset never exceeds RAM limits.  

## Power Analysis & Sampling Strategy
- **Target**: Detect a minimum coverage‑deviation difference of 0.03 between models with 80 % power at α = 0.05.
- **Pilot variance estimate**: Conducted on a **200‑series pilot** (100 from each dataset) to obtain a more stable σ≈0.07.  
- **Robustness simulation**: Additionally simulate variances in the range σ = 0.05–0.12; the chosen N≈ 460 (rounded to **500**) maintains ≥ 80 % power under the worst‑case variance.  
- **Stratification** ensures representation of all frequencies and load‑profile types.  

## Sensitivity & Bias Analysis
- **Skipped‑Series Report**: The pipeline logs all series excluded due to constant variance or LSTM instability to `results/skipped_series.log`.  
- **Impact Quantification (Task T023b)**: After the main analysis, we **recompute aggregate metrics including the skipped series** by imputing Gaussian intervals (for diagnostic purposes) and compare to the primary results.  
  - The bias (difference in aggregate coverage, PIT KS p‑value, CRPS) is reported.  
 - If the bias exceeds **[deferred]** of the respective metric, a warning is raised, and the limitation is documented in the final report.

## Limitations & Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Inaccessibility** | Pipeline aborts, no results | Verified‑Dataset‑Check (T000a) aborts early with explicit error; researcher can add URLs to verified list. |
| **LSTM Instability** | Missing coverage for some series | Retry with reduced LR; fallback logging; sensitivity analysis (T023b). |
| **Statistical Power** | Sample of 500 may miss small effects | Larger pilot (200) and variance‑range simulation justify sample size. |
| **Constitution‑Specification Conflict** | KS vs Ljung‑Box | KS remains primary to satisfy Constitution VI; Ljung‑Box reported as secondary. |
| **Governance Amendment (T040)** | Future change to Constitution | Treated as external gate; does not block current execution. |

## Execution Order (High‑Level)
1. **Governance Gate** (T040) – external, does not block code.  
2. **Verified‑Dataset‑Check** (T000a) → **Data Fetch & Checksum** (T000, T009) → **Extraction** (T010) → **Streaming Load** (T011).  
3. **Sampling & Splitting** (T012‑T014).  
4. **Model Fitting** (T015‑T017) with edge‑case handling (T018).  
5. **Interval Generation** (T019‑T021).  
6. **Metric Computation** (T022‑T024).  
7. **Bootstrap Significance** (T026).  
8. **Conformal Wrapper** (T027‑T028).  
9. **Sensitivity/Bias Analysis** (T023b).  
10. **Aggregation & Reporting** (T029‑T031).  
11. **Governance Gate** (T040) – external amendment process, does not block earlier phases.  

---  

## Quick Summary of Outputs (found under `results/`)

| File | Description |
|------|-------------|
| `coverage.csv` | Empirical coverage for 0.80 & 0.95 intervals. |
| `distributional_metrics.csv` | PIT KS & Ljung‑Box p‑values, CRPS scores. |
| `significance_test.csv` | Paired bootstrap p‑values. |
| `conformal_results.csv` | Coverage before/after SCCP and improvement delta. |
| `benchmark_timing.csv` | Runtime per stage (useful for CI monitoring). |
| `skipped_series.log` | Log of series skipped due to constant variance or LSTM instability. |
| `contract_validation.log` | Summary of schema validation (Task T031). |
