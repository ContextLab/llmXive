# Research: Exploring the Impact of Data Imputation Methods on Causal Inference

## Problem Definition

The research question investigates how standard imputation methods (Mean, KNN, MICE) distort causal effect estimates when the missingness mechanism is Missing Not At Random (MNAR). Specifically, when the probability of missingness in the outcome variable depends on the unobserved outcome values themselves, standard methods that assume Missing At Random (MAR) or Missing Completely At Random (MCAR) are theoretically expected to produce biased estimates. This project aims to quantify that bias and identify the threshold of MNAR strength where standard methods fail catastrophically.

## Dataset Strategy

**Strategy**: Synthetic Data Generation.  
**Rationale**: No external real-world dataset exists with a verified, parameterized MNAR mechanism where the ground-truth ATE is known. External datasets (e.g., the "Verified datasets" list provided) contain MNAR *labels* or *imputed* versions but do not provide the underlying ground truth required to calculate bias ($|\hat{\tau} - \tau_{true}|$).  
**Implementation**:
- **Source**: Synthetic generation via `code/generate_data.py`.
- **Variables**: Binary Treatment ($T$), Continuous Outcome ($Y$), Continuous Confounders ($X$).
- **Ground Truth**: The ATE ($\tau_{true}$) is defined by the structural parameters of the data generation process.
- **MNAR Mechanism**: Missingness indicator $M$ is generated via $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$.
- **Fidelity Check**: Instead of attempting to recover $\beta$ from observed data (which is impossible under MNAR), we verify the mechanism by correlating $M$ with the *latent* (true) $Y$ during generation. This is a valid simulation-only check.

**Verified Datasets Reference**:
*Note: As per the "Dataset-variable fit" assumption in the spec and the lack of verified MNAR ground-truth datasets in the provided list, no external dataset URLs are cited for the primary analysis. The "Verified datasets" list contains generic MNAR or imputation-related datasets that lack the necessary ground-truth causal parameters for this specific simulation study.*

## Methodology

### 1. Data Generation (FR-001, FR-002)
- **Model**: Linear Structural Causal Model (SCM).
  - $X \sim \mathcal{N}(0, I)$
  - $T = \mathbb{I}(\gamma^T X + \epsilon_T > 0)$ (Binary treatment)
  - $Y = \tau_{true} T + \delta^T X + \epsilon_Y$ (Continuous outcome)
- **MNAR Injection**:
  - **Target Missingness Rate**: Fix a target rate (e.g., $r = 0.30$).
  - **Solve for $\alpha$**: Given $\beta$ and target $r$, numerically solve for $\alpha$ such that $E[M] \approx r$. This decouples the missingness *proportion* from the MNAR *strength* ($\beta$).
  - Calculate $M$ for each observation: $M_i \sim \text{Bernoulli}(\text{logit}^{-1}(\alpha + \beta Y_i))$.
  - Mask $Y_i$ if $M_i = 1$.
- **Parameters**:
  - $\tau_{true} = 2.0$ (Fixed ground truth).
  - $\beta \in \{0.1, 0.5, 1.0, 2.0\}$ (Sensitivity sweep).
  - $N = 1000$ per replication.
  - Replications = 200.

### 2. Imputation Strategies (FR-003)
- **Mean Imputation**: Replace missing $Y$ with $\bar{Y}_{obs}$.
- **KNN Imputation**: $k=5$ neighbors based on $X$ and observed $Y$.
- **MICE**: 5 iterations, assuming MAR (using `IterativeImputer` or `fancyimpute` MICE).
- **Constraint**: All methods run on CPU. MICE convergence failures will be caught, logged, and the replication flagged/excluded.

### 3. Causal Estimation (FR-004)
- **Baselines**:
  - **Oracle**: Estimate ATE on *complete* data (no missingness). This represents the best possible estimator performance.
  - **Complete Case**: Estimate ATE on data with missing rows removed (Listwise Deletion). This represents standard practice without imputation.
- **Imputed Estimates**:
  - Apply IPW and PSM to each imputed dataset.
  - **Interpretation**: The "Bias" metric is defined as $|\hat{\tau}_{imp} - \tau_{true}|$. This captures **Total Deviation** (imputation error + estimator failure under MNAR).
  - **Isolation**: By comparing $\hat{\tau}_{imp}$ to $\hat{\tau}_{oracle}$, we can estimate the specific error introduced by the imputation step.

### 4. Statistical Analysis (FR-005, FR-006, FR-007)
- **Bias Calculation**: $Bias = |\hat{\tau} - \tau_{true}|$.
- **RMSE**: $\sqrt{Bias^2 + Var(\hat{\tau})}$.
- **CI Coverage**: Calculate the confidence interval for each estimate. Coverage = proportion of replications where $\tau_{true} \in [CI_{lower}, CI_{upper}]$.
- **Repeated-Measures ART ANOVA**: Use Aligned Rank Transform with **Seed** as a blocking factor (or Random Effect in a Mixed Model) to test $H_0$: Bias distributions are equal across imputation methods, accounting for the non-independence of methods within the same seed.
- **Sensitivity Plot**: Bias vs. $\beta$ for each method.
- **Breakdown Point**: Identify $\beta$ where Mean Imputation Bias > 10% of $\tau_{true}$.
- **Variance Check**: Verify that the variance of bias across replications is non-trivial (not zero) to ensure the ANOVA tests a real distribution.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since the primary test is the omnibus Repeated-Measures ART ANOVA (one test per $\beta$ level), family-wise error is controlled. If post-hoc pairwise comparisons are performed, Bonferroni correction will be applied.
- **Power**: 200 replications are assumed sufficient to detect moderate effect sizes in bias distributions ($p < 0.05$). If power is low, the limitation will be explicitly stated.
- **Causal Framing**: Claims are strictly about the *recovery of the known ground truth* in a simulation. No causal claims about real-world populations are made.
- **Collinearity**: Synthetic $X$ variables will be generated with controlled correlation ($\rho < 0.7$) to avoid VIF > 10.
- **MNAR Validity**: The logistic model is the standard parametric form for MNAR in simulation literature (Little & Rubin).
- **Estimator Limitations**: Explicitly acknowledged that IPW/PSM on imputed data do not correct for MNAR; the study measures the *total* error resulting from this mismatch.

## Compute Feasibility

- **Hardware**: GitHub Actions free tier (multi-core CPU, 7GB RAM).
- **Strategy**:
  - Data generation and imputation are vectorized (NumPy/Pandas).
  - MICE iterations are limited to a sufficient number to ensure convergence.
  - KNN $k=5$ is computationally light for $N=1000$.
  - Total runtime estimated: < 2 hours for 200 replications (well within 6h limit).
  - No GPU required; all libraries (`scikit-learn`, `statsmodels`, `linearmodels`) have CPU wheels.

## Risks & Mitigations

- **Risk**: MICE fails to converge.
  - **Mitigation**: Catch exception, log seed, retry with 10 iterations or exclude from ANOVA with a flag.
- **Risk**: Extreme sparsity (>90% missing) causes estimator failure.
  - **Mitigation**: Check missingness rate; if >90%, flag result as "unreliable" but do not crash.
- **Risk**: VIF > 10 in confounders.
  - **Mitigation**: Regenerate $X$ if VIF > 10 detected.

## References

- Little, R. J., & Rubin, D. B. (2019). *Statistical Analysis with Missing Data*. Wiley.
- Rubin, D. B. (1976). Inference and missing data. *Biometrika*.
- Wobbrock, J. O., et al. (2011). The Aligned Rank Transform for Nonparametric Factorial Analyses. *UIST*.

