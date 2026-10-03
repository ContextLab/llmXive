# Research: Statistical Discrepancies in Publicly Available Election Data

## Problem Statement

The research question is whether reported vote counts at higher aggregation levels (county/state) deviate from the sum of lower-level reports (precincts) by more than expected under a model of random clerical error. This analysis aims to distinguish between benign noise (random fluctuations) and systematic anomalies (potential data entry errors or other irregularities) using statistical hypothesis testing.

## Dataset Strategy

### Available Data Sources

The spec requires data from **OpenElections** and **EAC**. However, the `# Verified datasets` block provided for this project contains **NO verified source** for OpenElections or EAC election data.

**Critical Finding**: There is **NO verified, directly-downloadable dataset** in the provided list that contains US election precinct/county vote counts.

**Resolution Strategy**:
1.  **Primary Plan**: The implementation will target the **OpenElections** project as the canonical source.
2.  **Synthetic Data Fallback (CI Mode)**: Since no verified open-source URL exists in the allowlist, the `ingestion.py` script will default to a **Synthetic Data Fallback** mode for the CI runner. This mode generates a realistic election dataset using a probabilistic model (with injected anomalies) to ensure the pipeline is testable and reproducible without relying on unverified external sources.
3.  **Real Data Mode**: If a user provides a verified URL or a HuggingFace dataset ID in `config.py`, the script will attempt to fetch that real data. If the fetch fails or the data is too large (>10GB), it falls back to sampling or the synthetic mode.
4.  **Dataset Verification**: Before analysis, the script will verify the presence of required columns: `precinct_id`, `precinct_vote_count`, `county_name`, `county_reported_total`.
5. **Data Limitations**: If the full dataset exceeds processing limits, a fixed-seed random sample of [deferred] jurisdictions will be used, with the limitation explicitly noted.

### Variable Mapping

| Required Variable | Source Column (Expected) | Handling if Missing |
|-------------------|--------------------------|---------------------|
| Precinct ID | `precinct_id` | Error if missing; cannot aggregate. |
| Precinct Vote Count | `total_votes` or `candidate_votes` | Sum across candidates; error if missing. |
| County Reported Total | `county_total` | Error if missing; cannot calculate discrepancy. |
| County Name | `county_name` | Used for aggregation key. |

## Statistical Methodology

### Null Model Construction

1.  **Robust Negative Binomial Model**:
    -   **Rationale**: Clerical errors in vote counting are likely over-dispersed. A Poisson model assumes variance = mean, which is often too restrictive. The Negative Binomial (NB) distribution accounts for this over-dispersion.
    -   **Robust Estimation (Two-Pass)**: To avoid 'baking in' anomalies, the NB parameters are **not** fitted to the raw observed discrepancies. Instead:
        -   **Pass 1**: Calculate robust statistics (median and Median Absolute Deviation - MAD) on the observed discrepancies to estimate the 'clean' error scale, ignoring the heavy tails.
        -   **Pass 2**: Use these robust parameters to fit the NB distribution. This ensures the null model represents the expected 'clean' error distribution, not the observed distribution which may contain systematic errors.
    -   **Simulation**: Generate a substantial set of synthetic discrepancy values from the fitted NB distribution.

2.  **Fallback: Parametric Bootstrap with Noise Injection**:
    -   **Rationale**: If the NB fit fails (e.g., data is too sparse or zero-inflated), the 'Permutation Model' is invalid because shuffling precincts within a county preserves the county total (discrepancy = 0).
    -   **Method**: Generate synthetic precinct sums by adding random noise (scaled by a conservative error rate derived from the median) to the reported totals. This creates a valid distribution of non-zero discrepancies for comparison.
    -   **Interpretation**: This provides a non-parametric baseline that does not rely on the NB assumption.

3.  **Goodness-of-Fit Tests**:
    -   **Anderson-Darling (AD)**: More sensitive to deviations in the tails of the distribution. Used to test if observed discrepancies follow the NB null.
    -   **Kolmogorov-Smirnov (KS)**: Tests the maximum distance between cumulative distribution functions.
    -   **Interpretation**: A p-value < 0.05 indicates the observed discrepancies deviate significantly from the random error model.

### Sensitivity Analysis

- **Threshold Sweep**: Re-run anomaly detection at thresholds: **0.01%, 0.05%, 0.1%, [deferred]** (primary). (Resolved FR-005).
-   **Model Comparison**: Compare results from Robust NB null vs. Parametric Bootstrap null.
-   **Robustness Check**: If the number of flagged anomalies varies wildly across thresholds or models, the findings are considered unstable.

### Causal Framing

-   **Observational Design**: Since we cannot randomize data entry pipelines, we **cannot** claim that discrepancies are caused by fraud or specific systemic failures.
-   **Language**: All results will be framed as "deviations from expected random fluctuations" or "associational anomalies." Claims of "fraud" or "causal mechanisms" are strictly prohibited.

## Compute Feasibility & Data Availability

-   **CPU-First**: The entire pipeline (ingestion, NB fitting, 10k simulations, AD/KS tests) is designed to run on CPU using `scipy` and `numpy`. No GPU is required.
-   **Memory Management**:
    -   **Two-Pass Streaming**: Pass 1 aggregates sufficient statistics (sum, count, sum of logs) to estimate parameters without loading full data. Pass 2 runs the simulation.
 - **Chunked Simulation**: 10,000 iterations are run in batches (e.g., [deferred] per batch) to stay under 7GB RAM.
    -   **Synthetic Fallback**: If no real data is available, synthetic data is generated on the fly to ensure CI reproducibility.
-   **Disk Limit**: Intermediate files are cleaned up after use. The final `data/processed/` directory is expected to be < 500MB for a sampled analysis.

## Decision/Rationale

-   **Why Robust NB?**: Fitting NB directly to observed data biases the null if anomalies exist. Robust estimation (median/MAD) isolates the 'clean' error signal.
-   **Why Parametric Bootstrap Fallback?**: Permutation of precincts within a county results in zero discrepancy (sum = total). Parametric bootstrap adds noise to generate a valid non-zero distribution.
-   **Why No Causal Claims?**: The data is observational. Without random assignment of "error-prone" vs. "error-free" pipelines, causal inference is invalid.
-   **Why Synthetic Fallback?**: Ensures the pipeline is testable and reproducible in CI even when no verified open election dataset exists.