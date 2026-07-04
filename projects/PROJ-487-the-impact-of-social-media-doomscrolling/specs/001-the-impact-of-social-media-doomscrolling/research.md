# Research: The Impact of Social Media "Doomscrolling" on Anticipatory Anxiety

## Problem Statement Refinement

The user query asks about the relationship between "aggregate volume of negative news consumption on social media" and "anticipatory anxiety."
- **Constraint**: Direct API access to granular social media consumption volume (e.g., Twitter/X, Facebook usage logs) is unavailable to the public.
- **Proxy Strategy**: The spec (FR-001) explicitly defines `AVGTONE` from the GDELT Project as a proxy for the *intensity* of negative news exposure. This measures the average sentiment tone of global news articles.
- **Outcome**: "Anticipatory anxiety" is proxied by Google Trends search volume for terms like "anticipatory anxiety," "worry about future," and "future anxiety."

## Dataset Strategy

The following datasets are required. **Note**: The "Verified datasets" block provided in the prompt contains CSVs unrelated to this project. **No specific URL** for GDELT or Google Trends was provided in the input block. The plan proceeds by defining the **Canonical Data Accession** protocol to ensure reproducibility.

### 1. GDELT Global News Sentiment (Predictor)
- **Variable**: `AVGTONE` (Average Tone).
- **Range**: -100 (Very Negative) to +100 (Very Positive).
- **Canonical Source**: GDELT 2.0 Global Events Database.
- **Accession Protocol**: 
  - Archive: `GDELT 2.0 Global Events Database`
  - Field: `AVGTONE`
  - Query: `EventRootCode=NEWS` (or equivalent filter for news articles)
  - Time Range: 2020-01-01 to 2023-12-31
- **Status**: **NO VERIFIED URL IN INPUT BLOCK**.
- **Action**: The implementation will use the official GDELT API or archive download script. If the API is inaccessible on CI, the pipeline will fall back to a static sample CSV (checksummed) representing the expected schema.
- **Citation**: GDELT Project Documentation (General knowledge).

### 2. Google Trends Search Volume (Outcome)
- **Variable**: Relative search interest (0-100 scale).
- **Keywords**: "anticipatory anxiety", "worry about future", "future anxiety".
- **Canonical Source**: Google Trends API (via `pytrends`).
- **Accession Protocol**:
  - Geo: `US` (or global if specified, defaulting to US for consistency)
  - Category: `0` (All categories)
  - Time: `2020-01-01 2023-12-31`
- **Status**: **NO VERIFIED URL IN INPUT BLOCK**.
- **Action**: The implementation will use `pytrends` (unofficial API) to fetch data. If `pytrends` is unstable on CI, the pipeline will fall back to a static CSV placeholder.
- **Citation**: Google Trends Help (General knowledge).

### Dataset Fit Assessment
- **Predictor**: GDELT `AVGTONE` measures news sentiment, not *social media consumption volume*.
- **Gap**: The spec acknowledges this in FR-001: "GDELT AVGTONE measures... not direct social media consumption volume."
- **Mitigation**: The research question is reframed to "Impact of negative news sentiment intensity" rather than "social media volume." This aligns with the available data.
- **Verdict**: **Acceptable with caveats**. The plan proceeds with GDELT as the proxy for "doomscrolling intensity."

## Statistical Methodology

### 1. Stationarity Verification (Critical)
- **Method**: Augmented Dickey-Fuller (ADF) test (`statsmodels.tsa.stattools.adfuller`).
- **Procedure**: 
  - Test raw series for unit roots.
  - If p > 0.05 (non-stationary), apply first-order differencing (`diff()`).
  - Re-test differenced series.
- **Justification**: Granger causality is mathematically invalid on non-stationary time series (spurious regression). Z-scoring alone does not remove unit roots. Differencing ensures stationarity.

### 2. Correlation Analysis
- **Methods**: Pearson (linear) and Spearman (monotonic) correlation.
- **Justification**: Time-series data may not be normally distributed; Spearman provides robustness.
- **Multiple Comparisons**: Bonferroni applied if multiple keyword trends are tested separately.

### 3. Granger Causality (Multivariate)
- **Method**: `statsmodels.tsa.stattools.grangercausalitytests` with exogenous variables.
- **Lags**: 1, 2, 3 days.
- **Hypothesis**: Negative news sentiment (t) predicts anxiety search volume (t+lag).
- **Confounder Control**: 
  - **Problem**: Global events (e.g., pandemic onset) drive both news sentiment and anxiety, creating spurious correlation.
  - **Solution**: Create binary dummy variables for major global events (e.g., `is_pandemic`, `is_election`) derived from external calendars or GDELT metadata. Include these as exogenous regressors in the Granger model.
- **Correction**: **Holm-Bonferroni** correction for 3 dependent tests (lags 1, 2, 3). Bonferroni is too conservative for overlapping windows; Holm-Bonferroni maintains family-wise error control while reducing Type II error risk.
- **Assumption**: Observational data. **No causal claims** will be made. Results indicate *predictive* relationships only.

### 4. Sensitivity Analysis
- **Method**: Sweep lag windows {1, 2, 3}.
- **Metric**: Significance rate (p < 0.05) across lags.
- **Purpose**: Ensure results are not an artifact of a single arbitrary lag choice.

## Compute Feasibility

- **Hardware**: 2 CPU, 7 GB RAM.
- **Data Size**: [deferred] rows × 2 columns.
- **Library Overhead**: `pandas`, `numpy`, `statsmodels` are lightweight.
- **Conclusion**: Fully feasible. No GPU required.

## Limitations & Risks

1. **Proxy Validity**: GDELT sentiment is not a direct measure of social media usage.
2. **Confounding**: Despite dummy variables, unobserved confounders may exist.
3. **Data Availability**: GDELT and Google Trends APIs may have rate limits or require manual CSV export for historical data.
4. **Stationarity**: If differencing removes too much signal, the relationship may be obscured. The plan prioritizes statistical validity over signal retention.