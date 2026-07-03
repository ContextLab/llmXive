# Research: Virtual Reality Exposure Therapy Meta-Analysis

## Literature Search Strategy

### Databases
The systematic review will target the following repositories. Since the CI environment cannot perform live API queries to PubMed/PsyArXiv without keys and rate limits, the **Search Phase** will be designed to accept **CSV exports** from these sources as the primary input, simulating the API result.

1.  **PubMed Central (PMC)**: Primary source for full-text RCTs.
2.  **PsyArXiv**: Preprint server for recent psychological studies.
3.  **OpenAlex**: Open bibliography for broad coverage.

### Search Query Construction
Per FR-001, the search string will be constructed as:
`("virtual reality" OR "VR") AND ("exposure therapy" OR "exposure treatment") AND ("anxiety" OR "anxiety disorder") AND ("randomized controlled trial" OR "RCT")`

### Data Availability & Verification
**Verified Datasets**:
As of the current date, there is **no single open-access, pre-curated dataset** containing all VR exposure therapy RCTs with the required statistics (means, SDs, Ns) for immediate analysis.
- **Strategy**: The pipeline will be designed to ingest a `raw_studies.csv` file. This file will represent the "export" from the search databases.
- **Mock Data for CI**: To ensure the pipeline is testable on GitHub Actions (which cannot scrape the web), a `data/raw/mock_studies.csv` will be provided in the repository. This file will contain a representative set of synthetic but realistic study records adhering to the schema, allowing the `inclusion_filter` and `effect_size_calc` modules to be unit-tested and integration-tested.
- **Real Data Path**: In a production run, the user would replace `mock_studies.csv` with the actual CSV export from the literature search.

**Dataset Variable Fit Check**:
- **Required Variables**: Study ID, Title, Year, Population (Anxiety Type), N_Treatment, Mean_Treatment, SD_Treatment, N_Control, Mean_Control, SD_Control, Outcome Measure (e.g., STAI).
- **Fit Confirmation**: The mock data and the expected CSV schema are designed to include all these fields. If a real study export lacks these specific columns (e.g., only reports p-values), the `inclusion_filter` module will explicitly exclude it (as per Spec Edge Cases) and log the reason "INSUFFICIENT_STATISTICS".

## Statistical Methodology

### Effect Size Computation (FR-003)
- **Metric**: Hedges' g (standardized mean difference with small-sample correction).
- **Formula**:
  $$ g = J \times \frac{\bar{X}_T - \bar{X}_C}{S_{pooled}} $$
  Where $J = 1 - \frac{3}{4(N_T + N_C) - 9}$ is the correction factor, and $S_{pooled}$ is the pooled standard deviation.
- **Justification**: Hedges' g is preferred over Cohen's d for meta-analyses with small sample sizes (typical in VR trials) to reduce bias.
- **Implementation**: Calculated using `numpy` for vectorized performance. No external heavy libraries required.
- **Handling Missing Correlation (r)**: If the input data lacks the correlation coefficient ($r$) between pre- and post-measures (required for change-score effect sizes), the pipeline will compute effect sizes for a range of plausible correlations ($r=0.4$ and $r=0.8$) as a sensitivity analysis. These values will be stored in the `sensitivity_range` object within the output schema, with `low_r` corresponding to $r=0.4$ and `high_r` corresponding to $r=0.8$. If $r$ is provided, the primary effect size is computed using that value.

### Meta-Analysis Model (FR-004)
- **Model**: Random-Effects Model.
- **Estimator**: **Restricted Maximum Likelihood (REML)** will be used for the final analysis to provide unbiased estimates of between-study variance ($\tau^2$).
- **Tooling**: The implementation will use the `statsmodels.stats.meta_analysis` module (specifically `combine_effects` with `method='REML'`).
- **Validation Strategy**: To ensure the Python implementation matches the gold standard, a dedicated validation step (Task 0.5 in the plan) will compare `statsmodels` outputs against a pre-computed R `metafor` benchmark (using `rma.uni` with `method='REML'`) on a fixed synthetic dataset. The pipeline will halt if the difference exceeds floating-point tolerance. This eliminates the risk of relying on a custom, unverified implementation.
- **Justification**: VR studies vary significantly in hardware, protocol, and anxiety subtypes. A fixed-effects model would be inappropriate. REML is generally preferred over DL for small sample sizes.
- **Feasibility**: Calculating $\tau^2$ and $I^2$ for <100 studies is trivial on a 2-core CPU.

### Publication Bias (FR-005)
- **Method**: Egger's Linear Regression Test.
- **Threshold**: $p < 0.10$ (standard for meta-analysis to reduce Type II error in small N).
- **Condition**: Only performed if $N \ge 10$. If $N < 10$, the report will state "Egger's test underpowered; visual inspection only."
- **Visualization**: Funnel plot generated via `matplotlib`.
- **Trim-and-Fill**: If asymmetry is detected ($p < 0.10$), the pipeline will perform a trim-and-fill adjustment to estimate the number of missing studies and calculate an adjusted effect size. This adjusted value will be stored in the `trim_fill_adjusted_g` field of the output.

### Sensitivity Analysis (FR-006)
- **Method**: Leave-One-Out (LOO).
- **Process**: Iteratively remove one study, re-run the random-effects model, and record the pooled effect size.
- **Feasibility**: For $N=15$, this requires 15 model fits. Computationally negligible.

## Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Memory**: The entire dataset (CSV + DataFrames) will be < 10MB. No memory issues.
- **Time**:
  - Search/Filter: < 1 min.
  - Effect Size Calc: < 1 sec.
  - Meta-Analysis: < 1 sec.
  - Plotting: < 10 sec.
  - PDF Gen: < 30 sec.
 - **Total**: Well within the 6-hour limit.
- **No GPU**: All operations are linear algebra or text processing. No neural networks.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Python over R** | While `metafor` is the gold standard in R, the project requires a self-contained CI pipeline. Python's `statsmodels` provides sufficient functionality for REML and Egger's test without requiring a complex R environment setup in GitHub Actions. Validation against R (DL and REML) ensures correctness. |
| **CSV Input over Live API** | Live API calls introduce rate limits, authentication complexity, and non-determinism (results change daily). Using a CSV export ensures the CI pipeline is reproducible and deterministic (Constitution Principle I). |
| **Mock Data for CI** | To satisfy the "Independent Test" requirement of the spec (US-1, US-2), a `mock_studies.csv` is necessary to demonstrate the pipeline works. This is not "fabricated results" but a **test fixture** for the code logic. Real data is required for the final research output. |

## Risks & Mitigations

- **Risk**: Real studies report only p-values or confidence intervals, not means/SDs.
  - **Mitigation**: The `inclusion_filter` will detect this and exclude the study, logging the reason. The report will explicitly state the number of excluded studies due to "Insufficient Statistics."
- **Risk**: High heterogeneity ($I^2 > 75\%$).
  - **Mitigation**: The pipeline will automatically trigger a moderator analysis (if moderator data is present) or flag the result as "High Heterogeneity" in the report, as per Spec Edge Cases.
- **Risk**: $N < 10$ for Egger's test.
  - **Mitigation**: The code will detect $N < 10$ and skip the statistical test, generating only the funnel plot and a text warning.
