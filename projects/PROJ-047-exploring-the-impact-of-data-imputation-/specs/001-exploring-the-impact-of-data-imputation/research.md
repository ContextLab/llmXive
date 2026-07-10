# Research: Exploring the Impact of Data Imputation Methods on Causal Inference

## Executive Summary

This research investigates the robustness of standard imputation methods (Mean, KNN, MICE) under Missing Not At Random (MNAR) conditions in causal inference. By simulating data with known ground-truth Average Treatment Effects (ATE) and injecting missingness dependent on unobserved outcomes, we quantify the bias introduced when standard MAR-based assumptions are violated. The study sweeps the MNAR parameter $\beta$ to identify failure thresholds and compares Inverse Probability Weighting (IPW) vs. Propensity Score Matching (PSM) to assess estimator interaction.

## Dataset Strategy

**Synthetic Data Generation**:
This study relies entirely on **synthetically generated data** to ensure control over the MNAR mechanism and the ground-truth ATE. No external real-world datasets are used for the primary analysis because real-world MNAR mechanisms are unobservable and ground-truth ATEs are unknown.

*   **Source**: `code/simulation/scm_generator.py` (Custom implementation).
*   **Rationale**: As per FR-001 and Constitution Principle VI, the "ground truth" is the parameter of the generative model. External datasets (even those listed in the verified block like `pppereira3/HW4_REGRESSION_mnar`) are unsuitable because:
    1.  They do not provide the *true* unobserved $Y$ values required to verify the MNAR mechanism's exact parameters.
    2.  They lack a known, fixed ATE for bias calculation.
    3.  They may have complex, undocumented missingness patterns that cannot be precisely parameterized by $\beta$.

**Verified Datasets Note**:
The verified datasets block contains sources for MNAR data (e.g., `pppereira3/HW4_REGRESSION_mnar`), but these are **NOT** used for the primary simulation. They may be referenced in `research.md` for context on existing MNAR datasets, but the core experimental data is generated locally to satisfy the "Synthetic Ground Truth Integrity" principle.

## Methodology

### 1. Synthetic Data Generation (FR-001, US-1)
*   **Model**: Structural Causal Model (SCM) with binary treatment $T$, continuous outcome $Y$, and confounders $X$.
*   **Ground Truth**: The ATE ($\tau_{true}$) is explicitly set (e.g., 0.5) during generation.
*   **MNAR Mechanism**: Missingness $M$ is generated via logistic regression: $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$.
    *   $\beta$ controls the strength of MNAR.
    *   **$\beta=0$ corresponds to MAR (control)**.
 * **Dynamic Tuning of $\alpha$**: For each $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$, the intercept $\alpha$ is dynamically adjusted to target a **fixed missingness rate** (e.g., [deferred]). This ensures that the effect of $\beta$ is isolated from the effect of missingness volume.
    *   **Verification**: All runs are included in the analysis regardless of the Spearman correlation between $M$ and unobserved $Y$. No arbitrary threshold (e.g., $\rho > 0.5$) is used to discard runs, allowing the sensitivity analysis to capture the full spectrum of MNAR strength, including subtle effects. The acceptance criteria in the spec (US-1) regarding $\rho > 0.5$ is a verification of the *mechanism generation* (ensuring the code works) but is NOT applied as a filter to the final dataset for sensitivity analysis.
*   **Bias Definition**: The 'bias' metric is defined as the absolute difference between the estimator on imputed data and the **known generative parameter** ($\tau_{true}$), not an empirical estimate from observed data. This avoids tautological confusion about identifiability under MNAR. The observed data under MNAR is inherently biased; the study measures how much the imputation methods fail to recover the *generative parameter*.

### 2. Imputation Pipeline (FR-003, US-2)
*   **Methods**:
    *   **Mean**: Simple mean imputation (baseline).
    *   **KNN**: k-Nearest Neighbors ($k=5$) using Euclidean distance.
    *   **MICE**: Multivariate Imputation by Chained Equations (using `IterativeImputer` in scikit-learn with `RandomForestRegressor` or `BayesianRidge`).
*   **Constraint**: All methods run on CPU. No GPU acceleration.

