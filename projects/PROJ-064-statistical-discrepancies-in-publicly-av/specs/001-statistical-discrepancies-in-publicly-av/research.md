# Research: Statistical Discrepancies in Publicly Available Election Data

## Research Question

Do reported vote counts at the county level deviate from the sum of precinct-level vote counts by more than expected under a null model of random clerical error?

## Dataset Strategy

The analysis requires a dataset containing **precinct-level vote counts** and the corresponding **county-level reported totals** for the same election cycle. 

### Verified Sources & Selection

Based on the "# Verified datasets" block provided:
- **OpenElections**: NO verified source found. The plan does **not** cite a URL for OpenElections.
- **EAC (parquet)**: Three verified Hugging Face URLs are available. 
  - `community-datasets/europa_eac_tm` (parquet)
  - `CVasNLPExperiments/OxfordPets_test...` (parquet - likely irrelevant, metadata-heavy)
  - `CVasNLPExperiments/OxfordPets_test...` (parquet - likely irrelevant, metadata-heavy)

**Critical Gap Analysis**: 
The verified EAC URLs provided (`community-datasets/europa_eac_tm`) appear to be related to European/African datasets or specific NLP benchmark tasks (OxfordPets), not US precinct-level election data. The `community-datasets/europa_eac_tm` dataset is unlikely to contain US precinct/county vote counts. 

**Decision**: Since the verified URLs do **not** contain the required US election variables (precinct sums, county totals), the plan **cannot** proceed with these specific files as the primary data source for the *US* election question. 

**Pivot: Synthetic Data Fallback**: 
To ensure the statistical methodology is testable and the pipeline is functional, the plan implements a **Synthetic Data Fallback**:
1.  **Attempt Load**: The pipeline first attempts to load the verified Hugging Face datasets to inspect their schema.
2.  **Schema Validation**: If a source lacks US precinct/county variables, the script raises `DataIntegrityError` for the primary path.
3.  **Fallback Execution**: The pipeline automatically switches to a **Synthetic Data Generator** that creates a dataset with:
    -   Realistic precinct/county hierarchies.
    -   Known "ground truth" vote counts.
    -   Injected "clerical errors" (random noise) and "systematic anomalies" (known deviations) with controlled parameters.
4.  **Methodology Validation**: The statistical tests (NB, Permutation, AD/KS) are run against this synthetic data. Since the ground truth is known, we can verify if the pipeline correctly identifies the injected anomalies.
5.  **Reporting**: If only synthetic data is available, the final report explicitly states: "Analysis validated on synthetic data with known ground truth; US-specific application pending verified data source."

**Data Loading Strategy**:
- Use `datasets.load_dataset(..., streaming=True)` for the verified Hugging Face sources to check schema without downloading full files.
- If a source is verified but lacks variables, the script triggers the Synthetic Data Generator.
- **Never** fabricate a URL. If no verified US source exists, the pipeline proceeds with synthetic data.

## Statistical Methodology

### Null Models

**Critical Correction**: To avoid circular reasoning (fitting the null to the observed anomalies), the null models are constructed as follows:

1.  **Negative Binomial (Theoretical Prior)**:
    -   **Rationale**: Vote discrepancies often exhibit over-dispersion (variance > mean).
    -   **Parameter Derivation**: Instead of fitting to observed discrepancies, parameters ($\mu$, $\theta$) are derived from:
        -   **Option A**: Historical audit studies (external priors) for typical clerical error rates.
 - **Option B**: A theoretical error model where $\mu$ is the expected error rate (e.g., [deferred]) and $\theta$ is estimated from the variance of *randomly generated noise* added to the synthetic data.
    -   **Implementation**: The NB distribution is generated *independently* of the observed data's anomaly structure.

2.  **Permutation-Based (Intra-County Noise)**:
    -   **Rationale**: Non-parametric approach simulating random clerical error.
    -   **Correction**: The plan no longer shuffles precinct-to-county assignments (which destroys geography). 
    -   **Corrected Method**: The permutation test shuffles the **sign** of the discrepancy or adds random noise to precinct counts **within their original county boundaries**. This preserves the geographic structure while simulating the "random clerical error" null hypothesis.
    -   **Implementation**: A large number of iterations of adding random noise (drawn from a theoretical error distribution) to precinct counts, re-aggregating to county level, and calculating discrepancies.

### Hypothesis Testing & Anomaly Detection

-   **Anderson-Darling (AD)**: Tests the global fit of the observed distribution against the null.
-   **Kolmogorov-Smirnov (KS)**: Tests for general distributional differences.
-   **Individual Jurisdiction Scoring**:
    -   While AD/KS test the global fit, individual anomalies are flagged by calculating a **p-value for each jurisdiction**:
        -   $p_i = \frac{\text{count of simulated discrepancies} \ge \text{observed discrepancy}_i}{\text{total simulations}}$
    -   Jurisdictions with $p_i < \alpha$ (e.g., 0.05) are flagged as anomalies.
-   **Significance Level**: $\alpha = 0.05$.
-   **Framing**: Results will be reported as "The observed distribution deviates from the random expectation" (associational), never "Fraud was detected."

### Sensitivity Analysis

- **Threshold Sweep**: Explicitly defined as `{[deferred], [deferred], [deferred], [deferred]}` to satisfy FR-005.
-   **Model Comparison**: Compare anomaly counts between Negative Binomial and Permutation models.
-   **Primary Threshold**: The **0.5%** threshold is fixed as the primary reference point for SC-001.

### Collinearity & Predictor Diagnostics (SC-006)

-   If the analysis extends to regression on covariates (e.g., population density):
    -   Calculate Variance Inflation Factor (VIF) for all predictors.
    -   If VIF > 5, report collinearity and describe relationships descriptively.
    -   **No independent effects** are claimed for collinear variables.
-   If no regression is performed, SC-006 is marked as "Not Applicable" in the report.

## Compute Feasibility

-   **CPU-First**: All statistical tests (AD, KS, Negative Binomial fitting) are CPU-tractable.
- **Memory Management**: Monte Carlo iterations (10,000) will be run in chunks (e.g., [deferred] iterations per batch) to keep RAM usage < 7 GB.
-   **No GPU Required**: The analysis does not involve deep learning or large language models.
- **Time Limit**: [deferred] iterations of simple statistical sampling should complete well within 6 hours on a 2-core CPU.
-   **Synthetic Data**: Generating synthetic data is computationally inexpensive and ensures the pipeline runs even without large external datasets.

## Decision / Rationale

| Method | Choice | Rationale |
|--------|--------|-----------|
| Null Model | Negative Binomial (Theoretical) + Permutation (Intra-County) | Avoids circular reasoning; preserves geographic structure. |
| Data Source | Verified Hugging Face (if US data present) OR Synthetic Fallback | Strict adherence to "Verified datasets" block; ensures methodology is testable. |
| Inference | Associational only | Observational data cannot support causal claims (Principle VII). |
| Compute | CPU (Chunked) | Fits within GitHub Actions limits; no GPU needed for this statistical analysis. |
| Sensitivity | Thresholds {0.01%, 0.05%, 0.1%, [deferred]} | Explicitly satisfies FR-005; [deferred] is primary reference. |