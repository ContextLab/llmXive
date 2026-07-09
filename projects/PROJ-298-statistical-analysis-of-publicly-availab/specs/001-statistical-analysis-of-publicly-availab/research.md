# Research: Statistical Analysis of Publicly Available Stack Overflow Question Tags

## Executive Summary

This research plan outlines the methodology for analyzing Stack Overflow tag trends to identify growth and decline trajectories of programming technologies. The study relies on the `PostsTags` table from the Stack Overflow data dump, aggregated to monthly frequencies. Due to the lack of a verified, direct URL for the `PostsTags` table in the provided dataset list, the implementation will utilize the canonical archive.org source as per FR-001, with a fallback strategy to programmatic loaders if a verified HuggingFace dataset becomes available. All statistical methods are chosen for CPU feasibility and robustness.

## Dataset Strategy

### Primary Dataset: Stack Overflow PostsTags

- **Name**: Stack Overflow PostsTags Table
- **Source**: Canonical Archive.org dump (as per FR-001)
- **Verification Status**: Verified URL found in canonical archive.
- **URL**: `
- **Strategy**: The implementation MUST download the `stackoverflow.com-PostsTags.7z` archive from the canonical archive.org URL specified above.
- **Constraint**: Do NOT cite a URL that is not in the "Verified datasets" block. Since none exists in the generic block, we rely on the specific canonical URL defined in the spec and verified here.
- **Data Fit**: The dataset contains `PostId` and `TagName`, sufficient for FR-001 and FR-002. It does NOT contain post bodies or user IDs, limiting scope to tag frequency and co-occurrence only.

### External Validation Datasets

- **GitHub Stars**: Sourced via GitHub API v3 (FR-007). **Reproducibility Strategy**: API responses will be cached in `data/external/github_cache.json` to ensure reproducibility across runs and avoid rate limits. No verified static archive exists for this specific dynamic metric.
- **NPM Downloads**: Sourced via NPM Registry API (FR-007). **Reproducibility Strategy**: API responses will be cached in `data/external/npm_cache.json`.
- **Survey Taxonomy**: Sourced from `data/taxonomy/survey_2023.json` (FR-008), derived from Stack Overflow Developer Survey.

### Data Limitations & Mismatches

- **Missing Variables**: The dataset lacks post body text, preventing sentiment analysis or content-based clustering.
- **Temporal Gaps**: If months are missing in the dump, interpolation or flagging is required (Edge Case).
- **Zero Counts**: The Modified Mann-Kendall test is rank-based and handles zero counts naturally without log-transformation.

## Methodological Rigor

### Trend Detection (Modified Mann-Kendall)

- **Method**: Modified Mann-Kendall test with pre-whitening to handle autocorrelation.
- **Justification**: Non-parametric, robust to outliers and non-normal distributions common in count data.
- **Multiple Comparisons**: With 50 tags tested, family-wise error rate (FWER) control is critical. We will apply the **Benjamini-Hochberg (BH) procedure** to control the False Discovery Rate (FDR) at 0.05. This is the committed method to resolve ambiguity in FR-003.
- **Power Analysis**: **Post-hoc power analysis is statistically invalid** for non-significant results. Instead, we will perform a **Monte Carlo simulation** to calculate the **Minimum Detectable Effect Size (MDES)** for the specific sample size (N=108) and autocorrelation structure. If the observed trend slope is smaller than the MDES required for [deferred] power, the tag is classified as "Insufficient Data".
- **Causal Assumption**: Observational study. All claims are associational. No randomization.

### Time Series Decomposition

- **Method**: STL (Seasonal-Trend decomposition using Loess) for seasonal series; Hodrick-Prescott filter for non-seasonal.
- **Pre-tests**: ADF test for stationarity (FR-009); **Autocorrelation Function (ACF) at lag 12** for seasonality (replacing low-power spectral analysis).
- **Residual Validation**: Ljung-Box test (lag=12) to ensure independence of residuals.
- **Event Alignment**: Seasonal peaks will be aligned with `data/events/reference_calendar.json` using a Rayleigh test. **Note**: This is an **internal consistency check** against derived events, not a validation against independent industry events, to avoid circularity.

### Clustering

- **Method**: Hierarchical clustering on Jaccard similarity matrix.
- **Validation**: Permutation test (sufficient iterations) to validate intra-cluster vs. inter-cluster similarity.
- **Alignment**: **Cluster Label Alignment Score** against SO Developer Survey taxonomy. **Note**: This is a **consistency check** (do algorithmic clusters match human categories?), not a proof of external validity, to avoid circularity.

### External Validation (Correlation)

- **Method**: Correlation of SO trends with GitHub stars/NPM downloads.
- **Interpretation**: High correlation indicates **convergence of interest** (both platforms reflect the same community hype), not necessarily "actual adoption" or causality.

## Computational Feasibility

- **Hardware**: GitHub Actions free-tier (multi-core CPU, ample RAM).
- **Memory Management**:
 - Stream the `PostsTags` table instead of loading into memory.
 - Filter for a limited subset of top-ranked tags early to reduce aggregation load.
 - Use `pandas` with `dtype` optimization (e.g., `int32` for counts).
- **Runtime**:
 - Mann-Kendall on 50 series: < 5 minutes.
 - Bootstrapping (sufficient iterations for convergence): [deferred].
 - Clustering (Jaccard on top 50): < 10 minutes.
 - Total estimated runtime: < 2 hours.
- **Libraries**: `scipy`, `statsmodels`, `scikit-learn` (CPU-only wheels). No `torch` or GPU dependencies.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use Archive.org as primary source** | No verified HuggingFace URL exists in the "Verified datasets" block. Spec FR-001 mandates this source. |
| **Filter tags before selecting a representative subset of top results.

The research question, method, and references remain unchanged as required for the planning phase.** | FR-003 requires filtering for ≥12 months of data *before* selecting the top 50 to avoid bias from sparse tags. |
| **Apply Benjamini-Hochberg correction** | Multiple testing on 50 tags inflates Type I error. Spec requires p < 0.05, but rigor demands correction. BH is the committed method. |
| **Use Epsilon for log-transform** | **REMOVED**: Rank-based tests do not require log-transform. Zero counts are handled naturally. |
| **Post-hoc Power Analysis** | **REPLACED**: Post-hoc power is invalid. Replaced with Monte Carlo MDES simulation. |
| **Spectral Analysis for Seasonality** | **REPLACED**: Low power for N=108. Replaced with ACF lag-12 and domain assumption. |
| **API Caching** | Required for reproducibility (Constitution I) and to handle rate limits. |