### 3. Causal Estimation (FR-004, US-2)
*   **IPW**: Inverse Probability Weighting using propensity scores estimated via logistic regression on **imputed data**.
*   **PSM**: Propensity Score Matching (1:1 nearest neighbor matching) on **imputed data**.
*   **Handling MNAR Bias in Propensity Scores**: The plan explicitly acknowledges that under MNAR, the imputation introduces bias into the propensity scores (since $Y$ influences $M$, and $M$ influences the imputed $Y$, which influences $T$ estimation if $T$ is correlated with $Y$). This bias is an expected component of the total error being measured. No attempt is made to restrict to complete cases, as that would defeat the purpose of testing imputation methods. The study measures the total bias (imputation + estimation) relative to the generative parameter.

### 4. Bias Quantification & Statistical Testing (FR-005, FR-006, US-3)
*   **Metrics**:
    *   Absolute Bias: $|\hat{\tau} - \tau_{true}|$
    *   RMSE: $\sqrt{\frac{1}{n}\sum(\hat{\tau}_i - \tau_{true})^2}$
    *   Coverage Rate: Proportion of 95% CIs containing $\tau_{true}$.
*   **Statistical Tests**:
    *   **Default**: **Friedman test** for comparing bias across 3 methods (Mean, KNN, MICE) within each beta level. The Shapiro-Wilk test has been removed to avoid 'test of assumptions' bias.
    *   **Post-hoc**: **Nemenyi test** for pairwise comparisons if Friedman test is significant ($p < 0.05$).
    *   **Robustness**: Bootstrap CIs for median differences.
*   **Sensitivity Analysis**: Spearman rank correlation ($\rho$) between $\beta$ and mean absolute bias. Expect $\rho > 0.9$.

## Statistical Rigor & Assumptions

*   **Multiple Comparisons**: When comparing 3 methods $\times$ 2 estimators, we apply the **Nemenyi test** (a non-parametric post-hoc test) for pairwise comparisons following a significant Friedman test.
* **Sample Size/Power**: We target **200 replications per beta level** ([deferred] total runs). This is a **simulation study**, so power is driven by the number of replications (200 per level) to stabilize the bias estimate, not by the sample size of a single dataset.
*   **Causal Assumptions**:
    *   The study acknowledges that under MNAR, the true ATE is **not identifiable** from observed data.
    *   Claims are strictly about the *bias relative to the generative parameter*, not about recovering a real-world causal effect.
    *   No causal claims are made about the external world; the "truth" is the simulation parameter.
*   **Collinearity**: VIF checks are performed. Runs with VIF > 10 are flagged/excluded to prevent unstable estimates (Edge Case).
*   **Measurement Validity**: The instruments are the synthetic variables themselves, defined by the SCM. The "validity" is ensured by the deterministic generation code.

## Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (multi-core CPU, substantial RAM).
*   **Strategy**:
    *   Data generation and imputation are vectorized (numpy/pandas).
    *   MICE uses `IterativeImputer` with a limited number of iterations and a lightweight estimator (Ridge).
    *   Causal estimation uses `statsmodels` (IPW) and `causalinference` or custom PSM (efficient numpy implementation).
 * **Runtime**: [deferred] runs total. Estimated time per run: [deferred] (CPU). Total: [deferred].
    *   **Memory**: $N=1000$ datasets are small (~1MB). A sufficient number of runs fits easily in standard system memory..
    *   **No GPU**: All libraries (scikit-learn, statsmodels) default to CPU.

## Decision Rationale

*   **Why Synthetic?**: Real MNAR datasets do not have known ground truth. Without known $\tau_{true}$, bias cannot be calculated.
*   **Why IPW & PSM?**: To isolate imputation error from estimator error (Constitution Principle VII).
*   **Why Friedman/Nemenyi?**: To rigorously test if differences in bias are statistically significant, accounting for the repeated-measures nature of the simulation (same seed, different methods) without relying on normality assumptions.
*   **Why 200 Replications per Level?**: To ensure statistical power for the Friedman test and to stabilize the bias estimates for the sensitivity analysis.
*   **Why Dynamic $\alpha$?**: To isolate the effect of the MNAR mechanism ($\beta$) from the effect of missingness volume.