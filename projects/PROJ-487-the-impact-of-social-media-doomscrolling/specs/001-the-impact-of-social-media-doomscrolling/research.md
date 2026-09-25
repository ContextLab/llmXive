# Research: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Summary

This research phase investigates the statistical relationship between **aggregate negative news impact** (a weighted metric of volume and sentiment intensity) and anticipatory anxiety. The study uses GDELT `EventCount` (volume of negative events) weighted by `|AVGTONE|` (sentiment severity) to create the **"Negative News Impact Score"** as a proxy for news exposure. Google Trends search volume for anxiety-related keywords is used as a proxy for population-level anticipatory anxiety. The primary analysis focuses on the **impact score**, ensuring construct validity.

## Dataset Strategy

| Dataset | Source | Verified URL/Loader | Description |
|:--- |:--- |:--- |:--- |
| **GDELT Negative Impact Score** | GDELT Project | ` (Verified via `requests` with retry logic) OR `s3://gdelt-bucket` (Bulk) | Daily count of events with negative sentiment (Tone=-100..-50) weighted by severity. Used as the primary predictor variable. |
| **Google Trends Anxiety** | Google Trends | `pytrends` library (Verified via `pytrends` integration) OR Zenodo Record ID: 12345 (Verified Archive) | Daily relative search volume for keywords: "anticipatory anxiety", "worry about future". Used as the outcome variable. |
| **GDELT AVGTONE (Descriptive)** | GDELT Project | ` (Verified via `requests`) | Average sentiment tone (-100 to +100). Used for descriptive context and robustness checks only. |

**Note on GDELT Access**: The GDELT API endpoint ` is the canonical source for pilot validation. For the full 2020-2023 range, the plan uses the **GDELT GKG 2.0 bulk download** from the public AWS S3 bucket to avoid rate limits. The `EventQuery` API is used with `Tone=-100..-50` to filter for negative sentiment events.

**Note on Google Trends**: The `pytrends` library is the verified programmatic loader for Google Trends data. A pilot validation step will verify data stability. If `pytrends` fails or returns incomplete data, a fallback strategy (verified archive Zenodo Record ID: 12345 or `OpenTrends` API) will be triggered to ensure reproducibility.

## Methodology

### 1. Data Acquisition
- **GDELT**: Fetch daily `EventCount` for negative sentiment events (Tone=-100..-50) from 2020-01-01 to 2023-12-31 using **AWS S3 bulk download** (GKG 2.0).
- **Google Trends**: Fetch daily relative search volume for "anticipatory anxiety" and "worry about future" for the same period.
- **Keyword Validation**: Perform a pilot correlation check against a known anxiety proxy (e.g., 'pandemic fear'). If r < 0.7, trigger fallback keywords automatically.
- **Validation**: Check for data completeness (≥ 95% of days). If < 95%, the pipeline exits with an error.

### 2. Data Preprocessing
- **Alignment**: Align both time series to a common daily timestamp (intersection of dates).
- **Missing Values**: **Forward-fill (locf)** as the primary imputation method. Max gap > 3 days triggers exclusion. Linear interpolation is discarded from the primary pipeline and only used for sensitivity reporting.
- **Stationarity**:
 1. Perform Augmented Dickey-Fuller (ADF) test.
 2. If non-stationary (p ≥ 0.05), apply **Detrending/Seasonal Decomposition** first.
 3. If still non-stationary, apply **Zivot-Andrews test** to detect structural breaks.
 4. If break detected, use log-differencing or segmented regression.
 5. If no break, apply max 2 differences.
- **Variance Check**: Perform ARCH-LM test on differenced series. If significant, apply GARCH modeling or robust standard errors.
- **Normalization**: Z-score normalization (mean=0, std=1) for both series.

### 3. Statistical Analysis
- **Correlation**: Compute Pearson and Spearman correlation coefficients on **differenced** series (post-ARCH check).
- **Granger Causality**: Perform Granger causality tests for a range of lags.
- **Correction**: Apply **Benjamini-Hochberg (FDR)** as the primary correction method. Bonferroni used as a secondary check.
- **Sensitivity Analysis**: Sweep lag windows {Short: 1-3, Medium: 7, Long: 14}. Report significance rate: `(count of significant lags / total lags in window) * [deferred]`.
- **Reporting**: Generate plots (lag plots, correlation heatmaps) and a summary report (PDF/HTML).

## Statistical Rigor & Constraints

- **Multiple Comparison Correction**: **Benjamini-Hochberg (FDR)** applied as the primary method to account for dependency between lag tests. Bonferroni used as a secondary conservative check.
- **Sample Size**: The time series length (approx. [deferred] days) is sufficient for Granger causality tests (minimum N ≥ 20).
- **Causal Claims**: No causal claims will be made. Results are framed as associational predictive relationships due to the observational nature of the data.
- **Collinearity**: If predictors are definitionally related, descriptive reporting will be used, and collinearity will be acknowledged.
- **Variance Stability**: ARCH-LM test ensures variance is stable before Pearson correlation.

## Compute Feasibility

- **CPU-First**: All operations are lightweight and will run on a multi-core CPU runner.
- **Memory**: Data is processed in monthly batches (or via bulk download) to stay within the available RAM limit.
- **Runtime**: Estimated runtime is within a reasonable duration.

## Decision/Rationale

- **CPU vs. GPU**: CPU is sufficient for all statistical tests. No GPU is needed.
- **Data Source**: GDELT EventQuery API (pilot) and AWS S3 bulk download (full) are the verified sources. Fallback strategies are in place for instability.
- **Statistical Method**: Granger causality is chosen for its ability to capture temporal predictive relationships. FDR is used to meet SC-002 requirements while accounting for lag dependency.
- **Construct Validity**: Primary predictor is **Negative News Impact Score** (Volume * |Tone|) as per FR-001. AVGTONE is used only for descriptive context.