# Research: Assessing the Validity of Statistical Significance in RCTs with Missing Data

## Problem Statement

The study aims to quantify the inflation of Type I error rates in Complete-Case (CC) analysis when data contains missing values under different mechanisms (MCAR, MAR, MNAR). **Scope Clarification**: While the spec requires RCT datasets, no verified RCT sources exist in the allowed list. Therefore, this study uses **proxy datasets** (survey/log data) with **synthetic treatment and outcome columns** to simulate RCT-like conditions (randomized treatment, null effect). The "tipping points" identified are **methodological thresholds** for the specific data distributions used, not universal clinical rules. The primary goal is to assess the statistical robustness of CC, MI, and IPW methods under these controlled conditions.

## Dataset Strategy

### Verified Datasets
Per the project constraints, the system MUST use only the following verified sources.

| Dataset Name | Verified URL / Identifier | Relevance to RCT Spec | Action |
|--------------|--------------|-----------------------|--------|
| Malawi Survey | `mcarthuradal/malawi` (Parquet) | General survey data. Lacks explicit treatment/outcome structure for RCT. | **Use as proxy**: Will construct synthetic `treatment` (randomized) and `outcome` (correlated with covariates, zero effect) columns. |
| CAD Logs | `markov-ai/cad-1000-hours` (CSV) | CAD log data. Not an RCT. | **Use as proxy**: Will construct synthetic `treatment` and `outcome` columns. |
| MNAR Synthetic | N/A (Generated) | N/A | **Synthetic Generation**: The system will generate synthetic RCT data (N > 200) with known parameters to satisfy the MNAR requirement, as no verified source exists. |

**Gap Analysis & Mitigation**:
- **FR-001 Deviation**: The spec (FR-001) mandates "public RCT datasets". The verified list provides **NO RCT source**.
  - **Mitigation**: The implementation will use the **Malawi** and **CAD** datasets as *structural proxies*. The system will:
    1. Select a subset of covariates.
    2. Generate a synthetic binary `treatment` column (randomized).
    3. Generate a synthetic `outcome` column correlated with covariates but with a *true null effect* (treatment coefficient = 0) via permutation.
    4. Apply missingness mechanisms to the `outcome`.
  - **Rationale**: This satisfies the "Ground Truth Calibration" (Constitution Principle VI) by ensuring the null hypothesis is mathematically enforced. The "tipping points" identified will be valid for the *statistical properties* of the data, though generalizability to real clinical RCTs is limited by the proxy nature of the data.
  - **MNAR Handling**: Since no verified MNAR source exists, the system will generate a synthetic dataset specifically for MNAR testing, ensuring the missingness depends on the unobserved (true) outcome values.

**Data Validity Check**:
Before the main simulation, the system will verify that the synthetic outcome generation produces a distribution with the expected variance and correlation structure relative to the covariates. If the proxy data's covariates are uncorrelated with the outcome, the MAR simulation will be flagged as invalid for that dataset.

### Data Loading Strategy
- **Streaming**: For large parquet files, use `datasets.load_dataset(..., streaming=True)` to avoid RAM overflow.
- **Checksum**: All downloaded files will be checksummed (SHA-256) and stored in `data/raw/`.
- **Preprocessing**:
  1. Load data.
  2. Impute any pre-existing missingness in covariates (mean/mode) to ensure a complete baseline for simulation.
  3. **Permute Treatment**: Shuffle the `treatment` column to establish the true null hypothesis (zero effect).
  4. **Synthesize Outcome (if needed)**: If the dataset lacks a clear outcome, generate one based on covariates with zero treatment effect.

## Statistical Methodology

### 1. Simulation Loop (per dataset, per mechanism, per rate)
For $K=500$ iterations:
1. **Baseline**: Load permuted data (True Null).
2. **Simulate Missingness**:
   - **MCAR**: Randomly drop $r\%$ of outcomes.
   - **MAR**: Drop outcome based on observed covariates (e.g., `logit(p) = β0 + β1 * age`).
   - **MNAR**: Drop outcome based on the *true* permuted outcome value (e.g., `logit(p) = β0 + β1 * outcome`). **Note**: The true outcome value is established *before* the permutation step used for the null hypothesis test. The missingness mechanism depends on the *true* Y, not the permuted noise. This ensures the MNAR mechanism is valid and reflects the causal link.
