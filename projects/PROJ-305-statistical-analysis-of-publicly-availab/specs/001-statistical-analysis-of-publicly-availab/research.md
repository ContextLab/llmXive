# Research: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Dataset Strategy

| Dataset | Source | Verified URL | Usage | Notes |
|---------|--------|--------------|-------|-------|
| VAERS Reports (-2023) | CDC VAERS | https://vaers.hhs.gov/data/datasets.html | Primary data source | **Verified**. Downloaded as CSV. |
| MedDRA Hierarchy | MedDRA MSSO | https://www.meddra.org/how-to-use/supporting-documentation | SOC mapping | Required for FR-002. |
| Vaccine Doses (Denominator) | CDC NVSR / VFC | https://www.cdc.gov/vaccines/programs/vfc/ | Normalization (RPMD) | Used to calculate "Reports per Million Doses" for both COVID and non-COVID groups. |
| Media Event Flags | CDC Press Releases | https://www.cdc.gov/media/releases/ | Covariate | Curated list of dates with major safety announcements to control for reporting bias. |

> **Data Limitation Note**: The VAERS dataset does not contain `vaccination_date` or `onset_date`. Therefore, the "14-30 days post-vaccination" analysis (FR-007) is **uncomputable**. The plan uses **Calendar-Time Anomaly Detection** as a proxy, acknowledging this limitation.

## Methodological Rationale

### Disproportionality Metrics (FR-003, FR-004)

- **Reporting Odds Ratio (ROR)**: Calculated via custom logic: (a/b) / (c/d), where a=COVID+SOC, b=COVID+non-SOC, c=non-COVID+SOC, d=non-COVID+non-SOC. 95% CI via log transformation.
- **Proportional Reporting Ratio (PRR)**: (a/(a+b)) / (c/(c+d)). Handles zero counts via continuity correction (add 0.5).
- **Information Component (IC)**: Bayesian approach (log2 ratio of observed/expected). Lower bound > 0 indicates signal.
- **Multiple Testing**: Benjamini-Hochberg (BH) correction applied **only** to SOCs passing the **Minimum Count Threshold** (n >= 10 in both groups) to control FDR at α=0.05 (FR-005).

### Signal Definition (FR-006)

A signal is "positive" **ONLY IF** the following strict criteria are met in order:

1.  **Mandatory Primary Threshold**: The **ROR lower 95% CI bound must be > 1.0**. If this condition fails, the SOC is immediately excluded from further signal consideration, regardless of PRR or IC values.
2.  **Multi-Metric Consistency**: At least **two** of the three metrics must indicate a signal:
    *   ROR lower 95% CI > 1.0 (Satisfied by step 1).
    *   PRR lower 95% CI > 1.0.
    *   IC lower 95% CI > 0.
3.  **Bias Adjustment**: The metrics are calculated on **Media Event Flag adjusted residuals** or the model includes the flag as a covariate to isolate signals from reporting artifacts.

This strict ordering ensures that the "ROR lower 95% CI > 1.0" prerequisite is never bypassed, preventing false positives from metrics that might be sensitive to different biases than ROR.

### Temporal Analysis (FR-007, FR-010)

- **Calendar-Time Anomaly Detection**: Poisson regression on **weekly counts** (Calendar Weeks).
- **Covariates**: Includes **Media Event Flag** (binary, derived from CDC press releases) to control for reporting spikes.
- **Control Group Comparison**: Poisson regression with **interaction term** (Vaccine_Type * Time) to test if the temporal trend differs significantly between COVID-19 and non-COVID groups (FR-010).
- **Normalization**: Uses **Reports per Million Doses (RPMD)** for both groups, using CDC annual vaccine coverage data as the denominator.

### Memory & Runtime Optimization (FR-009)

- **Chunked Processing**: VAERS files processed in chunks (e.g., large batches) to stay under a constrained RAM footprint.
- **Polars**: Used for memory-efficient dataframe operations (lazy evaluation, streaming).
- **Sampling**: If raw data exceeds 7GB after chunking, a stratified sample (preserving SOC proportions) is taken.

## Statistical Rigor Checklist

| Requirement | Status | Method |
|-------------|--------|--------|
| Multiple-comparison correction | ✅ | Benjamini-Hochberg (FR-005) applied to filtered SOCs (n >= 10). |
| Sample-size / power justification | ⚠️ | Acknowledged limitation: VAERS is spontaneous reporting; power analysis not feasible. Focus on effect size (ROR/PRR) and minimum count threshold. |
| Causal inference assumptions | ✅ | Explicitly framed as associational (observational study). No causal claims. |
| Measurement validity | ✅ | MedDRA hierarchy is standard; SOC mapping documented. |
| Predictor collinearity | ✅ | SOCs are mutually exclusive categories; no collinearity in disproportionality analysis. |
| Reporting Bias | ✅ | **Media Event Flag** covariate included in Poisson regression to control for media-driven reporting spikes. |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use Polars instead of Pandas | Polars offers better memory efficiency and streaming capabilities for large datasets. |
| Apply continuity correction (0.5) for zero counts | Prevents division-by-zero errors in PRR/IC calculations (Edge Case 2). |
| Omit background rate comparison if unavailable | FR-008 mandates proceeding with internal baseline if external rates are missing. |
| **Revised Temporal Analysis** | VAERS lacks `vaccination_date`; "14-30 day" window uncomputable. Replaced with Calendar-Time Anomaly Detection. |
| **Bias Adjustment** | Added Media Event Flag to control for reporting artifacts in ROR/PRR/IC and Poisson models. |
| **Denominator Strategy** | Used CDC annual vaccine coverage reports to normalize counts (RPMD) for valid control group comparison. |
| **Strict Signal Definition** | Explicitly enforced ROR lower CI > 1.0 as a mandatory gate before checking multi-metric consistency to satisfy FR-006. |
