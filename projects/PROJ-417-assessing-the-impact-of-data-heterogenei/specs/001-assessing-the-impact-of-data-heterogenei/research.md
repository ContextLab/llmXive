# Research: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Dataset Strategy

### 1.1 Base Data Source
The simulation engine requires a "base" dataset representing real-world meta-analysis structures (study-level effect sizes and standard errors) to perturb.

*   **Target Source**: Cochrane Reviews meta-analyses.
*   **Verification Status**: **NO verified source found** in the provided `# Verified datasets` block for a specific Cochrane meta-analysis dataset.
*   **Strategy**:
    1.  The system will implement a `BaseDataLoader` that attempts to fetch a representative Cochrane dataset from a public repository if one becomes available.
    2.  **Fallback**: If no verified URL is found in the execution environment, the system will use a **synthetic base** generated from standard meta-analysis parameters.
    3.  **Constraint**: The plan will **NOT** fabricate a URL. If the spec requires a specific Cochrane dataset and none is verified, the research phase will document this gap and proceed with the synthetic base, noting that the "ground truth" is the injected $\tau^2$ relative to the synthetic base distribution, not a specific real-world study.

### 1.2 Construct Validity of Synthetic Base
To address construct validity risks (concern methodology-c7d809d9), the synthetic base will not use arbitrary parameters. It will mimic the statistical properties of real Cochrane reviews as described in methodological literature (e.g., *Jackson et al., 2010; Thompson & Sharp, 1999*).
*   **Study Count ($k$)**: Sampled from a Gamma distribution (shape=2.5, scale=5.0) to approximate the typical range of 5-30 studies per meta-analysis.
*   **Standard Errors ($\sigma_i$)**: Sampled from a Log-Normal distribution ($\mu=0.2, \sigma=0.5$) to reflect the right-skewed nature of SEs in real data (where small studies have large SEs).
*   **True Effect ($\theta$)**: Fixed at 0.5 (Log Odds Ratio scale) for the primary simulation, representing a moderate effect size.
*   **Verification**: The generated base distribution will be plotted and compared against reference plots from *Cochrane Handbook Chapter 10* to ensure visual fidelity.

### 1.3 Data Generation Model (Two-Stage)
To address the concern that treating within-study variances as fixed constants leads to overly optimistic coverage (concern methodology-94b1d70c, scientific_soundness-0840e50a), the simulation will use a **Two-Stage Generation** process:
1.  **Stage 1 (Study Size)**: For each study $i$ in a replicate, sample a total sample size $N_i$ from a Log-Normal distribution.
2.  **Stage 2 (SE Derivation)**: Derive the standard error $\sigma_i$ from $N_i$ based on the effect metric (e.g., for Log Odds Ratio, $\sigma_i \approx \sqrt{1/a + 1/b + 1/c + 1/d}$). This ensures $\sigma_i$ is correlated with the sample size and acts as a random variable, not a fixed constant.
3.  **Stage 3 (Effect Generation)**: Draw effect sizes $y_{i,r} \sim N(\theta, \sigma_i^2 + \tau^2)$.
This approach mimics the uncertainty in real meta-analyses where $\sigma_i$ is estimated from data.

### 1.4 Simulated Data Generation
*   **Method**: The simulation will generate $N$ replicates for each $\tau^2 \in \{0, 0.1, 0.5, 1.0, 2.0\}$ (Primary) and $\{0.05, 0.1, 0.5\}$ (Sensitivity).
*   **Volume**:
    *   Primary Sweep: 5 levels $\times$ 500 replicates = 2,500 datasets.
    *   Sensitivity Sweep: 3 levels $\times$ 500 replicates = 1,500 datasets.
    *   Total: A diverse collection of datasets.

## 2. Statistical Methodology

### 2.1 Estimators
The system will implement three estimators as per FR-002:
1.  **Fixed-Effects (FE)**: Assumes $\tau^2 = 0$. Weight $w_i = 1/\sigma_i^2$.
2.  **DerSimonian-Laird (DL)**: Method-of-moments estimator for $\tau^2$.
3.  **REML**: Restricted Maximum Likelihood estimator for $\tau^2$.
    *   *Handling Convergence*: If REML fails to converge (negative variance), the system will log the event, set $\hat{\tau}^2 = 0$ (or a minimal positive value), and flag the result (FR-006).

