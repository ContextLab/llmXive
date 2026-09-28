# Research: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Summary of Research

This research investigates the relationship between the volume of negative news publications and population-level anticipatory anxiety. The study utilizes aggregate news volume as a proxy for "news exposure" and search trend volume for "anticipatory anxiety." The analysis focuses on time-series correlation, cointegration, and Granger causality to determine if news volume predicts subsequent anxiety trends. Crucially, the study acknowledges the observational nature of the data and frames results as predictive associations rather than causal claims.

## Dataset Strategy

### Verified Datasets

The following datasets are the primary sources for this analysis. They are selected based on their public availability and programmatic accessibility, ensuring reproducibility on a CI runner.

| Dataset Name | Description | Source URL | Access Method |
|:--- |:--- |:--- |:--- |
| **GDELT 2.0 GKG 2.0** | Global news events with sentiment scores and event counts. Used for `EventCount` of negative sentiment events. | ` (AWS S3 Public Bucket) | `s3fs` / `wget` bulk download |
| **Google Trends** | Relative search interest for keywords related to anxiety. | ` | `pytrends` library (Session-based) |

### Data Acquisition Plan

1. **GDELT Data**:
 * **Strategy**: Bulk download of GDELT 2.0 GKG 2.0 files from the public AWS S3 bucket for the range [2020-01-01, 2023-12-31].
 * **Query**: Filter for `EventCount` where `AvgTone` < 0.
 * **Frequency**: Daily aggregation.
 * **Validation**: Check for non-empty rows and date continuity.
2. **Google Trends Data**:
 * **Keywords**: "anticipatory anxiety", "worry about future".
 * **Fallback Keywords**: "stress about future", "pandemic fear" (if primary keywords yield insufficient volume).
 * **Method**: Fetch daily time-series data.
 * **Keyword Stability Check**: Verify that selected keywords yield non-zero data for >5% of the time range. If a keyword fails, switch to the next fallback. This replaces the impossible "pilot validation against a known baseline" with an empirical volume check and literature-based construct validity.
 * **Literature Validation**: The choice of keywords is supported by literature (e.g., *Salathé et al., 2012*) which validates Google Trends search volume as a proxy for public concern/anxiety.

### Missing Data Handling

* **Gaps**: If a specific day has zero events in GDELT, it is recorded as `0` (valid zero).
* **Nulls**: If the API returns a null/missing value for a day, linear interpolation is applied **only** to non-zero gaps. Zero-event days are preserved.
* **Threshold**: If data completeness (valid days / total days) < 95% after interpolation, the pipeline exits with an error (SC-001).

## Methodological Rigor

### Statistical Methods

1. **Stationarity Check (ADF Test)**:
 * **Protocol**:
 1. **Seasonal Differencing**: Apply first-order differencing with lag=7 to address weekly news cycles.
 2. **ADF Test**: Test for stationarity.
 3. **STL Decomposition**: If non-stationary, apply STL (Seasonal-Trend decomposition using Loess) to remove trend and seasonality.
 4. **Simple Differencing**: If STL fails, apply simple first-order differencing.
 * **Threshold**: p < 0.05 required for stationarity.
 * **Action**: Document the number of differences and method applied.

2. **Cointegration & ECM**:
 * **Check**: Test if the original (non-differenced) series are cointegrated (Engle-Granger or Johansen).
 * **Logic**:
 * **If Cointegrated**: The relationship exists in levels. Use an **Error Correction Model (ECM)** to capture both short-term dynamics and long-run equilibrium.
 * **If Not Cointegrated**: Proceed with differenced series for Granger Causality.
 * **Rationale**: This prevents "blind differencing" which destroys long-run level information if a true cointegrating relationship exists.

3. **Correlation Analysis**:
 * **Metrics**: Pearson (linear) and Spearman (monotonic) correlation coefficients.
 * **Significance**: p-values calculated.

4. **Granger Causality**:
 * **Method**: Vector Autoregression (VAR) based Granger causality test.
 * **Lag Windows**: 1, 2, 3, 7, 14 days.
 * **Interpretation**: Framed as "predictive power" rather than causality.
 * **Correction**: **Holm-Bonferroni correction** applied for multiple comparisons (5 tests). This is more appropriate than Bonferroni for dependent (nested) hypotheses. Adjusted alpha is calculated step-down.

5. **Sensitivity Analysis**:
 * Sweep lag windows to report stability of significance.

6. **Variance Stability**:
 * **ARCH-LM Test**: Perform Autoregressive Conditional Heteroskedasticity Lagrange Multiplier test on residuals to check for stable variance.

### Statistical Rigor Checklist

* **Multiple Comparison Correction**: **Yes**, Holm-Bonferroni correction applied to Granger causality results across 5 lag windows.
* **Sample Size/Power**: The dataset covers a multi-year period spanning approximately four years. This is sufficient for time-series analysis with 14 lags (N >> max lag). Power limitation is acknowledged if the effective sample size drops significantly after differencing.
* **Causal Inference**: **No causal claims**. The study is observational. Results are framed as "predictive associations" due to lack of randomization.
* **Measurement Validity**: GDELT `EventCount` is a validated proxy for news volume. Google Trends data is a validated proxy for public concern/anxiety (cited in literature, e.g., *Salathé et al., 2012*).
* **Collinearity**: Not applicable for simple bivariate analysis, but if covariates are added later, Variance Inflation Factor (VIF) will be checked.
* **Construct Validity**: Acknowledged gap between GDELT "EventCount" and psychological "negativity". The analysis measures "aggregate negative event volume" as a proxy.

### Confounding & Interpretation

* **Information Exposure Confound**: High news volume may cause high search volume simply because people search for what they read (information exposure). The analysis risks validating a tautology: "More news coverage leads to more news-related searches."
* **Mitigation**: Results are strictly framed as "predictive associations" and "news volume impact on search trends," not direct psychological causation. The study does not claim to measure the internal state of "anticipatory anxiety" directly, but rather the population-level search behavior associated with it.

## Compute Feasibility

* **CPU-First**: All operations (fetching, pandas manipulation, statsmodels, arch) are CPU-bound and efficient.
* **Memory**: The dataset (of moderate size) fits easily in RAM.
* **Time**: Estimated runtime < 1 hour on a 2-core CPU.
* **GPU**: Not required. No deep learning models are used.

## Decision/Rationale

* **Why GDELT S3?** It provides the only global, daily, programmatic time-series of news volume with sentiment scoring. Bulk download avoids API rate limits.
* **Why Google Trends?** It is the most accessible proxy for population-level anxiety search behavior.
* **Why CPU?** The statistical methods (correlation, Granger, ECM) do not require GPU acceleration.
* **Why Holm-Bonferroni?** To control the family-wise error rate when testing 5 dependent lag hypotheses.
* **Why STL/Seasonal Diff?** To handle weekly news cycles that simple differencing misses.
* **Why Cointegration/ECM?** To preserve long-run level relationships if they exist, avoiding the destruction of signal by blind differencing.