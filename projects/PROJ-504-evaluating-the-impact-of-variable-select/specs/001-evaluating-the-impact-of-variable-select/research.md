# Research: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Overview

This research document details the dataset strategy, simulation methodology, and statistical rigor required to execute the power analysis plan. It addresses the "how" of the simulation and analysis, ensuring alignment with the spec's Functional Requirements (FRs) and Success Criteria (SCs).

**Methodological Correction**: The primary metric is redefined as **Selection Recovery Rate** (ground-truth based) to avoid the "double-dipping" fallacy associated with post-selection p-values. Statistical inference will be performed on **dataset-level aggregates** (n=10) to prevent pseudoreplication.

## Dataset Strategy

The study relies on **OpenML** as the source of real-world regression datasets to provide realistic covariance structures. The spec requires exactly 10 datasets with ≥ 100 rows and ≥ 3 predictors.

**Verified Datasets**:
The following OpenML datasets have been verified for availability and format. The implementation will select a set of datasets from the OpenML repository that meet the criteria (regression task, sufficient size). *Note: The specific 10 dataset IDs are not pre-fixed in this document to allow dynamic selection at runtime based on current OpenML availability, but they will be logged in `data/raw/`.*

*   **Source**: OpenML (https://www.openml.org/)
*   **Selection Criteria**:
    *   Task Type: Regression
    *   Rows: ≥ 100
    *   Features: ≥ 3
    *   Missing Values: Handled via imputation or skipped if > 10% missing (configurable).
*   **Verification**: The `downloader.py` script will query the OpenML API, filter candidates, and download the top 10 valid datasets. Each download will be checksummed.

**SimulatedDataset**:
As per the spec, the `SimulatedDataset` (the synthetic outcome vectors) has **NO verified source**. These are generated programmatically using the covariance matrices of the downloaded OpenML datasets. The generation process is deterministic given a seed.

## Simulation Methodology

### 1. Covariance Extraction
For each of the 10 downloaded datasets ($D_i$):
1.  Load features $X_i$.
2.  Compute the covariance matrix $\Sigma_i = \text{Cov}(X_i)$.
3.  Standardize $X_i$ to have mean 0 and variance 1 (optional but recommended for LASSO stability).

### 2. Synthetic Outcome Generation (Controlled SNR)
For each dataset $D_i$, we simulate $N_{sim} = 1,000$ outcome vectors.
For each simulation $s \in \{1, \dots, 1000\}$:
1.  **Sparsity Level ($\rho$)**: Iterate over $\rho \in \{0.1, 0.2, 0.4\}$.
2.  **SNR Level ($\lambda$)**: Iterate over $\lambda \in \{0.5, 1.0, 2.0, 5.0\}$.
3.  **True Coefficients ($\beta^*$)**:
    *   Select $k = \lfloor \rho \times p \rfloor$ predictors to be non-zero.
    *   Assign non-zero coefficients $\beta^*_j \sim \mathcal{N}(0, 1)$ for selected $j$.
    *   **Normalization**: To ensure the SNR parameter is a controlled experimental variable, the vector $\beta^*$ is scaled such that the resulting signal variance $\beta^{*T} \Sigma_i \beta^*$ is fixed to a target value $S_{target}$ for the given SNR level. This prevents uncontrolled variance in the signal component due to random $\beta^*$ draws.
4.  **Signal & Noise**:
    *   Calculate noise variance: $\sigma^2_{noise} = S_{target} / \lambda$.
    *   Generate noise $\epsilon \sim \mathcal{N}(0, \sigma^2_{noise})$.
5.  **Outcome**: $y_s = X_i \beta^* + \epsilon$.

### 3. Variable Selection & Recovery Calculation
For each simulated pair $(X_i, y_s)$:
1.  **Forward Stepwise**: Add variables one by one based on AIC/BIC or p-value threshold until no improvement. Record the decision threshold used.
2.  **Backward Elimination**: Start with all variables, remove the least significant until all remaining are significant (p < 0.05) or stopping criterion met. Record the decision threshold used.
3.  **LASSO**: Fit LASSO with cross-validated $\lambda$ (L1 regularization). Record the selected $\lambda$. Refit OLS on the selected subset **only for descriptive p-value reporting** (see note below).
4.  **Primary Metric: Selection Recovery Rate**:
    *   Count True Positives (TP): Number of non-zero $\beta^*_j$ that were **selected** by the method.
    *   Count Total True Non-Zero ($k$): Number of non-zero $\beta^*_j$.
    *   **Recovery Rate** = $TP / k$.
    *   *Note*: This metric measures selection accuracy against ground truth, avoiding the bias of post-selection inference.
5.  **Secondary Metric (Descriptive Only)**:
    *   If OLS is refitted, p-values are calculated. These are **flagged as "Post-Selection Biased"** and are **NOT** used for the primary power metric. They are reported only for descriptive comparison with standard practice.

## Statistical Rigor & Methodological Considerations

### Unit of Analysis & Pseudoreplication
*   **Correction**: The unit of analysis is the **dataset** ($n=10$), not the individual simulation ($n=120,000$). Simulations within a dataset share the same covariance structure ($X$) and are not independent.
*   **Aggregation**: For each combination of Method, SNR, and Sparsity, the 1,000 simulation recovery rates are aggregated into a **single mean recovery rate per dataset**.
*   **Statistical Test**: We will use a **Friedman test** (for repeated measures across the 10 datasets) or a **Linear Mixed-Effects Model** with 'dataset' as a random effect to compare methods. This accounts for the correlation between simulations within the same dataset. Kruskal-Wallis on individual simulations is explicitly rejected.

### Multiple Comparison Correction
*   **Correction**: If pairwise comparisons are performed (e.g., after Friedman test), we apply **Holm correction** to control the Family-Wise Error Rate (FWER).
*   **Implementation**: `scipy.stats.friedmanchisquare` followed by `scikit-posthocs` with Holm adjustment.

### Sample Size & Power Justification
*   **Simulation Count**: 1,000 simulations per condition provides a standard error for the recovery rate estimate of $\sqrt{p(1-p)/1000} \approx 0.015$ (max), which is sufficient for stable aggregation to the dataset level.
*   **Limitation**: The study is a simulation study; "power" here refers to the *empirical recovery rate* of the selection methods. The 1,000 replications are the "sample size" for estimating the true recovery rate per dataset.

### Causal Inference & Assumptions
*   **Observational Nature**: The study is a simulation, so causal claims are about the *mechanism* of variable selection under controlled conditions.
*   **Assumptions**:
    *   Linearity: The true model is $y = X\beta + \epsilon$.
    *   Normality of Errors: Assumed for OLS p-value validity (descriptive only).
    *   No Perfect Multicollinearity: Datasets with condition number > $10^{10}$ are skipped.

### Measurement Validity
*   **Instruments**: The "instruments" are the selection algorithms (Forward, Backward, LASSO). Their validity is established by standard statistical literature.
*   **Ground Truth**: Validity is ensured by the explicit construction of $\beta^*$ and the exact knowledge of which variables are non-zero. The **Selection Recovery Rate** directly measures this ground truth alignment.

### Predictor Collinearity
*   **Issue**: If predictors are definitionally related or highly correlated, LASSO may arbitrarily select one and drop others. Forward/Backward may be unstable.
*   **Handling**: The plan records the Condition Number and VIF for each dataset. If collinearity is extreme, the recovery rate might be low for all methods, which is a valid result. The plan does *not* claim independent effects for collinear variables; it reports the selection frequency and recovery descriptively.

## Decision Rationale (Compute Feasibility)

*   **CPU-Only**: All methods (OLS, LASSO via `sklearn`, Mixed-Effects via `statsmodels`) are CPU-tractable.
*   **Memory**: Storing 10 datasets × a large number of simulations × 4 SNR × 3 Sparsity results in a substantial volume of metadata rows. The actual $X$ and $y$ matrices are processed one simulation at a time or in small batches to stay well under 7 GB RAM.
*   **Runtime**: A large volume of simulations is a heavy load. To ensure completion within 6 hours:
    *   Parallelization: Use `multiprocessing` to split the 10 datasets across 2 cores (or batch processing).
    *   Efficient Libraries: Use `numpy` vectorization for simulation steps.
    *   Early Exit: If a simulation fails (e.g., singular matrix), log and skip immediately.

## Edge Case Handling

1.  **Perfect Multicollinearity**: If `np.linalg.cond(X) > 1e10`, skip the dataset and log a warning.
2.  **Zero True Coefficients**: If $k=0$ (all $\beta^*=0$), exclude from recovery calculation (denominator).
3.  **API Timeout**: Implement `requests` retry logic with exponential backoff (max 3 retries) for OpenML downloads.

## Post-Selection Inference Limitation

**Critical Note**: The standard practice of refitting OLS on LASSO-selected variables and calculating p-values is known to produce **biased p-values** (selection bias). This plan explicitly **does not use these p-values** for the primary metric (Recovery Rate). Any p-values reported in the output are strictly for descriptive purposes and are labeled "Post-Selection Biased" to avoid misinterpretation as valid frequentist power estimates.