### 2.2 Metrics
*   **Bias**: $\hat{\theta} - \theta_{true}$.
*   **Coverage**: Indicator $I(\theta_{true} \in [\hat{\theta} - 1.96 \times SE, \hat{\theta} + 1.96 \times SE])$.
* **Magnitude of Deviation**: $\text{Coverage Rate} - 0.95$ (with [deferred] Wilson Score Interval).

### 2.3 Hypothesis Testing
*   **Coverage Test**: Exact Binomial Test against nominal $\alpha$ (e.g., 0.05).
    *   $H_0$: Observed coverage = Nominal coverage.
    *   Correction: **Bonferroni** applied across 5 $\tau^2$ levels ($\alpha_{adj} = 0.05 / 5 = 0.01$) (FR-007).
*   **Bias Test**:
    *   **Normality Check**: *Removed*. The plan will **not** use a two-stage Shapiro-Wilk test to switch between ANOVA and Kruskal-Wallis (concern scientific_soundness-bd2b82c2).
    *   **Group Comparison**: Default to **Kruskal-Wallis** test for bias differences across levels, as it is robust to non-normality and preferred in simulation studies with $N=500$. If normality is assumed for a specific sub-analysis, **Bootstrap Confidence Intervals** for mean differences will be used instead of ANOVA.
    *   **Post-Hoc**: If Kruskal-Wallis is significant, perform **Dunn's Test** with Bonferroni correction for pairwise comparisons (concern methodology-f0002eaf).

### 2.4 Magnitude Estimation (Scientific Soundness)
To address the concern that binary p-values are trivial (scientific_soundness-4171c7b9), the analysis will explicitly calculate:
* The **deviation** of observed coverage from the nominal [deferred] (e.g., [deferred] vs [deferred]).
* The **[deferred] Wilson Score Interval** for the coverage rate.
*   The report will focus on whether the *magnitude* of under-coverage exceeds a practical threshold (e.g., >2%) rather than just statistical significance.

## 3. Computational Feasibility

*   **Environment**: GitHub Actions Free Tier (multiple CPU cores, 7GB RAM, 6h limit).
*   **Strategy**:
    *   **No GPU**: All operations use `numpy`/`scipy` CPU paths.
    *   **Memory**: Process replicates in batches (e.g., 100 at a time) to keep RAM usage low.
    *   **Runtime**: 4,000 replicates of simple meta-analysis is computationally trivial on CPU. Estimated runtime < 45 minutes.
    *   **Libraries**: `scipy`, `numpy`, `pandas` (all CPU-optimized).

## 4. Methodological Rigor & Assumptions

*   **Causal Framing**: As per Assumption in Spec, findings are **associational**. The simulation establishes the relationship between injected heterogeneity and estimator performance, not a causal effect of heterogeneity on truth.
*   **Multiple Comparisons**: Bonferroni correction is strictly applied (FR-007).
*   **Collinearity**: Not applicable in this simulation context as $\tau^2$ is the independent variable manipulated directly.
*   **Power**: A sufficient number of replicates will be used to provide adequate power to detect deviations in coverage from 95% (Monte Carlo error $\approx 1.3\%$).

## 5. Decision Rationale

*   **Why Synthetic Base?**: No verified Cochrane dataset URL exists in the `# Verified datasets` block. Using a synthetic base ensures reproducibility and avoids hallucinating a URL. The validity of the *method* (estimator performance under known $\tau^2$) remains intact.
*   **Why Bonferroni?**: Required by FR-007 to control Family-Wise Error Rate (FWER) when testing 5 distinct heterogeneity levels.
*   **Why REML Fallback?**: High heterogeneity with small study counts often causes REML non-convergence. A fallback ensures the simulation completes (SC-003) without losing data points.
*   **Why Kruskal-Wallis Default?**: Avoids the pitfalls of data-driven normality testing (concern scientific_soundness-bd2b82c2) and provides a robust non-parametric test for bias differences.
*   **Why Two-Stage Generation?**: Ensures the simulation reflects the uncertainty in standard errors found in real meta-analyses, improving external validity (concern methodology-94b1d70c).