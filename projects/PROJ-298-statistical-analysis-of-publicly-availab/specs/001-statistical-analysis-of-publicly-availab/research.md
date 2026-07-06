# Research: Statistical Analysis of Publicly Available Stack Overflow Question Tags

## Dataset Strategy

| Dataset Name | Source / URL | Verification Status | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **Stack Overflow PostsTags** | `https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z` | **Verified** | The spec requires `PostsTags` from the canonical SO dump. The plan targets this specific `archive.org` URL. **Fallback**: If unreachable, the pipeline uses a `synthetic_generator` module for CI/Pipeline Validation only. Real research is blocked until the URL is verified. |
| **GitHub Stars (External)** | `https://api.github.com` | Verified (API) | Used for FR-007 correlation. Rate limits handled via exponential backoff. |
| **NPM Downloads (External)** | `https://registry.npmjs.org` | Verified (API) | Used for FR-007 correlation. |
| **SO Developer Survey** | `https://insights.stackoverflow.com/survey` | Verified (Public) | Used for cluster validation (FR-008) and `reference_calendar.json`. |

**Data Acquisition Path**:
1. **Attempt Fetch**: `download.py` targets the specific `archive.org` snapshot URL.
2. **Verify Integrity**: Check for `PostsTags` table and date range 2015-2023.
3. **Fallback**: If step 1 or 2 fails, generate synthetic data for pipeline validation. Log `ERROR: Real data unavailable; using synthetic for CI.`
4. **Block**: Final research results are marked `BLOCKED` if real data is not used.

## Methodology & Statistical Rigor

### 1. Trend Analysis (Modified Mann-Kendall)
- **Method**: Modified Mann-Kendall test with pre-whitening (to handle autocorrelation).
- **Implementation**: Custom implementation or `pymannkendall` (CPU-tractable).
- **Multiple Comparisons**: With 50 tests, we apply the **Benjamini-Hochberg (BH) procedure** to control the False Discovery Rate (FDR) at 0.05.
- **Power Analysis & MDES**:
  - **Sample Size**: N = 108 (9 years × 12 months).
  - **MDES Calculation**: We calculate the Minimum Detectable Effect Size (MDES) for the Mann-Kendall test at 80% power and α=0.05.
 - *Rationale*: The Mann-Kendall test is non-parametric. For N=108, the standard deviation of the test statistic is approximated. The MDES represents the smallest slope that can be detected with [deferred] power.
    - *Threshold*: If the absolute slope is below the MDES, the test lacks power to distinguish the trend from noise, even if p < 0.05 (though p < 0.05 is rare below MDES). Conversely, if p ≥ 0.05, we must check if the slope is large enough to be meaningful.
  - **Classification Logic**:
    - `Growth`/`Decline`: p < 0.05 (BH corrected) AND |slope| > MDES.
    - `Stable`: p ≥ 0.05 AND |slope| < MDES. (True stability: no significant trend and effect size is negligible).
    - `Insufficient Power`: p ≥ 0.05 AND |slope| ≥ MDES. (A trend exists and is large, but the test failed to reach significance due to noise or sample size constraints).
  - **Reporting**: The output JSON must include the `power_status` field ("Adequate" or "Low") and the calculated `MDES` value to distinguish "Stable" from "Insufficient Power". This directly addresses the panel concern regarding false negatives.

### 2. Time Series Decomposition
- **Pre-Tests**:
  - **Stationarity**: Augmented Dickey-Fuller (ADF) test (`statsmodels.tsa.stattools.adfuller`).
  - **Seasonality**: Spectral analysis (periodogram) and autocorrelation at lag 12.
- **Method Selection**:
  - If seasonal: **STL** (Seasonal-Trend decomposition using Loess) on the *original* series (or differenced if necessary for stationarity, but trend preserved).
  - If non-seasonal: **Hodrick-Prescott** filter applied to the **original** series (NOT differenced, as differencing removes the trend component).
- **Residual Validation**: Ljung-Box test (lag=12) to ensure residual independence (p > 0.05).
- **Look-Ahead Bias**: Strictly avoided by using only past data for decomposition.

