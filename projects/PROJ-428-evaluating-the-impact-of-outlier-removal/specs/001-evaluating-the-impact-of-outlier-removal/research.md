# Research: Evaluating the Impact of Outlier Removal Methods on Variance Estimation

## Summary

This research phase defines the dataset strategy, statistical methodology, and experimental design required to implement the simulation study. It confirms the feasibility of the approach on CPU-only infrastructure and establishes the ground truth metrics for evaluation.

## Dataset Strategy

The study relies on two data sources:
1. **Synthetic Data**: Generated programmatically using theoretical distribution parameters (mean, variance, shape) to establish a known "ground truth" variance. This allows for precise calculation of bias and MSE against the *true parameter* of the underlying distribution.
2. **UCI Repository Data**: Used *only* as a source for real-world distribution shapes (skewness, kurtosis) to seed the synthetic generation parameters. Real UCI data is **not** used for bias/MSE evaluation because it lacks a known ground truth variance.

Per the verified dataset list, the following sources are available for reference or loading:
- **UCI HAR (CSV)**: `
- **UCI Shopper (Parquet)**: `
- **UCI DROP (Parquet)**: `
- **IQR GPT Prompts (CSV)**: `
- **MedBot (Parquet)**: `
- **TTS Test (Parquet)**: `
- **Alpaca ES (Parquet)**: `

**Selection Rationale**:
The spec requires "at least 5 public datasets from the UCI Machine Learning Repository". While the verified list contains specific HuggingFace mirrors of UCI data, the primary analysis will focus on **synthetic generation** seeded by the statistical properties (mean, variance, skew) extracted from these real-world datasets. This ensures we have a known ground truth (synthetic) while maintaining the distributional characteristics of real data (UCI).

| Dataset Source | Type | Usage in Plan |
|:--- |:--- |:--- |
| UCI HAR (via HF) | Real | Extract distribution properties (skew/kurtosis) to seed synthetic generation. |
| UCI Shopper (via HF) | Real | Same as above. |
| UCI DROP (via HF) | Real | Same as above. |
| IQR GPT Prompts | Real | Same as above. |
| MedBot | Real | Same as above. |
| **Synthetic** | Generated | **Primary Analysis**: Generate clean data, inject outliers, compute ground truth variance (theoretical parameter). |

**Note**: If a specific dataset from the verified list lacks continuous variables, it will be skipped as per Edge Case handling. The plan prioritizes the *statistical properties* of these datasets over the raw data itself to ensure the "known ground truth" requirement is met.

## Methodology

### Experimental Design
- **Independent Variables**:
 1. **Removal Method**: IQR (1.5x), Winsorization (5th/95th), Trimming ([deferred]).
 2. **Contamination Level**: Various levels (including zero), [deferred], [deferred], [deferred].
 3. **Distribution Type**: Normal, LogNormal, Exponential, Beta, Gamma (5 types).
- **Dependent Variables**:
 1. **Bias**: $| \hat{\sigma}^2_{clean} - \sigma^2_{true} |$ where $\sigma^2_{true}$ is the theoretical variance parameter.
 2. **MSE**: $E[(\hat{\sigma}^2_{clean} - \sigma^2_{true})^2]$
- **Replicates**: 100 per condition (Total: $3 \times 4 \times 5 \times 100 = 6,000$ runs).

### Statistical Analysis
1. **Linear Mixed-Effects Model (LMM)**: To test if the mean MSE differs significantly across the three removal methods.
 - **Fixed Effects**: Method, Contamination Level, Distribution Type, and their interactions.
 - **Random Effects**: Random intercept for `replicate_id` to account for within-replicate correlation across methods (since each replicate generates data for all methods).
 - **Rationale**: This correctly handles the factorial design where Distribution and Contamination are between-subjects factors (different data generations) and Method is a within-subjects factor (same replicate).
2. **Post-Hoc Testing**: Pairwise comparisons with **Holm-Bonferroni correction** to control Family-Wise Error Rate (FWER) with greater power than standard Bonferroni.
 - Adjusted Alpha: $\alpha_{adj}$ calculated dynamically based on ordered p-values.
3. **Visualization**: Interaction plots (Contamination Level vs. MSE, faceted by Distribution Type, lines by Method).
4. **Assumption Checking**: Normality and sphericity of residuals will be tested. If assumptions are violated (common for skewed distributions), the analysis will fallback to a non-parametric **Friedman test** with post-hoc Nemenyi test.

### Statistical Rigor & Assumptions
- **Multiple Comparisons**: Holm-Bonferroni correction applied explicitly as per FR-006.
- **Sample Size/Power**: A sufficient number of replicates per condition is a standard threshold for Monte Carlo stability in variance estimation studies. The plan strictly enforces this count; if runtime exceeds 6 hours, the project is flagged as infeasible rather than reducing power.
- **Causal Inference**: This is an **experimental simulation study**. The "intervention" (outlier removal) is controlled by the researcher. Claims will be framed as "Method A causes lower MSE than Method B under Condition X" within the simulation framework, supported by the LMM design.
- **Measurement Validity**: Variance estimation is the ground truth metric. Bias and MSE are standard, validated metrics for estimator performance.
- **Collinearity**: Not applicable. The analysis is univariate (per variable).

## Compute Feasibility
- **Hardware**: CPU cores, 7GB RAM.
- **Strategy**:
 - Data generation is vectorized (numpy) for speed.
 - No model training; only statistical calculations.
 - [deferred] iterations of simple arithmetic are computationally trivial on CPU.
 - Memory usage will be kept low by processing one condition at a time and streaming results to disk/CSV.
- **Risk Mitigation**: The plan enforces 100 replicates. If the -hour limit is approached, the script will log a warning but **will not reduce replicates**. If the job times out, the project is considered infeasible under current constraints.

## Decision Rationale
- **Synthetic vs. Real**: Real datasets do not have a known "true" variance after contamination. Synthetic data seeded with real distribution shapes is the only way to satisfy SC-001 and SC-002 (measuring against known ground truth).
- **LMM vs. ANOVA**: LMM is required because the design involves between-subjects factors (Distribution, Contamination) and a within-subjects factor (Method). Repeated Measures ANOVA is invalid here.
- **Holm-Bonferroni**: Chosen for better statistical power while maintaining FWER control, addressing the conservativeness of standard Bonferroni.
- **Trimming**: The method is "Trimming" (removal), resulting in "Trimmed Variance".