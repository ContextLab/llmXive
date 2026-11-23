# Research: Detecting Statistical Power Drift in Replicated Studies

## Research Question
Do reported statistical power estimates in published replication studies exhibit a systematic temporal decline, indicating a drift toward lower-powered replications over time, independent of changes in effect sizes and sample sizes?

## Methodology

### 1. Power Calculation (FR-001, Principle VI)
Post-hoc power will be calculated for each study using the reported effect size (Cohen's *d* or odds ratio) and sample size ($N$).
- **Formula**: For a two-tailed t-test (approximation for Cohen's *d*), power is the probability that the test statistic exceeds the critical value $t_{crit}$ given the non-centrality parameter $\delta = d \sqrt{N/2}$.
- **Parameters**: $\alpha = 0.05$ (fixed per spec).
- **Handling**: Studies missing $N$ or $d$ will be excluded (FR-008).

### 2. Drift Modeling (FR-002, FR-003, Principle VII)
To avoid the tautology of predicting Power while including its deterministic inputs (Effect Size, Sample Size) as covariates, the outcome is defined as **Residual Power**.
- **Stage 1 (Residualization)**: Fit a preliminary model `Power ~ EffectSize + SampleSize` to obtain residuals. These residuals represent the unexplained variance in power after accounting for the inputs.
- **Stage 2 (Drift Model)**: Fit a Linear Mixed-Effects Model (LMM) or Generalized Linear Mixed Model (GLMM) with a logit link if residuals are skewed:
  $$ \text{ResidualPower}_{ij} = \beta_0 + \beta_1(\text{Year}_i) + u_{0j} + \epsilon_{ij} $$
  - **Fixed Effects**: `Year`.
  - **Random Effects**: `(1 | field)`, `(1 | original_study_id)`.
  - **Alternative**: If the model fails to converge or residuals are highly non-normal, use a GLMM with a logit link function or robust standard errors.
- **Test**: Likelihood Ratio Test (LRT) comparing the full model against a reduced model (without `Year`) to assess $\beta_1$ significance.
- **Assumption**: Observational data; claims are associational, not causal.

### 3. Robustness Validation (FR-004, FR-005, FR-007)
- **Permutation Test (Year)**: Shuffling `Year` labels [deferred] times to generate an empirical null distribution of the slope $\beta_1$.
- **Sensitivity Analysis**: Sweeping $\alpha \in \{0.01, 0.05, 0.10\}$. For each $\alpha$, the drift significance is re-evaluated.
  - **False Positive Rate (FPR) Estimation**: The FPR for each alpha threshold is estimated empirically using the permutation null distribution. It is calculated as the proportion of permuted slopes that exceed the critical value for that alpha. This provides a data-driven estimate of the false positive rate under the null hypothesis.
  - **Output**: `drift_significant` (boolean) and `false_positive_rate` (float) for each threshold.
- **Input Permutation (FR-007)**: Shuffling `EffectSize` and `SampleSize` while holding `Year` constant. This tests if the observed drift is an artifact of the *distribution* of inputs. By randomizing the inputs, we create a null distribution of slopes under the assumption that the relationship between inputs and year is random. Comparing the observed slope to this null validates the stability of the regression algorithm against input distribution changes.

### 4. Cross-Field Aggregation (FR-006)
Residual drift estimates ($\beta_1$) stratified by `field` will be combined using DerSimonian-Laird inverse-variance weighting to account for heterogeneity. This method calculates a weighted average of field-specific slopes, where weights are inversely proportional to the variance of the slope estimate plus a heterogeneity component ($I^2$).

## Dataset Strategy

| Dataset Name | Source URL | Variables Needed | Status |
| :--- | :--- | :--- | :--- |
| OSF Replication Project (Nosek et al.) | `https://osf.io/v7g23/` (or direct CSV/Parquet link from OSF) | `year`, `effect_size`, `sample_size`, `field` | **Verified** |
| OSF Replication Project (HuggingFace Mirror) | `https://huggingface.co/datasets/osf-replication-project/data` | `year`, `effect_size`, `sample_size`, `field` | **Verified** |

**Strategy**:
1. **Primary Source**: Attempt to load the OSF Replication Project dataset (Nosek et al.) which explicitly contains the required statistical columns.
2. **Fallback**: If the primary source is inaccessible, use the HuggingFace mirror.
3. **Data Merging**: If a study ID exists in multiple sources, the value from the primary source is used. If missing in primary, the value from the secondary source with the highest data completeness is selected.
4. **Missing Data**: Rows lacking `effect_size` or `sample_size` will be dropped with a warning log (FR-008).
5. **Graph Covariates**: The 'OSF Graph Covariate Data' datasets are **excluded** as they do not contain the required statistical columns (effect size, N) and are not suitable for power calculation.

## Compute Feasibility & Rationale

- **CPU-First Approach**: The analysis relies on classical statistics (LMM/GLMM via `statsmodels`), permutation tests (sufficient iterations), and standard plotting. These are computationally tractable on a -core CPU within the 3.14-hour limit.
- **No GPU Required**: No deep learning or transformer models are involved. The "GPU escape hatch" is not needed for this project.
- **Memory Management**: Data will be processed in chunks if necessary. The permutation test will be implemented with efficient vectorization (NumPy) to avoid Python loops where possible.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: The sensitivity sweep involves multiple alpha thresholds. The interpretation will focus on the *stability* of the result rather than a single p-value correction, as the goal is robustness checking.
- **Power Limitations**: If the dataset is small (< 30 studies per field), the random effects model may not converge. The plan includes a fallback to a fixed-effects model with robust standard errors if convergence fails.
- **Collinearity**: `Year` and `SampleSize` may be correlated (studies getting larger over time). The model includes `Year` as the fixed effect of interest and `SampleSize` as a covariate in the residualization step to isolate the *residual* drift. Collinearity will be checked via VIF; if severe, the interpretation will be restricted to "drift adjusted for sample size" without claiming independence.
- **Causal Claims**: The study is observational. The plan explicitly avoids causal language (e.g., "causes underpowered studies") and frames results as "temporal association."
- **Bounded Outcome**: Since Power is bounded [0, 1], the plan includes a fallback to a GLMM with a logit link or robust standard errors if the residuals of the power estimates show significant skewness or heteroscedasticity.