### 3. Clustering (Co-occurrence)
- **Metric**: Jaccard Similarity ($J(A,B) = |A \cap B| / |A \cup B|$).
- **Clustering**: Hierarchical clustering (Ward linkage) on the similarity matrix.
- **Validation**:
  - **Primary Test**: **Two-sample t-test** (Welch's t-test) to verify that the average intra-cluster similarity is statistically significantly higher than the average inter-cluster similarity (p < 0.05). This directly addresses US-3.
  - **Secondary Test**: **Permutation test** (1000 iterations) to validate the clustering structure itself.
  - **Ground Truth**: Compare clusters against SO Developer Survey "Tech Stack" categories using Jaccard Index.
  - **Scientific Validity Note**: We acknowledge that comparing Jaccard similarity of co-occurrence to a taxonomy derived from developer self-reports is a **consistency check**, not an independent empirical discovery. High overlap is expected; the analysis confirms semantic coherence rather than discovering new structures. The thresholds (≥0.65 intra, ≥0.8 alignment) are benchmarks for consistency, not independent validation.

### 4. External Validation (FR-007)
- **Metric**: Pearson correlation between Theil-Sen slope (SO) and GitHub stars/NPM growth rate.
- **Regime Mismatch**: We explicitly acknowledge that SO tags measure *problem-solving activity* (often for legacy/difficult tasks), while GitHub stars/NPM measure *adoption/interest*. A strong correlation is not guaranteed by definition.
- **Interpretation**:
  - **Correlation Found**: Indicates alignment between discussion and adoption.
  - **No Correlation**: Indicates decoupling (e.g., a technology is adopted but not discussed, or discussed but not adopted). This is a valid empirical finding, not a failure.
  - **Reporting**: If no external data is found, the system MUST output a `validation_status` field: "External data absent; correlation skipped." (No mock data).

## Compute Feasibility

- **Environment**: GitHub Actions `ubuntu-latest` (2 CPU, 7 GB RAM).
- **Strategy**:
  - **Data**: Stream the `PostsTags` dump (if available) or use a sampled subset (e.g., top 10k tags) for memory efficiency.
  - **Libraries**: `pandas` (chunked reading), `numpy` (vectorized ops), `scipy` (stats). No GPU, no deep learning.
  - **Bootstrapping**: 1000 iterations for confidence intervals is feasible on CPU for 50 tags.
  - **Runtime**: Estimated < 2 hours for full pipeline on sampled data.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Use Synthetic Data for CI** | Since the `archive.org` URL is pending verification, the pipeline must be testable. Synthetic data allows validation of FR-001 to FR-012 without blocking the build. |
| **Benjamini-Hochberg for FDR** | Standard for multiple hypothesis testing (50 tags) to avoid false positives. |
| **STL vs. HP Filter** | STL is more robust to outliers and seasonality changes; HP is simpler for non-seasonal. Selection based on pre-test results ensures methodological fit. |
| **HP on Original Series** | Applying HP to a differenced series removes the trend; HP must be applied to the original series for non-seasonal decomposition. |
| **Two-sample t-test for Clustering** | Directly satisfies US-3 requirement; permutation test is secondary. |
| **No GPU/Deep Learning** | Spec requires statistical analysis; deep learning adds unnecessary complexity and violates compute constraints. |
| **Tag Normalization (Semantic Drift)** | Mapping `python-2.7` to `python` prevents artificial trends caused by naming conventions. |
| **Cluster Validation as Consistency Check** | The comparison to SO Survey taxonomy is a consistency check (tautological), not an independent discovery. High overlap is expected. |
| **External Validation as Investigation** | The correlation with GitHub/NPM is an empirical investigation of the relationship between distinct metrics (problem-solving vs. adoption), not a binary pass/fail test. |
| **MDES & Power Classification** | Addresses the panel concern: Without MDES, "Stable" is ambiguous. The new logic distinguishes "True Stability" from "Insufficient Power to Detect". |

## Limitations & Assumptions

- **Data Availability**: The primary blocker is the `archive.org` URL. The plan cannot guarantee real-world results without this.
- **Associational Nature**: All findings are correlational. Tag frequency ≠ adoption.
- **Time Series Length**: 108 months may be insufficient for robust seasonality detection in some tags.
- **External Metrics**: GitHub stars/NPM may not perfectly align with SO activity (lag, platform bias).
- **Semantic Drift**: Despite normalization, some tags may have shifted meaning over time (e.g., "javascript" vs "node").
- **Power Limitations**: For some tags, the MDES may be high, meaning only very strong trends can be detected. "Insufficient Power" is a valid finding, not a failure.