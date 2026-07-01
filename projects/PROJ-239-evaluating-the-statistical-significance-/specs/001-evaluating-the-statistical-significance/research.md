# Research: Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

## Research Question

To what extent does intra-cluster correlation (ICC) in user clickstream data inflate Type I error rates in standard A/B tests (specifically in a Cluster-Randomized Trial design where naive analysis assumes observation-level independence), and can cluster-robust standard errors or block permutation tests restore nominal error rates?

## Background & Motivation

Standard A/B testing relies on the assumption that observations (e.g., user clicks, conversion events) are independent and identically distributed (i.i.d.). In clickstream data, users often generate multiple events (sessions, pages) that are correlated within the user or session cluster. This intra-cluster correlation (ICC) violates the i.i.d. assumption.

This study specifically models a **Cluster-Randomized Trial (CRT)** scenario, where the treatment (e.g., a new UI) is assigned at the cluster level (e.g., user or session group), but the naive baseline analysis incorrectly treats every observation as an independent randomization unit (pseudoreplication). This design mismatch leads to severely underestimated standard errors in standard two-sample t-tests, causing the empirical Type I error rate (false positive rate) to exceed the nominal significance level ($\alpha$).

This research validates the magnitude of this inflation across a range of ICC values and evaluates two correction strategies:
1.  **Cluster-Robust Standard Errors (CRSE):** Adjusting the variance estimator to account for within-cluster correlation, valid for CRT designs.
2.  **Block Permutation Tests:** Resampling treatment labels at the cluster level (the randomization unit) rather than the observation level to preserve the dependency structure under the null hypothesis.

## Dataset Strategy

The study utilizes **synthetic data** generated to mimic the structure of real-world clickstream data (e.g., UCI Online Retail) where session clusters induce correlation. No external real-world dataset is required for the core simulation, as the ground truth (H0: $\mu_1 = \mu_2$) is known by construction.

However, to validate the *structure* of the synthetic clusters, we reference the **UCI Online Retail** dataset (specifically its transaction/session hierarchy) as a conceptual model for cluster sizes and distributions.

**Verified Datasets Reference:**
*   **Conceptual Model:** UCI Online Retail (Session/Transaction structure). *Note: The provided verified datasets list does not contain the raw UCI Online Retail file directly, but the structure is well-documented in literature. We will simulate cluster sizes based on typical distributions found in such data (e.g., varying cluster sizes).*
*   **Verification:** The simulation will generate data with known ICC. No external URL is needed for the data generation itself, ensuring reproducibility and avoiding reliance on potentially unstable external links for the core logic.

*Note: The verified datasets block provided in the prompt (UCI HAR, Shopper, DROP) does not contain the specific "Online Retail" dataset mentioned in the spec assumptions. Since the spec relies on *synthetic* generation based on the *structure* of such data, we proceed with synthetic generation. We do not fabricate a URL for the Online Retail dataset.*

## Methodology

### 1. Data Generation (US-01) - CRT Design
We generate synthetic outcome data $Y_{ij}$ for cluster $j$ and observation $i$ using a random intercept model:
$$Y_{ij} = \mu + \tau T_j + u_j + \epsilon_{ij}$$
Where:
*   $T_j$ is the treatment assignment (0 or 1) at the **cluster level**.
*   $u_j \sim N(0, \sigma_u^2)$ is the cluster-level random effect.
*   $\epsilon_{ij} \sim N(0, \sigma_e^2)$ is the observation-level error.
*   **ICC** is controlled by the ratio $\rho = \frac{\sigma_u^2}{\sigma_u^2 + \sigma_e^2}$.
*   Under $H_0$, $\tau = 0$.
*   **Critical Design Note**: Treatment $T_j$ is constant for all $i$ within a cluster $j$. The "Standard T-Test" baseline incorrectly treats all $N$ observations as independent, ignoring that $T$ only varies $J$ times (where $J$ is the number of clusters).

### 2. Statistical Tests
*   **Standard T-Test (Naive)**: Assumes i.i.d. observations. This is the baseline for pseudoreplication.
*   **Cluster-Robust SE**: Uses the formula $V_{CR} = (X'X)^{-1} (\sum_{j} X_j' \hat{u}_j \hat{u}_j' X_j) (X'X)^{-1}$ where $\hat{u}_j$ are cluster-level residuals. This adjusts the variance to the correct number of randomization units ($J$).
*   **Block Permutation**: Permute $T_j$ across clusters $j$ (not $i$) to build the null distribution. This is the correct non-parametric null for a CRT.

### 3. Simulation Protocol
* **Iterations**: [deferred] per ICC level.
*   **ICC Levels**: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5].
*   **Alpha Levels**: {0.01, 0.05, 0.10}.
*   **Cluster Sizes**: Varied (e.g., mean=10, SD=5) to simulate unbalanced designs.
*   **Number of Clusters ($J$)**: **Minimum 50** (Default 100). This is critical because Cluster-Robust Standard Errors rely on asymptotic properties with respect to the number of clusters. Testing with $J < 50$ would introduce small-sample bias in the robust estimator itself, confounding the results.

## Feasibility & Compute Constraints

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
*   **Strategy**:
    *   **No GPU**: All operations use `numpy` and `scipy` (CPU-optimized).
 * **Memory**: Synthetic data is generated in chunks or streamed. We do not store all [deferred] iterations in memory simultaneously; results are aggregated incrementally.
 * **Runtime**: [deferred] iterations of simple t-tests and CRSE calculations are computationally light. Even with 6 ICC levels and 3 alpha levels, the total operations are well within the 6-hour limit.
    *   **Libraries**: `statsmodels` (for CRSE) and `scipy` (for t-tests) are lightweight and install cleanly on CPU.

## Statistical Rigor & Methodological Considerations

*   **Multiple Comparisons**: While we test across multiple ICC and Alpha levels, these are distinct simulation scenarios, not multiple hypothesis tests on a single dataset. However, we will report confidence intervals for the empirical error rates to quantify estimation uncertainty.
* **Power/Sample Size**: The simulation *is* the power study. We fix the number of iterations ([deferred]) to ensure the standard error of the estimated Type I error rate is small ($\sqrt{p(1-p)/N} \approx 0.007$ at $p=0.05, N=1000$). We also ensure $J \ge 50$ clusters to satisfy the asymptotic requirements of the CRSE method being tested.
*   **Causal Claims**: None. This is a method validation study. The "treatment" is synthetic and randomly assigned at the cluster level, ensuring the only source of bias is the statistical method's assumption violation.
*   **Collinearity**: Not applicable in the synthetic generation (treatment is independent of cluster effects by design).
*   **Measurement Validity**: The "instrument" is the simulation engine itself. Validity is ensured by comparing empirical error rates against the known nominal $\alpha$.

## Decision Rationale

*   **Why Synthetic Data?** Real-world clickstream data often has unknown ground truth (we don't know if the treatment *actually* had zero effect). Synthetic data allows us to enforce $H_0$ strictly, which is necessary to measure Type I error accurately.
*   **Why Cluster-Robust SE?** It is the standard frequentist approach for clustered data and is computationally efficient.
*   **Why Block Permutation?** It is a non-parametric alternative that makes fewer distributional assumptions, serving as a robustness check.
*   **Why Minimum 50 Clusters?** To ensure the "Robust" methods are being tested under conditions where they are theoretically expected to work, avoiding small-sample bias in the variance estimator itself.