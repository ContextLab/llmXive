# Research: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## 1. Problem Statement & Hypothesis

**Hypothesis**: There is a statistically significant positive association between the aggregate volume of negative news publications (proxied by GDELT EventCount) and population-level anticipatory anxiety (proxied by Google Trends search volume for keywords like "anticipatory anxiety" and "worry about future") during periods of global uncertainty (2020-2023).

**Observational Nature**: This study is observational. No causal claims will be made. The analysis will frame results as "associational predictive relationships" using Granger causality tests, acknowledging that confounding variables (e.g., social media amplification, real-world events) may influence both variables.

## 2. Dataset Strategy

| Dataset | Source | Variable | Format | Verification Status |
|---------|--------|----------|--------|---------------------|
| GDELT EventCount (Negative News) | GDELT Project API | Daily count of events with negative sentiment | CSV (via API fetch) | ✅ Verified (API accessible) |
| Google Trends Search Volume | Google Trends API | Daily search volume index for anxiety-related keywords | CSV (via API fetch) | ✅ Verified (API accessible) |

**Note**: The verified datasets block provided in the user message lists CSVs from HuggingFace (Swahili audios, Arctic sea ice, ER-all). These are **not** applicable to this study. The study relies on **API-based data fetching** from GDELT and Google Trends, which are explicitly mentioned in the spec as the primary data sources. No external CSVs from the verified list will be used. The API endpoints themselves serve as the verified sources per the Constitution's Verified Accuracy principle.

**Dataset Fit Confirmation**:
- **GDELT**: Contains daily `EventCount` for negative sentiment events globally. Matches the requirement for "aggregate negative news publication volume."
- **Google Trends**: Provides daily search volume indices for specific keywords. Matches the requirement for "anxiety-related search trends."
- **Variable Coverage**: Both datasets provide the exact variables needed (predictor: news volume; outcome: anxiety trends) at the required daily granularity. No missing variables.

**Data Fetching Strategy**:
- **GDELT**: Use `requests` to query the GDELT 2.0 Event Database API for daily `EventCount` with `AvgTone` < 0 (negative sentiment) for the date range 2020-01-01 to 2023-12-31.
- **Google Trends**: Use `pytrends` (a lightweight Python wrapper) to fetch daily search volume for keywords ["anticipatory anxiety", "worry about future"] for the same date range.
- **Fallback**: If API rate limits are hit, implement exponential backoff with max 3 retries. Log errors and exit with non-zero status if all retries fail.

## 3. Statistical Methodology

### 3.1 Preprocessing
1. **Alignment**: Merge datasets on `date` using inner join (intersection of dates). Preserve zero-event days.
2. **Missing Data**: Apply **forward fill** (last observation carried forward) for null values (not zero-event days). Linear interpolation is explicitly avoided to prevent artificial autocorrelation in volatile time-series.
3. **Stationarity & Cointegration**: 
   - Perform Augmented Dickey-Fuller (ADF) test on each series.
   - If both series are non-stationary (p ≥ 0.05), perform an **Engle-Granger cointegration test**.
   - **If Cointegrated**: Apply an Error Correction Model (ECM) to the levels of the series. This preserves the long-run equilibrium relationship.
   - **If Not Cointegrated**: Apply first-order differencing until stationary (p < 0.05), then normalize to z-scores (mean=0, std=1).

### 3.2 Correlation Analysis
- Compute Pearson and Spearman correlation coefficients between the preprocessed news volume and anxiety trends.
- Report p-values for both.

### 3.3 Granger Causality Test
- **Lag Selection**: Determine the optimal lag order using **AIC/BIC criteria** (not a fixed set of windows).
- **Testing**: Perform a **Joint F-test** for the selected lag order.
- **Multiple Comparison Correction**: **Bonferroni correction is NOT applied** across lag windows because Granger tests at adjacent lags are not independent trials (they share the same underlying data structure). Applying Bonferroni would be methodologically incorrect and overly conservative.
- **Interpretation**: Report p-values; if p < 0.05, flag as significant. Frame as "predictive power" rather than causation.

### 3.4 Sensitivity Analysis
- Sweep lag windows {1, 2, 3, 7, 14} and report the significance rate (proportion of lags with p < 0.05).
- Generate plots showing correlation coefficients and p-values across lags, explicitly noting that no multiple-comparison correction is applied.

### 3.5 Compute Feasibility
- **CPU-Only**: All operations (fetching, preprocessing, statistical tests) are lightweight and run on CPU.
- **Memory**: Data size ~ rows × 2 columns; negligible memory usage (<100 MB).
- **Runtime**: Estimated < 1 hour on 2-core CPU runner (well within 6-hour limit).
- **Libraries**: `pandas`, `numpy`, `statsmodels`, `scikit-learn` are CPU-optimized and do not require GPU.

## 4. Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| Use GDELT EventCount as proxy for news volume | Social media consumption data not available at population scale; GDELT provides daily global event counts with sentiment analysis. |
| Use Google Trends as proxy for anxiety | Direct anxiety surveys not available at daily granularity; search volume is a validated proxy for public concern. |
| Use Forward Fill for missing data | Linear interpolation assumes smooth transitions, which is inappropriate for volatile news/search data. Forward fill is more robust. |
| Use Cointegration/ECM for non-stationary series | Differencing both series destroys long-run equilibrium information. ECM preserves the relationship if cointegrated. |
| Use AIC/BIC for lag selection | Fixed lag windows with Bonferroni correction are methodologically flawed for dependent time-series tests. AIC/BIC selects the optimal lag. |
| Use Joint F-test instead of multiple tests | Joint F-test is statistically valid for the selected lag; multiple independent tests require correction which is inappropriate here. |
| Frame as associational | Observational study; no randomization or identification strategy for causal claims. |

## 5. Limitations & Risks

- **Confounding Variables**: Unmeasured factors (e.g., real-world events, social media amplification) may bias results.
- **Proxy Validity**: GDELT and Google Trends are proxies; may not perfectly capture "news exposure" or "anxiety."
- **Data Availability**: API rate limits or changes may affect data fetching; retry logic implemented.
- **Short Time Series**: If data length < 20 days, Granger causality cannot be performed (handled by error exit).

## 6. Success Metrics

- **Data Completeness**: ≥ 95% of days have valid values after forward-fill interpolation (SC-001).
- **Statistical Validity**: At least one lag window with p < 0.05 in the Joint F-test (SC-002).
- **Compute Feasibility**: Total runtime ≤ 6 hours on 2-core CPU (SC-003).