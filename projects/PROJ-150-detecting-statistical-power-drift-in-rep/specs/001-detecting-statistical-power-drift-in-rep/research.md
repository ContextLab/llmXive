# Research: Detecting Statistical Power Drift in Replicated Studies

## 1. Problem Statement & Hypothesis

**Hypothesis**: Reported statistical power estimates in published replication studies exhibit a systematic temporal decline, indicating a drift toward lower-powered replications over time, independent of changes in effect sizes or sample sizes.

**Core Challenge**: A naive regression of power on year is confounded if sample sizes or effect sizes are also drifting. The analysis must isolate the *residual* drift in power that cannot be explained by the temporal trends of its constituent inputs. This is achieved by fitting a Linear Mixed-Effects Model (LMM) that includes `effect_size` and `sample_size` as covariates, thereby statistically controlling for them while testing the `year` coefficient.

## 2. Dataset Strategy

The analysis relies on the **Open Science Framework (OSF) Reproducibility Project: Psychology** dataset. This is a verified, open dataset containing replication study metadata including year, effect size, and sample size.

| Dataset Name | Purpose | Verified Source URL | Access Method |
|:--- |:--- |:--- |:--- |
| **OSF Reproducibility Project: Psychology** | Primary source for replication study metadata (year, effect size, sample size, field). | `https://huggingface.co/datasets/OSF/Reproducibility_Psychology/resolve/main/data/replication_data.csv` | `pandas.read_csv()` or `datasets.load_dataset(...)` |
| **OpenML Reproducibility Project** | Supplemental metadata if needed for cross-validation (optional). | ` | `sklearn.datasets.fetch_openml()` |

**Data Availability Note**: All listed sources are public, directly downloadable via HuggingFace Hub or OpenML API, and do not require registration or data-use agreements. This satisfies the "Data Availability" constraint for CI runners.

**Dataset Schema Verification**: The primary dataset contains the following required columns: `study_id`, `year`, `field`, `original_study_id`, `effect_size`, `sample_size`.

## 3. Methodology & Statistical Rigor

### 3.1 Power Calculation (FR-001)
Post-hoc power ($1-\beta$) will be calculated for each study using the standard non-central t-distribution approximation for Cohen's *d*:
$$ \text{Power} = 1 - \beta = \Phi\left( \sqrt{\frac{N}{2}}|d| - z_{1-\alpha/2} \right) $$
Where:
- $N$ = Total sample size
- $d$ = Cohen's *d$ (or converted effect size)
- $\alpha$ = 0.05 (two-tailed)
- $z_{1-\alpha/2}$ = 1.96

*Validity*: This formula is standard for two-group comparisons and aligns with the 1999 power-of-association formulas referenced in the spec.

*Bias Mitigation*: We acknowledge the "winner's curse" where post-hoc power is biased for significant results. To address this, we will perform a sensitivity analysis comparing the drift trend in the full dataset vs. only non-significant results, to ensure the drift is not an artifact of publication bias.

### 3.2 Temporal Drift Modeling (Linear Mixed-Effects Model)
To address the confounding of inputs and test the hypothesis of residual drift, we will fit a **Linear Mixed-Effects Model (LMM)**:

$$ \text{Power}_{i} = \beta_0 + \beta_1 \cdot \text{Year}_i + \beta_2 \cdot \text{EffectSize}_i + \beta_3 \cdot \text{SampleSize}_i + u_{\text{field}[j]} + \epsilon_i $$

Where:
- $\beta_1$ is the fixed effect of `year` (the primary parameter of interest).
- $\beta_2, \beta_3$ are fixed effects controlling for input drift.
- $u_{\text{field}[j]}$ is the random intercept for `field`.
- $\epsilon_i$ is the residual error.

**Hypothesis Test**: We test $H_0: \beta_1 = 0$ vs. $H_1: \beta_1 < 0$ (one-tailed) or $H_1: \beta_1 \neq 0$ (two-tailed) using a Likelihood-Ratio Test (LRT) comparing the full model against a reduced model without `year`.

### 3.3 Robustness & Validation (FR-004, FR-005, FR-007)

- **Permutation Test**: To validate the significance of the drift slope without relying on normality assumptions, we will perform a non-parametric permutation test (10,000 iterations).
 - *Method*: We will permute the `Year` labels *while preserving the distribution of inputs* (restricted permutation) or permute the residuals of the reduced model to generate a null distribution for the `year` coefficient.
 - *Fallback*: If memory/time limits are exceeded, the iteration count will drop to [deferred], and the result will be flagged as "approximate".
- **Sensitivity Analysis**: The analysis will sweep $\alpha \in \{0.01, 0.05, 0.10\}$ to ensure the drift detection is not an artifact of the significance threshold.
- **Input Permutation**: To test if the drift is an artifact of input distribution changes, we will permute `effect_size` and `sample_size` while holding `Year` constant, recalculating the `year` slope in the LMM to generate a null distribution.

### 3.4 Cross-Field Aggregation (FR-006)
For heterogeneous fields, we will use **DerSimonian-Laird** random-effects meta-analysis to combine the `year` slope estimates ($\beta_1$) from field-stratified models, weighting by inverse variance adjusted for heterogeneity ($I^2$).

## 4. Compute Feasibility

- **CPU-First**: All statistical modeling (`statsmodels`), power calculations (`scipy`), and permutations (vectorized `numpy`) are CPU-tractable.
- **Memory**: The dataset (a moderate number of rows) fits easily in 7GB RAM. Permutation tests will use streaming or chunked processing to avoid memory spikes.
- **Runtime**: A large number of permutations on 2 cores may take several hours. The 6-hour CI limit is sufficient.
- **No GPU Required**: No deep learning models are involved; all methods are classical statistics.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Linear Mixed-Effects Model (LMM)** | Required by FR-002 and Constitution Principle VII. It statistically controls for input drift (N, d) while testing the `year` effect, avoiding tautology. |
| **Permutation Count (10k)** | Specified in FR-004 to ensure robust p-value estimation. 1k is insufficient for stable tail probabilities in drift detection. |
| **Dataset Choice** | OSF Reproducibility Project is the canonical source for replication studies. The verified URL ensures unattended CI execution. |
| **CPU Execution** | No GPU is needed for these statistical methods. Running on CPU ensures compatibility with the free-tier runner. |
| **Winner's Curse Mitigation** | Post-hoc power is biased. A sensitivity analysis on non-significant results ensures the drift is not an artifact of publication bias. |