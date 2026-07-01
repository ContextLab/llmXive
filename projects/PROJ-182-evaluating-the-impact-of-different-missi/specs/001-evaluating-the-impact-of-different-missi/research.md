# Research: Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs

## Research Goal

To quantify the bias, variance, and confidence interval coverage of four RD estimation strategies (Naïve, MI, IPW, Selection) under three missing data mechanisms (MCAR, MAR, MNAR) using a controlled Monte-Carlo simulation.

## Dataset Strategy

This study relies on **synthetic data generation** rather than external real-world datasets. This approach is mandated by the spec (FR-001, US-1) to ensure:
1.  **Known Ground Truth**: The true discontinuity effect is fixed and known, allowing precise bias calculation (SC-003).
2.  **Controlled Missingness**: The ability to strictly enforce MCAR, MAR, and MNAR definitions without confounding real-world noise (FR-002).
3.  **Reproducibility**: Exact replication of the data generation process via pinned random seeds (Constitution Principle I).

**No external datasets are used.** The "Verified datasets" list provided in the prompt is not utilized because the study design explicitly requires synthetic data generation with specific, controlled missingness patterns that cannot be guaranteed in existing public datasets.

### Synthetic Data Generation Logic
- **Running Variable ($X$)**: Uniformly distributed $U[-1, 1]$.
- **Outcome ($Y$)**: $Y = \alpha + \beta X + \tau D + \epsilon$, where $D = 1[X \ge 0]$, $\tau$ is the true treatment effect.
- **Covariates ($Z$)**: Standard normal $N(0, 1)$, independent of $X$.
- **Exclusion Restriction ($Z^*$)**: A specific covariate generated as $N(0, 1)$, **independent of $X$ and $Y$**, but used **only** in the missingness equation for the Heckman model. This satisfies the identification requirement for the Selection Model.
- **Missingness Mechanisms**:
  - **MCAR**: Missingness indicator $R \sim Bernoulli(p)$, independent of $X, Y, Z, Z^*$.
  - **MAR**: $R \sim Bernoulli(\text{logit}^{-1}(\gamma_0 + \gamma_1 Z))$, dependent on $Z$ but not $Y$ or $Z^*$.
  - **MNAR**: $R \sim Bernoulli(\text{logit}^{-1}(\gamma_0 + \gamma_1 Y + \gamma_2 Z^*))$. **Note**: The dependence on $Y$ creates the MNAR condition, while $Z^*$ provides the necessary exclusion restriction for identification. The strength of the MNAR dependence ($\gamma_1$) will be swept to ensure significant bias.

## Methodology

### 1. Data Generation (FR-001, FR-002)
- **Model**: Triangular kernel RD design.
- **Parameters**: Sample size $N$ (deferred), True Effect $\tau$ (deferred).
- **Missingness Rates**: [deferred], [deferred], [deferred] (deferred exact rates in config).
- **MNAR Strength**: $\gamma_1$ will be set to values ensuring $|r| > 0.5$ between mask and $Y$ (as per US-1 Acceptance 3).
- **Validation**:
  - **Generation Validation**: Chi-square tests for MCAR independence; correlation tests for MAR/MNAR dependencies. **Crucially, the validation of the MNAR mechanism ($|r| > 0.5$) uses the ground truth $Y$ to confirm the *data generation code* is correct.** This is distinct from estimator evaluation, which does not have access to $Y$.
  - **Estimator Validation**: Estimators are evaluated based on their ability to recover $\tau$ from the *observed* (masked) data only.

### 2. Estimation Strategies (FR-003, FR-004, FR-005, FR-008)
- **Naïve Local-Linear**: Imbens-Kalyanaraman (IK) bandwidth selection. Fallback to [deferred] of running variable range if IK < 5% (FR-003). **Definition**: Applies **listwise deletion** (complete-case analysis) on the observed data. Under MNAR, this is expected to yield biased estimates because the missingness depends on $Y$.
- **Multiple Imputation (MI)**: `mice` logic (5 imputations) with Rubin's rules for pooling (FR-004).
- **Inverse-Probability Weighting (IPW)**: Logistic regression for propensity score. **Constraint**: The model must be trained **only on observed data** ($X, Z, Z^*$) and **cannot use the ground truth $Y$**. This ensures that under MNAR (where $R$ depends on unobserved $Y$), the IPW weights are misspecified, demonstrating the theoretical failure of IPW in this setting (FR-005).
- **Selection Model**: Heckman-type joint model. **Requirement**: Uses $Z^*$ as the exclusion restriction to identify the selection equation. Convergence limit: a predefined maximum number of iterations. Returns NaN on failure (FR-008).

### 3. Aggregation & Metrics (FR-006, FR-007)
- **Replications**: 1,000 per configuration.
- **Metrics**:
  - **Bias**: $\text{Mean}(\hat{\tau} - \tau_{true})$ (SC-003).
  - **RMSE**: $\sqrt{\text{Mean}((\hat{\tau} - \tau_{true})^2)}$ (SC-002).
  - **Coverage**: Empirical confidence interval coverage rate vs. nominal coverage rate (SC-001).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Not applicable in the traditional hypothesis testing sense, as this is a simulation study comparing estimator properties. However, the analysis will report all metrics without selective reporting to avoid publication bias.
- **Power/Sample Size**: Power is inherent in the Monte-Carlo design (1,000 replications). The simulation sample size $N$ will be chosen to ensure stable estimation of the RD effect in the complete data case.
- **Causal Inference**: Claims are strictly descriptive of estimator performance under simulated conditions. No causal claims about real-world populations are made (Assumption: Inference Framing).
- **Measurement Validity**: `mice` and logistic regression are standard, validated tools. The Heckman model is a standard theoretical correction for selection bias, **now identified via the exclusion restriction $Z^*$**.
- **Collinearity**: Synthetic covariates are generated independently of the running variable to avoid definitional collinearity (Assumption: Predictor Collinearity).

## Compute Feasibility

- **Target**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
  - Use `numpy` and `scipy` for fast vectorized operations.
  - Avoid heavy deep learning libraries.
  - Limit replication count to 1,000 as per spec; if runtime exceeds 6h, reduce $N$ or replications (with logging).
  - **No GPU**: All estimators run on CPU.
  - **Memory**: Process replications in batches if necessary to stay under 7GB RAM.

## Risk Mitigation

- **Heckman Convergence**: If the selection model fails to converge (common in small samples or extreme MNAR), the system logs the error and returns NaN (FR-008), preventing pipeline crash.
- **Bandwidth Selection**: If IK bandwidth is invalid, fallback to fixed [deferred] rule (FR-003).
- **Runtime**: If 1,000 replications exceed 6h, the plan allows for a "reduced" run (e.g., 100 replications) for debugging, with full run scheduled for the final CI job.
- **Identification Failure**: The inclusion of $Z^*$ ensures the Heckman model is identified. If $Z^*$ is accidentally correlated with $Y$, the model will be invalid; strict independence checks will be performed during data generation.