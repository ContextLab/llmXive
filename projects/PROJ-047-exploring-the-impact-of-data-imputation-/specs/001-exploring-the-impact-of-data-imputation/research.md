# Research: Exploring the Impact of Data Imputation Methods on Causal Inference

## Problem Statement

Standard imputation methods (Mean, KNN, MICE) assume Missing At Random (MAR) or Missing Completely At Random (MCAR). When data is Missing Not At Random (MNAR)—where the probability of missingness depends on the unobserved value itself—these methods can introduce severe bias into causal effect estimates. This study quantifies that bias under controlled MNAR mechanisms to identify failure thresholds for standard practices.

## Dataset Strategy

**Note**: This study relies on **synthetic data generation** to ensure ground-truth knowledge of the Average Treatment Effect (ATE) and the MNAR mechanism parameter ($\beta$). No external real-world dataset is used for the primary simulation, as real-world data lacks known ground truth for bias calculation.

However, to validate the *imputation logic* and *causal estimators* against known distributions, we reference the following verified datasets for unit testing and sanity checks where applicable (though not for the main simulation):

| Dataset Type | Verified URL | Usage |
|--------------|--------------|-------|
| **Synthetic Dataset (Reference)** | ` | Unit test: Verify synthetic generator produces similar distributions to known synthetic benchmarks. |
| **MNAR (Reference)** | ` | Unit test: Verify MNAR injection logic produces similar missingness patterns (correlation with outcome) as verified MNAR data. |
| **KNN (Reference)** | ` | Unit test: Verify KNN imputation logic against a known KNN dataset structure. |
| **MICE (Reference)** | ` | Unit test: Verify MICE convergence logic. |
| **IPW (Reference)** | ` | Unit test: Verify IPW estimator logic. |
| **PSM (Reference)** | ` | Unit test: Verify PSM estimator logic. |

**Decision**: The primary simulation uses a custom `synthetic_data.py` module. The verified datasets above are used *only* for unit testing specific components (imputation, estimation) to ensure they function correctly before the main simulation loop. The main simulation generates its own data to guarantee the "Ground Truth" integrity required by Constitution Principle VI.

## Methodology

### 1. Synthetic Data Generation (SCM)
- **Model**: Linear Structural Causal Model (SCM).
 - $T = \text{Bernoulli}(\text{logit}^{-1}(\gamma X))$
 - $Y = \alpha T + \beta X + \epsilon$
 - **Ground Truth ATE**: $\alpha$ (explicitly stored via regenerate_ground_truth).
- **MNAR Injection**:
 - Missingness indicator $M$ generated via logistic model: $P(M=1|Y) = \text{logit}^{-1}(\alpha_{mnar} + \beta_{mnar} Y)$.
 - $\beta_{mnar}$ is swept: $\{0.0, 0.2, 0.5, 0.8, 1.0\}$.
 - $\beta_{mnar} = 0$ represents MAR/MCAR (baseline).
 - $\beta_{mnar} > 0$ represents MNAR (missingness depends on unobserved $Y$).

### 2. Imputation Strategies
- **Mean**: Replace missing $Y$ with column mean. Bootstrap resampling for robust SEs/CIs.
- **KNN**: $k=5$ nearest neighbors (Euclidean distance on $T, X$). Bootstrap resampling for robust SEs/CIs.
- **MICE**: `sklearn.experimental.enable_iterative_imputer()` with `IterativeImputer` (estimator=BayesianRidge, max_iter=10). Rubin's Rules for combining SEs/CIs across imputations.
- **Constraint**: All run on CPU. No GPU.

### 3. Causal Estimation
- **IPW**: Inverse Probability Weighting using propensity scores.
- **PSM**: Propensity Score Matching (nearest neighbor, caliper=0.05).
- **Output**: Estimated ATE ($\hat{\tau}$) for each (Imputation, Estimator) pair.

### 4. Bias Quantification & Statistical Testing
- **Bias**: $|\hat{\tau} - \tau_{true}|$ where $\tau_{true}$ is the generative parameter (regenerated via regenerate_ground_truth).
- **RMSE**: $\sqrt{\frac{1}{N}\sum(\hat{\tau}_i - \tau_{true})^2}$.
- **Statistical Test (FR-006)** — Integrated Decision Tree:
 1. Shapiro-Wilk test on bias distribution.
 2. If $p < 0.05$ (non-normal) $\rightarrow$ **Friedman Test**.
 3. If $p \ge 0.05$ (normal) $\rightarrow$ **Repeated-Measures ANOVA**.
 4. **Independently** (always): If skewness > 1 or < -1 → Compute **Bootstrap CIs** (A sufficient number of iterations will be performed.) for difference in medians as robust alternative.
- **Sensitivity (FR-007, SC-005)**:
 - Sweep $\beta_{mnar}$.
 - Compute Spearman rank correlation (rho) and p-value for bias vs. beta.
 - Verify monotonic trend: rho > 0.9 AND p < 0.05. Write monotonicity_confirmed flag.
 - Compute regression slope for coverage vs. beta.
 - Verify negative slope: slope < 0 AND p < 0.05. Write negative_slope_confirmed flag.

### 5. Research Question Clarification

**What this study measures**: The *failure* of standard imputation methods to recover the *generative parameter* (tau_true) under MNAR. This is empirical (not tautological) because the bias depends on the specific imputation method chosen and the MNAR mechanism's strength.

**What this study does NOT claim**: That standard methods can recover the true causal effect under MNAR (they cannot; the effect is not identifiable from observed data alone).

**Independent Validation**: Compute bias relative to an IPW estimator on complete data (oracle benchmark). If bias relative to the oracle is large, the imputation methods are failing. If bias relative to the oracle is small but bias relative to the generative parameter is large, the MNAR mechanism is simply distorting the parameter (expected behavior, not a failure).

### 6. Computational Feasibility
- **Hardware**: GitHub Actions Free Tier (A modest computational setup with multiple CPU cores and sufficient memory to support the research question. The method involves [Method]. References include [References].).
- **Strategy**:
 - Sample size $N=1000$ per run.
 - runs total (40 per $\beta$ level).
 - Parallelize with `joblib` (n_jobs=2) or sequential.
 - **No GPU**: CPU-only libraries.
 - **Runtime**: Target < 4 hours.

## References

| Decision | Rationale |
|----------|-----------|
| **Synthetic Data** | Real-world data lacks known ATE. Simulation is the only way to quantify bias against "truth". |
| **MNAR Mechanism** | Logistic dependency on $Y$ is the standard parametric form for MNAR studies. Linear-logistic interaction is standard; non-linear mechanisms are future work. |
| **IPW + PSM** | Constitution Principle VII requires dual estimation to separate imputation error from identification error. |
| **Statistical Decision Tree** | FR-006 mandates robust testing. Integrated into single workflow to ensure robustness always executed. |
| **CPU-Only** | GitHub Actions free tier has no GPU. Heavy models are infeasible. |
| **Oracle Benchmark** | Provides independent validation beyond generative parameter. |
| **MNAR Validation** | Kolmogorov-Smirnov test validates mechanism against observable data properties. |
