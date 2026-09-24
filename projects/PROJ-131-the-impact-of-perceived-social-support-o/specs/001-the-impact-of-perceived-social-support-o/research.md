# Research: The Impact of Perceived Social Support on Resilience to Online Harassment

## Executive Summary
This research validates the data strategy and statistical methodology for testing the buffering hypothesis using the **Cyberbullying Survey 2021**. The primary finding is that a **single-dataset approach** is methodologically superior to the previously proposed dual-dataset matching, which introduced fatal confounding. The plan leverages standard psychological scales (CES-D, GAD-7, PCL-5) and robust statistical techniques (MICE, BCa Bootstrap, FDR) to ensure valid inference within the constraints of a CPU-only CI runner.

**Critical Data Availability Blocker**: The "Cyberbullying Survey 2021" dataset is **not** listed in the verified datasets block provided to the planner. No verified URL exists. The implementation **cannot proceed** without a user-provided, public, programmatic URL for this dataset. This is a blocking feasibility flaw.

## Dataset Strategy

### Verified Datasets
The analysis relies exclusively on the **Cyberbullying Survey 2021**. No other datasets are used, eliminating cross-dataset confounding.

| Dataset Name | Verified Source URL | Load Method | Notes |
|:---|:---|:---|:---|
| Cyberbullying Survey 2021 | **NOT VERIFIED** | `pandas.read_csv` / `pd.read_parquet` | **Sole Source**. Contains all required variables: `social_support`, `harassment_severity`, `depression`, `anxiety`, `ptsd`, `platform`, demographics. |

> **Note on Data Source URL**: The "Verified datasets" block in the input message did not list a specific URL for the "Cyberbullying Survey 2021". Per the **Data Availability** rules, if a dataset the spec needs has NO verified source in the block, we must state that explicitly rather than fabricating one.
>
> **Critical Finding**: The input `# Verified datasets` block contains only unrelated datasets (EnglishLM, GSS, CIs, FDR). It **does not** contain a verified URL for the "Cyberbullying Survey 2021".
>
> **Action**: The implementation plan **MUST** treat the data ingestion step as a "Blocking Feasibility Flaw" unless an open substitute is named.
>
> **Revised Strategy**: Since the "Cyberbullying Survey 2021" is not in the verified list, we cannot assume a direct download URL exists.
> 1.  **Immediate Constraint**: The plan cannot proceed with a "direct download" unless the user provides the URL or confirms it is available via a known loader (e.g., `ucimlrepo`).
> 2.  **Assumption for Plan**: We assume the dataset is available as a public CSV/Parquet file on a generic repository (e.g., Zenodo, Figshare) or via a direct URL that the implementer must discover.
> 3.  **Fallback**: If no open source exists, the project must be re-scoped. However, for the purpose of this plan, we assume the dataset is obtainable via a **public, programmatic download** (e.g., a direct HTTP link to a CSV) and that the implementer will verify the URL at runtime.
>
> **Correction**: The prompt instructions state: "For dataset/code/paper references in research.md, cite ONLY the URLs listed in the '# Verified datasets' block... NEVER invent or guess a dataset URL."
>
> **Conclusion**: The "Cyberbullying Survey 2021" is **NOT** in the verified list.
> **Decision**: The plan must explicitly state that **no verified source exists** for the "Cyberbullying Survey 2021" in the provided context. The implementation will fail unless the user provides a valid, public URL.

### Data Variables & Fit
The dataset must contain the following variables. If any are missing, the plan is invalid.

| Variable | Type | Source | Requirement |
|:---|:---|:---|:---|
| `social_support` | Numeric | Cyberbullying Survey 2021 | Perceived support score. |
| `harassment_severity` | Numeric | Cyberbullying Survey 2021 | Continuous severity score. |
| `depression` | Numeric | Cyberbullying Survey 2021 | CES-D total score. |
| `anxiety` | Numeric | Cyberbullying Survey 2021 | GAD-7 total score. |
| `ptsd` | Numeric | Cyberbullying Survey 2021 | PCL-5 total score (optional). |
| `platform` | Categorical | Cyberbullying Survey 2021 | Social media platform. |
| `age`, `gender`, `education`, `income` | Mixed | Cyberbullying Survey 2021 | Demographic covariates. |

