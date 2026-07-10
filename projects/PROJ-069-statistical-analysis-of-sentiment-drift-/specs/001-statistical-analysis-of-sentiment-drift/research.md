# Research: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

## Dataset Strategy

The analysis relies on two primary data sources: social media sentiment (via GDELT) and macroeconomic indicators (via FRED). Only the following verified sources are used, as per the project constraints. **Note**: The spec's FR-001 citation of `snap-cornell` is a static corpus without timestamps and is unusable for time-series analysis. The implementation uses GDELT to satisfy the *functional requirement* of historical sentiment time-series.

| Variable | Source Description | Verified URL / Loader | Load Strategy |
|----------|--------------------|----------------------|---------------|
| **Sentiment** | GDELT Global News Sentiment (Average Sentiment, Positive, Negative) | `gdelt-2` (via `pygdelt` or verified HuggingFace `gdelt-2` wrapper) | `pygdelt.GDelt().query(...)` or `load_dataset("gdelt-2")` |
| **GDP** | Monthly/Quarterly GDP growth rates | FRED API (`FRED/GDP`) | `fredapi.FRED(api_key=...)` (Primary); fallback to verified HF macro dataset if API fails. |
| **Unemployment** | Monthly Unemployment Rate | FRED API (`FRED/UNRATE`) | `fredapi.FRED(api_key=...)` (Primary); fallback to verified HF macro dataset. |
| **Consumer Confidence** | Monthly Consumer Confidence Index | FRED API (`FRED/CCI`) | `fredapi.FRED(api_key=...)` |
| **NBER Dates** | Recession start/end dates | NBER Business Cycle Dating Committee | Hardcoded reference dates in `code/config.yaml`. |

**Dataset Fit & Limitations**:
- **Sentiment**: GDELT provides daily/monthly aggregated sentiment scores with timestamps, suitable for temporal alignment. *Limitation*: GDELT covers global news; we filter for US-specific keywords to approximate social media sentiment as per the spec's intent.
- **Macroeconomic**: FRED provides high-quality, official monthly GDP and UNRATE. We will align to monthly frequency.
- **Missing Data**: If a dataset lacks a specific variable, we will note the gap and proceed with available data.
- **Sample Size**: To ensure CPU feasibility, we will sample the raw GDELT data to **100k rows** (preserving temporal distribution) if the raw volume exceeds RAM, as defined in `plan.md`.

## Methodology & Statistical Rigor

### 1. Data Preprocessing (FR-001, FR-002, FR-008, FR-010)
- **Alignment**: All series converted to **monthly** frequency.
  - GDP: Aggregated to monthly average (or interpolated from quarterly if necessary, but FRED provides monthly).
  - UNRATE: Native monthly.
  - Sentiment: Daily GDELT scores aggregated to monthly mean (Positive, Negative, Neutral separately).
- **Imputation**:
  - **Gaps <5%**: **Linear Interpolation** is applied as mandated by the spec (FR-008, US-1). A diagnostic log records the potential bias.
  - **Gaps ≥5%**: The affected months are **excluded** from the primary analysis to avoid spurious autocorrelation (violating stationarity).
- **Confidence**: Sentiment periods with sample size < threshold (e.g., <1000 news items/month) are flagged as low-confidence (FR-010). The threshold `sentiment_confidence < 0.7` is enforced in the data model.

### 2. Stationarity & Transformation (FR-003, FR-009)
- **ADF Test**: Augmented Dickey-Fuller test applied to all series.
- **Differencing**: If non-stationary (p > 0.05), first difference applied.
- **Fallback**: If still non-stationary, log or Box-Cox transformation applied (FR-009).
- **Documentation**: Log of transformation method and percentage of data affected (FR-011).

### 3. Causal Inference (FR-004, FR-013)
- **Variables**: Three distinct sentiment variables (Positive, Negative, Neutral) are used as predictors to avoid assuming linear symmetry.
- **VAR/VECM Selection**:
  - If series are I(1) and cointegrated (Johansen test), use VECM.
  - If not cointegrated, use VAR.
- **Lag Selection**: Optimal lag length selected via AIC (FR-002).
- **Granger Causality**: F-test for `Sentiment_Pos → GDP`, `Sentiment_Neg → GDP`, `GDP → Sentiment_Pos`, etc.
- **Cointegration Rank**: Select rank based on the **Trace statistic** as explicitly required by the spec (US-2). If Trace and Max-Eigenvalue conflict, the **Trace statistic** is prioritized, strictly following the project's specific requirement over general statistical heuristics.
- **Collinearity**: Calculate Variance Inflation Factor (VIF) for GDP and UNRATE. If high, frame results as a joint relationship (Edge Case).

### 4. Validation & Robustness (FR-006, FR-012, US-3, US-4)
- **Moving Block Bootstrap (MBB)**:
  - **Block Length**: **1 month** (representing the spec's "4 weeks" requirement, now valid on monthly data).
  - **Iterations**: [deferred] (minimum).
  - **Convergence**: CI width stabilizes within 1% for 3 consecutive runs.
 - **Consistency Metric**: **CI width ≤ 20% of the original OLS coefficient** (as mandated by SC-004). A fallback check (Coefficient of Variation < 0.1) is added to handle cases where the coefficient is near zero, but the [deferred] metric is the primary spec-compliant standard.
- **Sensitivity Analysis**:
  - Randomly mask [deferred]% to [deferred]% of data points.
  - Re-interpolate (if gaps <5%) or exclude (if gaps ≥5%) and re-run Granger test.
  - Report absolute p-value shift (FR-012).
  - **Bias Check**: Specifically compare results against a 'drop-missing' baseline to quantify interpolation bias.

## Statistical Rigor Checklist

- **Multiple Comparisons**: Apply Bonferroni or Holm correction to p-values when testing multiple sentiment variables.
- **Power Justification**: Acknowledge that monthly data increases power compared to quarterly, but Granger causality may still only detect strong relationships.
- **Causal Claims**: Strictly framed as "Granger-causality" (predictive precedence), not true causality, due to observational nature.
- **Measurement Validity**: Cite GDELT validation studies for economic sentiment.
- **Collinearity**: VIF check for GDP/UNRATE and sentiment variables.

## Compute Feasibility

- **Environment**: CPU-only (2 cores, 7GB RAM).
- **Data Sampling**: GDELT data sampled to **100k rows** if raw volume exceeds RAM.
- **Model Complexity**: VAR/VECM with small lag (1-4) and 3-4 variables. No deep learning.
- **Bootstrap**: 1,000 iterations on CPU is feasible for N (~400 months).
- **Runtime**: Target < 4 hours.

## Decision Rationale

- **Why VAR/VECM**: Standard for multivariate time-series with potential cointegration.
- **Why Monthly Frequency**: Required to make the spec's "4-week block" MBB constraint mathematically valid. This necessitates a deviation from the spec's "quarterly" requirement (FR-001, FR-002) to ensure the analysis is executable and the validation step (MBB) is meaningful.
- **Why GDELT**: Provides the necessary temporal dimension for time-series analysis, unlike static corpora.
- **Why Three Sentiment Variables**: Avoids the assumption of linear symmetry between positive and negative sentiment.