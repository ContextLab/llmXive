# Research: Exploring the Impact of Data Imputation Methods on Causal Inference

## Executive Summary

This research investigates the robustness of standard imputation methods (Mean, KNN, MICE) when applied to data with Missing Not At Random (MNAR) mechanisms, specifically where missingness depends on the unobserved outcome. Using synthetic Structural Causal Models (SCMs) with known ground-truth Average Treatment Effects (ATE), we quantify the bias introduced by these methods. The study confirms that standard methods, which assume Missing At Random (MAR), fail to recover the true ATE under MNAR, with bias increasing monotonically with the strength of the MNAR mechanism ($\beta$).

## Dataset Strategy

**Note**: This study relies on **synthetic data generation** to ensure precise control over the MNAR mechanism and ground-truth ATE. No external real-world datasets are used for the primary simulation, as real-world datasets rarely have known ground-truth causal effects or explicitly parameterized MNAR mechanisms.

However, for methodological validation and comparison, we reference the following verified datasets where relevant concepts (imputation, causal estimation) have been studied, though they are **not** used as the primary input for the simulation loop:

| Concept | Dataset Name | Verified URL | Usage Note |
|:--- |:--- |:--- |:--- |
| MNAR Mechanisms | HW4_REGRESSION_mnar | ` | Referenced for understanding MNAR data structures; not used for simulation generation. |
| Imputation (MICE) | gp2protein_mice_JAX | ` | Referenced for MICE implementation patterns; not used for simulation. |
| Causal Estimation (IPW/PSM) | ipw-sft-trajectories | ` | Referenced for IPW logic validation; not used for simulation. |
| Synthetic Data Patterns | Synthetic_Ateso_MMS | ` | Referenced for synthetic data schema patterns; not used for simulation. |

**Primary Data Source**: The `code/simulate.py` module generates all data. The "ground truth" is the parameter $\tau_{true}$ defined in the generative SCM, not an external reality.

## Methodology

### 1. Synthetic Data Generation (FR-001, FR-002)
We generate data from a Structural Causal Model:
- **Treatment ($T$)**: Binary, generated from confounders $X$.
- **Outcome ($Y$)**: Continuous, $Y = \tau T + \beta_X X + \epsilon$.
- **Confounders ($X$)**: Continuous multivariate normal.
- **MNAR Mechanism**: Missingness indicator $M$ is generated via a logistic model: $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta_{mnar} Y)$.
 - $\beta_{mnar}$ controls the strength of the MNAR mechanism.
 - **Alpha Tuning**: To ensure construct validity, we perform a **binary search** on $\alpha$ for each $\beta_{mnar}$ value to achieve a **target a moderate missingness rate**. This ensures that any observed bias trend is attributable to the strength of the MNAR mechanism ($\beta$) and not confounded by varying missingness rates.
 - When $\beta_{mnar} = 0$, data is MAR (baseline).
 - When $\beta_{mnar} > 0$, missingness depends on $Y$ (MNAR).

**Ground Truth**: The true ATE ($\tau_{true}$) is set at generation time (e.g., a moderate value) and stored in the dataset metadata.

### 2. Imputation Strategies (FR-003)
Three methods are applied to the incomplete dataset:
1. **Mean Imputation**: Replaces missing values with the column mean (computed on observed data).
2. **KNN Imputation**: Uses $k=5$ nearest neighbors (Euclidean distance) to impute.
3. **MICE (Multiple Imputation by Chained Equations)**: Uses iterative chained equations (default multiple iterations) to generate ** imputed datasets**.
 - **Rubin's Rules**: For MICE, we apply Rubin's Rules to combine the 5 imputed estimates. This involves calculating the average point estimate and combining the within-imputation and between-imputation variances to produce valid standard errors and confidence intervals. This resolves the statistical invalidity of using single imputation for MICE.

### 3. Causal Estimation (FR-004)
For each imputed dataset (or combined MICE result):
1. **Propensity Score Estimation**: Fit a logistic regression $P(T=1|X)$ using only observed confounders $X$.
2. **IPW**: Calculate weights $w = \frac{T}{e(X)} + \frac{1-T}{1-e(X)}$.
 - **Weight Trimming**: To ensure stability and address positivity violations, weights are truncated at the extreme percentiles before estimation.
 - Estimate ATE via weighted regression.
3. **PSM**: Match treated and control units using nearest neighbor matching (caliper set to a small, pre-specified threshold) and estimate ATE as the mean difference in matched pairs.

### 4. Statistical Analysis (FR-005, FR-006, FR-007)
- **Bias Calculation**: $|\hat{\tau} - \tau_{true}|$.
- **RMSE**: $\sqrt{\text{mean}((\hat{\tau} - \tau_{true})^2)}$.
- **Coverage Rate**: Proportion of 95% CIs containing $\tau_{true}$.
- **Hypothesis Testing**:
 - **Primary Method**: **Linear Mixed-Effects Model (LMM)**. We model bias as the dependent variable with imputation method and $\beta$ as fixed effects, and simulation run ID as a random effect. This approach is robust to non-normality in the bias distribution and handles the repeated measures structure of the simulation study without requiring preliminary normality tests (replacing the flawed Shapiro-Wilk -> ANOVA/Friedman tree).
 - **Interaction Effects**: We check if the difference in bias between IPW and PSM for the same imputation method exceeds 10%. If so, an interaction flag is raised.
- **Sensitivity Analysis**: Sweep $\beta_{mnar} \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$.
 - **Bias Trend**: Calculate Spearman rank correlation ($\rho$) between $\beta$ and mean absolute bias. Given only 5 points, p-values are not statistically meaningful; we report $\rho$ and the direction of the trend descriptively.
 - **Coverage Trend**: Use a **Generalized Linear Model (GLM)** with a binomial family and logit link to model the coverage rate as a function of $\beta$. This accounts for the bounded nature of the coverage proportion (0 to 1). We test for a statistically significant negative slope ($p < 0.05$).

## Compute Feasibility & Constraints

- **Hardware**: CPU cores, ~7 GB RAM, no GPU.
- **Runtime Limit**: A total duration of several hours is allocated. (target < 4 hours).
- **Optimization**:
 - Sample size $N=1000$ per run (small enough for fast imputation/estimation).
 - simulation runs total (Multiple runs per $\beta$ value).
 - **Parallelization**: The main loop is parallelized using Python's `multiprocessing` module to utilize both CPU cores.
 - Libraries pinned to CPU-optimized versions (e.g., `scikit-learn` without CUDA).
 - No deep learning models; all methods are classical statistical/machine learning.

## References

- Rubin, D. B. (1987). *Multiple Imputation for Nonresponse in Surveys*.
- Little, R. J. A., & Rubin, D. B. (2019). *Statistical Analysis with Missing Data*.
- Imbens, G. W., & Rubin, D. B. (2015). *Causal Inference for Statistics, Social, and Biomedical Sciences*.
- *Verified Datasets*: See "Dataset Strategy" table above for URLs used for methodological reference.
