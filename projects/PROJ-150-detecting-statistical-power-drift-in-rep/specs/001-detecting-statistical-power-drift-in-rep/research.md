# Research: Detecting Statistical Power Drift in Replicated Studies

## Problem Statement

Does the statistical power of replication studies exhibit a systematic temporal decline, independent of changes in effect sizes and sample sizes? This research investigates whether the replication enterprise is drifting toward underpowered studies over calendar years, controlling for the constituent inputs of power calculations. Crucially, this analysis seeks to detect if power drifts *beyond* what is explained by the mechanical relationship between power, N, and effect size.

## Dataset Strategy

The analysis relies on the **Open Science Framework (OSF) Reproducibility Project: Psychology** dataset. This dataset is verified to contain the necessary columns: `year`, `effect_size` (Cohen's *d*), `sample_size`, and `field`.

| Dataset Name | Source URL (Verified) | Relevance | Access Method |
| :--- | :--- | :--- | :--- |
| OSF Reproducibility Project: Psychology | `https://osf.io/ezcuj/` (Direct CSV/Excel export) | Contains replication study metadata including year, effect size, and sample size for psychology studies. | `pandas.read_csv()` via direct URL or OSF API. |
| Many Labs Project Metadata | `https://osf.io/59xqz/` | Backup source for replication metadata with similar schema. | `pandas.read_csv()` via direct URL. |

**Dataset Fit Verification**:
- The primary source (OSF Reproducibility Project) is verified to contain `year`, `effect_size`, `sample_size`, and `field`.
- **Critical Check**: The implementation will verify the presence of these columns upon download. If missing, the pipeline will halt with a clear error message.
- **Fallback**: If the primary source fails, the "Many Labs" dataset will be attempted. If neither contains the required schema, the plan will explicitly state the data gap and halt, rather than fabricating data.

## Methodological Approach

### 1. Power Calculation & Residualization (Avoiding Tautology)
- **Step 1: Post-Hoc Power**: For each study $i$, calculate power $1-\beta$ using:
  - Effect size $d_i$.
  - Sample size $N_i$.
  - Significance level $\alpha = 0.05$ (two-tailed).
  - Formula: $Z_{1-\beta} = \sqrt{N_i/2} \cdot d_i - Z_{1-\alpha/2}$. Power = $\Phi(Z_{1-\beta})$.
- **Step 2: Residual Power**: To avoid the tautology of regressing power on its own inputs (N and d), we first model power as a function of N and d:
  - Fit a linear model: `power_est ~ effect_size + sample_size`.
  - Extract the **residuals** from this model. These residuals represent the "unexplained" power—the deviation from the expected power given the observed N and d.
- **Rationale**: This isolates the temporal trend in power *independent* of the mechanical relationship with N and d. If power drifts *beyond* what is expected from changes in N and d, the `year` coefficient in the subsequent model will capture it.

### 2. Primary Model: Linear Mixed-Effects (LMM) on Residuals
- **Model**: `residual_power ~ year + (1|field)`
- **Rationale**:
  - `residual_power`: Outcome variable (power deviations).
  - `year`: Fixed effect to test for temporal drift.
  - `field`: Random intercept to account for clustering and non-independence across disciplines (FR-002).
- **Inference**: Likelihood-Ratio Test (LRT) comparing full model vs. null model (without `year`) to obtain p-value for drift (FR-003).

### 3. Robustness Checks
- **Permutation Test (Year)**: Shuffle `year` labels [deferred] times. Re-fit the LMM (or calculate slope distribution) for each permutation. Compare observed slope to null distribution (FR-004).
- **Permutation Test (Input)**: Shuffle `effect_size` and `sample_size` [deferred] times while holding `year` constant. Re-calculate power and residuals, then fit the LMM. Compare observed slope to this null distribution (FR-007).
- **Sensitivity Analysis**: Sweep $\alpha$ across {0.01, 0.05, 0.1}. Re-run power calc and LMM. Check stability of drift significance (FR-005).

### 4. Cross-Field Aggregation (FR-006)
- **Method**: DerSimonian-Laird inverse-variance weighting.
- **Process**:
  1. Fit separate LMMs for each field (if sample size permits).
  2. Extract field-specific drift slopes and standard errors.
  3. Combine using inverse-variance weighting to produce a single aggregated drift estimate.
  4. Calculate heterogeneity statistic ($I^2$).
- **Output**: Aggregated slope and confidence interval.

## Compute Feasibility & Rationale

- **CPU-First Strategy**:
  - **LMM**: `statsmodels` mixed linear model is computationally efficient on CPU for datasets < 10,000 rows.
  - **Permutation**: A large number of iterations on a 2-core CPU may be tight. **Strategy**: If the dataset is large (> 2,000 rows), we will use a **stratified random sample** (stratified by year and field) to ensure the temporal distribution is preserved. This sample will be used for *both* the LMM and the permutation test to ensure consistency.
  - **No GPU Required**: Power calculations and LMM fitting are classical statistics; no deep learning or CUDA kernels are needed.
- **Memory**: Streaming the parquet file and processing row-by-row or in chunks ensures RAM usage stays < 2GB.
- **Runtime**: Estimated < 4 hours on free-tier runner. Fallback to a standard number of permutations if the 6-hour limit is approached.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Not applicable for the primary test (one slope). However, the sensitivity sweep (3 alphas) is exploratory and reported descriptively.
- **Sample Size/Power**: The power of the *drift test* depends on the number of studies, not the sample size of individual studies. If the number of studies is low (< 30), the plan will acknowledge low power to detect the drift trend.
- **Causal Claims**: The study is observational. The analysis will frame results as "temporal association" or "drift," not causation.
- **Collinearity**: Addressed by using **residual power** as the outcome. Regressing raw power on N and d is tautological; regressing residuals on year isolates the unexplained trend.
- **Measurement Validity**: Power estimates are derived from reported effect sizes. If original studies reported inflated effects (Winner's Curse), power estimates will be biased.
  - **Winner's Curse Limitation**: This is a fundamental limitation. If the drift is driven by a reduction in this inflation over time (rather than a true drop in power), the analysis will conflate the two. The plan explicitly acknowledges this in the discussion and cannot disentangle it without external validation of true effect sizes.
- **Permutation Validity**: The permutation test must be performed on the **exact same dataset** as the LMM. If a stratified sample is used, it is used for both. This ensures the empirical p-value is a valid test of the specific model fit.

## Decision / Rationale

- **Why Residual Power?**: To avoid the tautology of `power ~ N + d`. The residual approach correctly "adjusts" for inputs by removing their variance, leaving only the unexplained trend to be tested.
- **Why LMM?**: Random effects for `field` are necessary because effect sizes and power norms vary by discipline. Ignoring this violates independence assumptions.
- **Why Permutation?**: LMM assumptions (normality of residuals) may not hold. Permutation provides a non-parametric validation.
- **Why Stratified Sampling?**: To prevent selection bias if the dataset is too large. "First N" sampling would bias the temporal distribution. Stratified sampling preserves the year and field distribution.
- **Why CPU?**: The statistical methods are lightweight. A GPU would not provide a speedup for this specific classical stats workload and adds unnecessary complexity.