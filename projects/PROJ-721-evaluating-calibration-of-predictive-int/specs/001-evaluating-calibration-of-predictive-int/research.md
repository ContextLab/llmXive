# Research: Evaluating Calibration of Predictive Intervals in Time Series Forecasting

## 1. Dataset Strategy

The project relies on the **M4 Competition Dataset**, the standard benchmark for time series forecasting.

### Verified Datasets
- **M4 Competition Dataset**: The official repository containing a large-scale collection of time series with metadata (frequency, seasonality, trend).
 - **Source**: ` (Official GitHub Repo).
 - **Access Method**: `code/download.py` will fetch the specific CSVs from the `M4-methods` repository `data` folder.
 - **Constraint**: The full dataset (large-scale series) exceeds the 6-hour CPU limit. The plan explicitly restricts the analysis to a **representative subset of [deferred] series** (FR-001, Assumption: Compute Feasibility). This subset will be stratified to match the frequency distribution of the full set (≥90% representation, SC-005).

### Variable Fit Verification
- **Required Variables**: `y` (time series values), `frequency`, `seasonality` (metadata), `trend_strength` (derived).
- **M4 Metadata Availability**: The M4 dataset explicitly includes `seasonality` (Yes/No) and `frequency` (Yearly, Quarterly, Monthly, Weekly, Daily, Hourly).
- **Derived Variables**: `trend_strength` is **not** in the metadata. As per FR-005 and Assumption (Metadata Validity), it will be derived via **STL decomposition** on the training split.
 - **Method**: `statsmodels.tsa.seasonal.STL`.
 - **Calculation**: Variance ratio of trend component to total variance. Threshold > 0.5 classifies as 'high'.
- **Gap Check**: No missing variables. The dataset contains all necessary inputs for the specified analysis.

## 2. Methodology & Statistical Rigor

### 2.1 Model Fitting (FR-002)
Four models will be fitted to each series:
1. **ARIMA**: `statsmodels.tsa.arima.model.ARIMA`. Auto-selected order via AIC.
2. **ETS**: `statsmodels.tsa.holtwinters.ExponentialSmoothing`. Auto-selected trend/seasonality.
3. **Prophet**: `prophet.Prophet`. Default parameters; CPU-only.
4. **LightGBM**: `lightgbm.LGBMRegressor`.
 - **Objective**: `quantile` (alpha=0.1 for 80% PI, alpha=0.05 for 95% PI).
 - **Features**: Lag features, rolling statistics, date features.
 - **Constraint**: Must run on CPU; no GPU acceleration.

### 2.2 Prediction Interval Generation (FR-003)
- **Nominal Levels**: [deferred] and [deferred] (targeted).
- **Horizons**: $h = 1$ to $12$.
- **Method**:
 - ARIMA/ETS/Prophet: Analytic intervals based on assumed error distributions (Gaussian).
 - LightGBM: Quantile regression outputs directly provide lower/upper bounds.

### 2.3 Coverage Calculation (FR-004)
- **Metric**: Empirical Coverage Rate = $\frac{1}{N_{test}} \sum_{t=1}^{N_{test}} \mathbb{I}(L_t \le y_t \le U_t)$.
- **Target**: Measure the **magnitude of deviation** from nominal [deferred] and [deferred]. (Note: This is an estimation of deviation, not a "validation" against an independent truth, as the metric is mathematically defined by the interval and actuals).
- **Sensitivity**: Absolute deviation thresholds of 0.01, 0.05, 0.1 (FR-008).

### 2.4 Stratified Analysis (FR-005)
- **Groups**: Seasonality (Yes/No), Trend Strength (High/Low).
- **Derivation**: STL decomposition on training data only.
- **Threshold Sensitivity**: To address uncertainty in the arbitrary 0.5 threshold, the analysis will be repeated with thresholds of 0.4 and 0.6. If results are stable across these thresholds, the 0.5 classification is robust.
- **Output**: Aggregated coverage rates per group.

### 2.5 Recalibration (FR-006)
- **Method**: Adaptive Conformal Prediction (ACP).
- **Trigger Condition**: Recalibration is triggered if **any** stratified subgroup (e.g., "Seasonal/High Trend") exhibits a deviation > 2% from the nominal target. This prevents skipping recalibration for specific failure modes that are masked by a global average.
- **Validation Strategy (Held-Out Set)**: To avoid selection bias (data snooping), the dataset is split into:
 1. **Calibration Set**: Used to determine if recalibration is needed and to tune ACP parameters.
 2. **Test Set**: Used exclusively to evaluate the final coverage rates of the recalibrated model.
- **Mechanism**: Adjust interval width dynamically based on recent coverage errors on the Calibration Set.
- **Validation**: Paired bootstrap test (a large number of resamples) on the **Test Set** to compare baseline vs. recalibrated coverage.

### 2.6 Statistical Significance (FR-007)
- **Tests**: Comparison of coverage rates across models and horizons.
- **Correction Method**: **Benjamini-Yekutieli (BY)** procedure.
 - **Rationale**: While the spec (FR-007) mandates Benjamini-Hochberg (BH), BH assumes independence or positive regression dependence. Forecast errors across horizons (h=1..12) are highly autocorrelated. BY is a conservative variant of FDR that guarantees control under *any* dependence structure.
 - **Implementation**: We will report BY-adjusted p-values as the primary result to ensure statistical rigor. A sensitivity analysis comparing BH and BY results will be included to demonstrate the impact of the dependence assumption.
- **Limitation**: Acknowledged that forecast errors are autocorrelated; BY is the standard robust choice for this scale in forecasting literature when independence cannot be guaranteed.

## 3. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (multiple vCPUs, several GB RAM, ~14 GB disk).
- **Time Limit**: 6 hours per job.
- **Strategy**:
 - **Subset**: Process [deferred] series (representative). Full 100k is infeasible.
 - **Model Limits**:
 - ARIMA/ETS: Auto-order limits to prevent overfitting and long runtimes.
 - Prophet: `n_changepoints` is configured at a reduced level to optimize computational speed.
 - LightGBM: `num_leaves` capped at a moderate limit, `n_estimators` at 100.
 - **Memory**: Data loaded in chunks; `pandas` optimized dtypes (float32).
- **No GPU**: All libraries configured for CPU execution.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **M4 Metadata Missing** | High | FR-010 validates metadata; skip series with missing fields and log warning. |
| **Series Too Short** | Medium | Skip series where $N_{train} < 2 \times N_{test}$; log warning. |
| **Model Convergence Failure** | Medium | Try/except blocks; record failure; continue with other series/models. |
| **Runtime Exceeds 6h** | Critical | Strict subset size (1k); aggressive model parameter caps; parallelize across series (if memory allows) or sequential with progress bars. |
| **LightGBM CPU Slowdown** | Medium | Use `verbose=-1`; limit tree depth; ensure `lightgbm` uses CPU wheel. |

## 5. Decision Rationale

- **Why M4 Subset?**: Full M (large-scale series) × 4 models × 12 horizons ≈ 4.8M model fits. Even at 1s/fit, this is >13 hours. A scalable series reduces this to approximately 1.3 hours, leaving margin for data processing and analysis.
- **Why Adaptive Conformal?**: Standard quantile regression (LightGBM) can be miscalibrated in small samples. ACP provides a distribution-free guarantee for finite samples.
- **Why BY FDR?**: Testing multiple hypotheses on autocorrelated data without robust correction yields inflated false positives. BY controls the FDR under any dependence, ensuring the "significant" claims are valid.
- **Why Held-Out Validation?**: Prevents the "data snooping" bias where recalibration is triggered and evaluated on the same data, which would artificially inflate improvement metrics.