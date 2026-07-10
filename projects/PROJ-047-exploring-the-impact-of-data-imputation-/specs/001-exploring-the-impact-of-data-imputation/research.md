# Research: Exploring the Impact of Data Imputation Methods on Causal Inference

## 1. Research Question & Hypotheses

**Primary Question**: How do standard imputation methods (Mean, KNN, MICE), which assume Missing At Random (MAR), bias causal effect estimates when the true missingness mechanism is Missing Not At Random (MNAR)?

**Hypotheses**:
1.  **H1**: As the MNAR strength parameter $\beta$ increases, the absolute bias of all standard imputation methods will increase monotonically.
2.  **H2**: MICE will exhibit lower bias than Mean imputation at low $\beta$ (near MAR) but will fail to outperform Mean (or degrade faster) as $\beta$ increases, due to its reliance on MAR assumptions.
3. **H3**: The coverage rate of confidence intervals for all methods will drop significantly below the nominal level (e.g., [deferred]) as $\beta$ increases, indicating invalid inference.

## 2. Dataset Strategy

This study relies on **synthetic data generation** to establish a known ground truth (ATE) and controlled MNAR mechanisms. No external real-world datasets are used for the primary analysis, as real-world MNAR mechanisms are unobservable and true ATEs are unknown.

**Synthetic Data Generation**:
-   **Source**: `code/simulation/scm_generator.py` (Custom implementation).
-   **Mechanism**: Structural Causal Model (SCM) with binary treatment $T$, continuous outcome $Y$, and confounders $X$.
-   **Ground Truth**: The ATE $\tau_{true}$ is a fixed parameter in the SCM (e.g., $\tau_{true} = 0.5$).
-   **Missingness**: Injected via logistic model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$, where $\beta$ controls MNAR strength.
-   **Verification**: The generated dataset will be verified to ensure the correlation between $M$ and $Y$ (Spearman $\rho > 0.5$) and that the complete-data ATE matches $\tau_{true}$.

**Note on External Datasets**: While the "Verified datasets" block lists several MNAR-related datasets (e.g., `pppereira3/HW4_CLASSIFICATION_mnar`), these are **not** used for the primary simulation study because they do not provide a known ground-truth ATE for bias calculation. They may be referenced in the literature review for context on real-world MNAR challenges but are not part of the computational pipeline.

## 3. Methodology & Statistical Rigor

### 3.1 Simulation Design
-   **Replications**: 200 independent simulation runs per $\beta$ level.
-   **Sample Size**: $N=1000$ per run.
    -   *Justification*: The statistical power to detect differences between imputation methods depends on the number of *replications* (200), not the per-run sample size. A paired t-test on 200 bias estimates provides >85% power to detect a Cohen's $d \approx 0.31$. The per-run sample size of $N=1000$ is chosen to minimize the variance of the ATE estimator *within* each run, ensuring stable bias estimates, but the meta-analysis power is driven by the 200 replications.
-   **MNAR Sweep**: $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$.
-   **Imputation Methods**: Mean, KNN ($k=5$), MICE (multiple iterations).
-   **Causal Estimators**: Inverse Probability Weighting (IPW), Propensity Score Matching (PSM).

### 3.2 Bias Quantification & Standard Errors
-   **Metric**: Absolute Bias $|\hat{\tau}_{imp} - \tau_{true}|$ and Squared Error (per run).
-   **Coverage**: Proportion of 95% CIs containing $\tau_{true}$.
-   **Standard Error Correction**:
    -   **MICE**: Standard errors and confidence intervals will be calculated using **Rubin's Rules** to properly account for imputation uncertainty.
    -   **Mean/KNN**: Since these do not naturally produce multiple imputations, the entire pipeline (imputation + estimation) will be **bootstrapped** (e.g., 100 resamples) to derive robust standard errors and confidence intervals. This is critical because under MNAR, standard SE formulas are typically underestimated.

### 3.3 Statistical Testing
-   **Within-Run Correlation**: The bias values for different imputation methods *within* a single simulation run are correlated.
-   **Test Selection**: Instead of Repeated-Measures ANOVA or Friedman test, a **Linear Mixed-Effects Model (LMM)** will be used.
    -   **Model**: `Bias ~ ImputationMethod + (1 | run_id)`
    -   **Rationale**: This explicitly accounts for the non-independence of observations within each `run_id`, preventing Type I error inflation that would occur if the bias values were treated as independent.
-   **Trend Analysis**: Spearman rank correlation ($\rho$) between $\beta$ and bias to confirm monotonicity ($\rho > 0.9$, $p < 0.05$).

### 3.4 Causal Inference Assumptions
-   **Observational Nature**: The simulation assumes an observational structure where $T$ is confounded by $X$.
-   **Identification**: IPW and PSM are used to identify the ATE under the assumption of *no unmeasured confounding* (which holds in the simulation as $X$ is fully observed).
-   **MNAR Limitation**: Under the defined MNAR mechanism, the true ATE is **not identifiable** from observed data alone. The study measures bias relative to the *generative parameter*, not an external reality. This is explicitly documented.

### 3.5 Computational Feasibility
-   **Hardware**: GitHub Actions free-tier (standard CPU, standard RAM allocation).
-   **Constraints**: 
    -   No GPU usage.
    -   MICE implemented via `IterativeImputer` (scikit-learn) or `fancyimpute` with CPU-only settings.
    -   Data subset to $N=1000$ to ensure < 7GB RAM usage.
    -   Total runtime target: < 4 hours.

## 4. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **MNAR Mechanism Mis-specification** | Explicitly document that $\beta=0$ implies MAR. Verify correlation between $M$ and $Y$ in generated data. |
| **Imputation Convergence Failure** | Flag runs where MICE fails to converge; exclude from bias average but report failure rate. |
| **Collinearity in Synthetic Data** | Include VIF check; exclude runs with VIF > 10. |
| **Runtime Exceedance** | Optimize loops; use parallel processing for independent replications (if CI allows); reduce replications if necessary (document trade-off). |

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Synthetic Data over Real Data** | Real datasets lack known ground-truth ATE, making bias quantification impossible. |
| **Logistic MNAR Model** | Standard approach for simulation studies; allows precise control of $\beta$. |
| **IPW & PSM Dual Estimation** | Required by Constitution Principle VII to distinguish imputation error from estimation error. |
| **CPU-Only Implementation** | Mandatory for GitHub Actions free-tier compatibility (SC-003). |
| **LMM over ANOVA** | Correctly handles within-run correlation of bias estimates, reducing Type I error. |
| **Rubin's Rules/Bootstrapping** | Necessary to obtain valid confidence intervals under MNAR where standard errors are biased. |
