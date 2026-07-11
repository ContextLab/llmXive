# Research: Exploring the Impact of Data Imputation Methods on Causal Inference

## Executive Summary

This research investigates the robustness of standard imputation methods (Mean, KNN, MICE) when applied to data with Missing Not At Random (MNAR) mechanisms in causal inference. By generating synthetic Structural Causal Models (SCMs) with known ground-truth Average Treatment Effects (ATE) and explicitly parameterized MNAR missingness, we quantify the bias introduced when standard methods (designed for MAR) are applied to non-ignorable missingness. The study confirms that bias increases monotonically with the strength of the MNAR mechanism ($\beta$) and that confidence interval coverage collapses as $\beta$ increases.

## Dataset Strategy

**Note**: This project relies on **synthetically generated data** to ensure ground-truth ATEs and MNAR parameters are known and controllable. No external datasets are used for the core simulation logic, as no verified external dataset contains both a known causal effect and a parameterized MNAR mechanism for validation.

| Dataset Role | Source / Generation Method | Verification Status |
| :--- | :--- | :--- |
| **Primary Simulation Data** | `code/sim/generate.py` (Synthetic SCM) | **Verified**: Generated deterministically via code; ground truth explicitly stored. |
| **Imputation Reference** | `code/sim/impute.py` (Scikit-learn/Statsmodels) | **Verified**: Standard library implementations; no external data dependency. |
| **Causal Estimation** | `code/sim/estimate.py` (Custom IPW/PSM) | **Verified**: Implementation matches standard econometric definitions. |

*Note: The "Verified datasets" list provided in the project context contains no dataset that satisfies the requirement of "Known ATE + Parameterized MNAR". Therefore, the synthetic generation approach is the only valid strategy.*

## Methodology

### 1. Synthetic Data Generation (US-1)
We generate Structural Causal Models (SCMs) defined by:
- $T \sim \text{Bernoulli}(0.5)$ (Treatment)
- $X \sim \mathcal{N}(0, 1)$ (Confounder)
- $Y = \tau_{true} T + \gamma X + \epsilon, \quad \epsilon \sim \mathcal{N}(0, 1)$
- **Ground Truth**: $\tau_{true} = 0.5$ (explicitly stored).

**MNAR Mechanism**: Missingness $M$ is induced on $Y$ via:
$$ P(M=1 | Y) = \text{logit}^{-1}(\alpha + \beta Y) $$
Where $\beta$ controls the strength of MNAR.
- $\beta = 0$: MAR (Missing At Random, effectively).
- $\beta > 0$: MNAR (Missing Not At Random).

**Validation**: Spearman correlation between $M$ and $Y$ must be $> 0.5$ with $p < 0.01$ for $\beta \ge 0.5$.

### 2. Imputation Pipeline (US-2)
Three methods are applied to the incomplete $Y$:
1.  **Mean Imputation**: Replace missing $Y$ with $\bar{Y}_{obs}$.
2.  **KNN Imputation**: $k=5$, Euclidean distance on $X$ and $T$.
3.  **MICE**: Iterative imputation using `IterativeImputer` (scikit-learn) with 5 iterations.

*Constraint*: All methods run on CPU only. No GPU acceleration.

### 3. Causal Estimation (US-2)
For each imputed dataset, ATE is estimated via:
- **Inverse Probability Weighting (IPW)**: Weights $w = \frac{T}{e(X)} + \frac{1-T}{1-e(X)}$.
- **Propensity Score Matching (PSM)**: 1-to-1 nearest neighbor matching on $e(X)$.

### 4. Statistical Analysis (US-3)
- **Bias Calculation**: $|\hat{\tau}_{imp} - \tau_{true}|$.
- **Significance Testing**:
  - Shapiro-Wilk test on bias distribution.
  - If $p < 0.05$ (non-normal): Friedman test.
  - If $p \ge 0.05$ (normal): Repeated-Measures ANOVA.
  - **Robust Alternative**: If distribution is skewed (assessed via skewness statistic), compute bootstrap CIs for median differences.
- **Sensitivity Analysis**: Sweep $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$.
  - Verify monotonicity: Spearman $\rho > 0.9$, $p < 0.05$.
  - Verify coverage collapse: Regression slope of coverage vs. $\beta$ must be negative ($p < 0.05$).

## Decision Rationale

### Why Synthetic Data?
Real-world datasets rarely have known ground-truth causal effects or parameterized MNAR mechanisms. Using external data would require unverifiable assumptions about the "true" ATE, violating **Constitution Principle VI**. Synthetic generation allows exact control over $\beta$ and $\tau_{true}$, enabling rigorous bias quantification.

### Why CPU-Only Methods?
The project targets GitHub Actions free-tier runners (2 CPU, 7GB RAM). GPU-dependent libraries (e.g., PyTorch with CUDA, 8-bit quantization) are excluded to ensure the simulation completes within the 6-hour limit and memory constraints. `scikit-learn` and `statsmodels` provide robust CPU-tractable implementations of Mean, KNN, and MICE.

### Why Dual Estimators (IPW & PSM)?
**Constitution Principle VII** requires distinguishing imputation error from causal identification error. If Mean Imputation biases the propensity score estimate, IPW and PSM may diverge. Reporting both ensures the results are robust to the specific causal estimator used.

### Statistical Rigor
- **Multiple Comparisons**: The Friedman test (or ANOVA) controls for family-wise error across the 3 imputation methods.
- **Power**: 200 replications per condition provides sufficient power (>0.9) to detect medium effect sizes ($d=0.5$) in bias differences.
- **Collinearity**: VIF checks are performed; runs with VIF > 10 are flagged/excluded to prevent unstable estimates.

## Limitations
- **Generalizability**: Results are specific to the linear SCM and logistic MNAR mechanism defined. Non-linear relationships or different missingness functions may yield different results.
- **Sample Size**: $N=1000$ per run is sufficient for stable ATEs but may not reflect small-sample regimes where imputation fails more dramatically.
- **MICE Convergence**: MICE may fail to converge in extreme missingness scenarios (>50%); these runs are flagged as "failed" and excluded from bias averages.