**Dataset Fit Check**: The plan assumes the dataset contains these exact columns. If the dataset lacks `social_support` or `harassment_severity`, the analysis cannot proceed.

## Methodological Rationale

### Statistical Approach
1.  **Model**: Ordinary Least Squares (OLS) regression with interaction terms.
    -   Formula: `Outcome ~ Harassment_Severity * Social_Support + Covariates`
    -   Purpose: To test the buffering hypothesis (interaction term significance).
    -   **Causal Limitation**: As this is a cross-sectional study, results will be framed as **associational**. Claims of "causal buffering" or "resilience" are not supported by the design.
2.  **Imputation**: Multiple Imputation by Chained Equations (MICE) using `sklearn.impute.IterativeImputer`.
    -   Rationale: Handles missing predictor data without bias, preserving power.
    -   Constraint: If MICE fails to converge, the pipeline halts (per T013a).
3.  **Confidence Intervals**: Bias-Corrected and Accelerated (BCa) Bootstrap.
    -   Resamples: 1,000 (per FR-007 and Verified Fact).
    -   Rationale: Robust to non-normality of interaction effects.
4.  **Multiple Testing Correction**: Benjamini-Hochberg FDR.
    -   Rationale: Controls false discovery rate across multiple outcomes (Depression, Anxiety, PTSD) and platforms.
    -   **Note**: BH assumes independence or positive dependence. Given high correlation between Depression, Anxiety, and PTSD, this may be conservative or slightly inflated. A permutation-based FDR would be ideal but is computationally heavier.

### Compute Feasibility
-   **CPU-First**: OLS and MICE are computationally efficient and run well on a minimal number of CPU cores.
-   **Memory**: Streaming the dataset or loading it in chunks ensures < 7 GB RAM usage.
-   **Time**: 1,000 bootstrap resamples on a Large-scale dataset will complete in < 1 hour on CPU.

### Sensitivity Analysis
-   **Continuous Severity**: Primary analysis uses continuous `harassment_severity`.
-   **Platform Stratification**: Stratify by platform if N >= 30.
-   **Robustness**: Check VIF < 5 for collinearity.

### Predictor Centering
To ensure statistical validity and reduce multicollinearity:
-   **Action**: Mean-center `harassment_severity` and `social_support` before creating the interaction term.
-   **Reason**: Uncentered interaction terms are highly collinear with main effects, inflating standard errors and making main effect coefficients uninterpretable (representing effect at 0, which may be outside data range).

### Clustered Bootstrap
To account for potential platform clustering:
-   **Action**: If respondents are nested within platforms, use a **clustered bootstrap** (resampling by platform) instead of simple random resampling.
-   **Fallback**: If N per platform is too small for clustering, use standard bootstrap but explicitly note the independence violation in the report.

### Missing Data Mechanism & Bias
-   **Predictors**: MICE assumes Missing At Random (MAR).
-   **Outcomes**: Listwise deletion assumes Missing Completely At Random (MCAR).
-   **Risk**: If missingness in outcomes (e.g., depression) is correlated with severity (Missing Not At Random - MNAR), listwise deletion introduces selection bias.
-   **Mitigation**: The plan acknowledges this limitation. A sensitivity analysis using a pattern-mixture model is recommended if feasible, but the primary analysis will proceed with the MCAR assumption and a discussion of bias in the report.

## Decision/Rationale Summary

| Decision | Rationale |
|:---|:---|
| **Single-Dataset Only** | Dual-dataset matching creates confounding (Harassment ~ Dataset Source). |
| **MICE Imputation** | Preserves power and reduces bias compared to listwise deletion. |
| **BCa Bootstrap** | Provides accurate CIs for interaction terms which are often skewed. |
| **CPU Execution** | No GPU required; OLS/Bootstrap are CPU-tractable. |
| **Halt on MICE Fail** | Ensures data quality; prevents silent failure of imputation. |
| **Predictor Centering** | Reduces multicollinearity and ensures interpretable main effects. |
| **Clustered Bootstrap** | Accounts for platform-level clustering if present. |
| **Data Availability Blocker** | No verified URL exists; implementation blocked until user provides one. |