3. **Analysis**:
   - **CC**: Filter rows where outcome is observed. Run t-test (continuous) or Wilcoxon (binary).
   - **MI**: Impute missing values (m=5) using `statsmodels.imputation.mice.MICE`. Pool results.
   - **IPW**: Calculate propensity of being observed. Weight the complete cases.
4. **Metric**: Record p-value.

### 2. Error Rate Calculation
- **Empirical Type I Error**: $\hat{\alpha} = \frac{1}{K} \sum I(p_i < 0.05)$.
- **Binomial Test**: Test if $\hat{\alpha}$ significantly deviates from 0.05.
  - $H_0: p = 0.05$
  - $H_1: p \neq 0.05$
  - Use `scipy.stats.binom_test`.
- **Multiple Comparison Correction**: The sweep involves multiple conditions (multiple rates x 3 mechanisms x 3 methods). To control the False Discovery Rate (FDR), we will apply the **Benjamini-Hochberg (BH)** procedure to the p-values from the Binomial tests across all conditions. A condition is flagged as a "significant deviation" only if its adjusted p-value < 0.05.

### 3. Tipping Point Identification
- Sweep missingness rates: $r \in \{5\%, 10\%, 15\%, 20\%, 25\%, 30\%, 35\%, 40\%\}$.
- **Definition**: A rate $r$ is a "tipping point" if:
  1. The 95% confidence interval of the empirical error rate excludes 0.05 (after BH correction).
  2. The error rate represents a notable increase over the baseline (proposed threshold: >5.25%, or 5% relative increase).
- This replaces the arbitrary fixed threshold with a statistically derived criterion.

### 4. Power Analysis (Alternative Hypothesis)
To satisfy SC-004, the system will generate a second set of simulations where the treatment effect is non-zero (e.g., Cohen's d = 0.5).
- **Process**: Generate outcome with a known treatment effect. Simulate missingness. Calculate power (proportion of p-values < 0.05).
- **Metric**: Compare empirical power to theoretical power for the given sample size and effect size.

### 5. Relative Error Inflation (SC-005)
To satisfy SC-005, the system will calculate the ratio of CC error to MI error at the identified tipping point.
- **Metric**: $Ratio = \frac{\hat{\alpha}_{CC}}{\hat{\alpha}_{MI}}$.
- **Flag**: A condition is a "Validated Tipping Point" if $Ratio > 2.0$.

### 6. Statistical Rigor & Assumptions
- **Multiple Comparisons**: Addressed via BH correction.
- **Power**: Addressed via the Power Analysis phase.
- **Collinearity**: In MAR simulation, covariates must not be collinear with the treatment (which is randomized, so this is naturally handled).
- **Causal Claims**: No causal claims are made about the *data generation*. Claims are limited to the *statistical validity* of the analysis methods under missingness.

## Compute Feasibility

- **CPU-First**: The simulation is embarrassingly parallel.
  - **Strategy**: Use `multiprocessing` to run 500 iterations in parallel across 2 cores (or batch them).
  - **Memory**: Each iteration processes a single dataset row-wise. Streaming ensures < 7GB RAM.
  - **Time**: 500 iterations x 8 rates x 3 mechanisms x 3 methods = 36,000 analysis runs.
    - If one analysis takes 10ms, total time = 360s (6 mins).
    - Even with overhead, this fits well within 6 hours on CPU.
- **GPU**: Not required. No deep learning models are used.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Use Proxy Datasets** | No verified RCT source exists. Using real-world data with synthetic treatment/outcome preserves the *distributional properties* of the covariates, which is critical for MAR/MNAR simulation, while ensuring the null hypothesis is mathematically enforced. |
| **MNAR via Synthetic Data** | No verified MNAR source exists. Generating synthetic data with known parameters is the only valid way to test MNAR where missingness depends on unobserved values. |
| **Permutation for Null** | Essential for Type I error calculation. We cannot assume the original data has a true null. Permuting treatment guarantees exchangeability. |
| **CPU-First** | The statistical methods (t-test, logistic regression, imputation) are computationally light. GPU acceleration offers no benefit and adds complexity. |
| **BH Correction** | Necessary to control FDR across 72 conditions. Raw p-values are insufficient for rigorous "tipping point" identification. |
| **Unified Thresholds** | SC-001 (≤ 5.25%) and SC-002 (> 5.25%) are unified: [deferred] is the proposed "tipping point" (failure), [deferred] is the "nominal" level. |