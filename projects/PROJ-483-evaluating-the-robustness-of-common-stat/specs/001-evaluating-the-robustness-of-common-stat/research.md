# Research: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

## 1. Problem Statement & Gap Analysis

Standard statistical tests (t-test, ANOVA, Chi-squared) assume independent and identically distributed (i.i.d.) observations. Public datasets, particularly those derived from longitudinal studies, sensor networks, or clustered populations, frequently violate this assumption through temporal autocorrelation, hierarchical nesting, or spatial clustering.

**The Gap**: While theoretical literature exists on the inflation of Type I error rates under non-independence, there is a lack of **empirical evidence** quantifying this inflation across **real-world public datasets** with varying degrees of dependency strength. Most studies rely on synthetic data generation, which may not capture the complex correlation structures found in actual data.

**Research Question**: How does the false-positive rate of standard statistical tests inflate when applied to public datasets with varying degrees of non-independence, and which tests are most vulnerable?

## 2. Dataset Strategy

The project adheres strictly to the **Constitution Principle II (Verified Accuracy)** and the **Verified datasets** block provided in the prompt. No new URLs are invented.

| Dataset Name | Source Type | Verified URL | Suitability for Study |
|:--- |:--- |:--- |:--- |
| **UCI Wine Quality (Red)** | UCI / CSV | `https://huggingface.co/datasets/UCI/wine-quality-red/resolve/main/winequality-red.csv` | Contains continuous variables (e.g., alcohol, pH) suitable for t-tests and ANOVA. Large N allows for hierarchical dependency injection. |
| **UCI HAR (Human Activity)** | UCI / CSV | ` | Time-series sensor data. Ideal for **Temporal (AR(1))** dependency injection. We will use the *window-level* aggregated features as the observation unit, and inject AR(1) dependency across the sequence of windows. |
| **UCI Adult** | UCI / CSV | `https://huggingface.co/datasets/UCI/adult/resolve/main/adult.csv` | Contains continuous (age, hours) and categorical variables. Suitable for t-tests and Chi-squared. |

**Data Availability Strategy**:
- **Download**: All datasets are fetched via `huggingface_hub` or direct HTTP GET to the verified URLs.
- **Streaming**: If a dataset exceeds available RAM (unlikely for these specific UCI subsets, but possible for full HAR), `datasets.load_dataset(..., streaming=True)` will be used to process chunks.
- **Null Construction**: For each dataset, we will identify a pair of variables where the null hypothesis is plausibly true (or artificially enforced via permutation) *after* dependency injection.

**Addressing the "Synthetic Data" Concern**:
The plan explicitly rejects generating *synthetic* data to replace the dataset. Instead, we use **Real Data + Injected Dependency**.
1. Download Real Data (UCI).
2. Inject Dependency (AR(1) for HAR, Cluster-Effect for Wine/Adult) into the real values (specifically, the residuals of a null model).
3. Apply Permutation to the *injected* data to create the null.
This satisfies FR-002: "construct a null hypothesis by first injecting the controlled dependency structure into the original data, and THEN applying random permutation."

**Dataset Exclusion**:
- **UCI DROP**: Excluded as it is a reading comprehension dataset without continuous numerical variables suitable for t-tests/ANOVA.
- **Spatial Dependency**: Dropped for the current verified datasets as none contain explicit spatial coordinates. We will only test Temporal and Hierarchical structures.

## 3. Methodology & Statistical Rigor

### 3.1 Dependency Injection Methods
1. **Temporal (AR(1))**: Applied to time-ordered data (HAR).
 - Model: $X_t = \rho X_{t-1} + \epsilon_t$, where $\rho \in \{0, 0.1, 0.2, 0.3, 0.5\}$.
 - Implementation: `numpy` vectorized recursion applied to the sequence of window-level features.
2. **Hierarchical (Cluster-Effect Injection)**: Applied to cross-sectional data (Wine, Adult).
 - Method: Instead of resampling (Block Bootstrap), we generate correlated noise $\epsilon_i$ with intra-cluster correlation $\rho$ and add it to the residuals of the outcome variable. This induces dependency without altering N or the marginal distribution of the original data.
 - Implementation: Generate a cluster ID for each observation, then add a cluster-specific random effect + individual noise.
3. **Spatial**: **Skipped** for this study as no verified datasets have explicit spatial coordinates.

### 3.2 Null Construction (FR-002)
The correct approach for testing Type I error under non-independence is to generate data where the *null is true* (no mean difference) but the *error terms are correlated*.
1. **Fit a Null Model**: Fit a model to the real data assuming no effect (e.g., $Y = \mu + \epsilon$) to extract residuals $\epsilon_{real}$.
2. **Inject Dependency**: Generate a new error term $\epsilon_{new}$ that has the desired correlation structure (AR(1) or Cluster-Effect) but the same variance as $\epsilon_{real}$.
3. **Construct Null Data**: Create $Y_{null} = \mu + \epsilon_{new}$.
4. **Permute Labels**: For the t-test/ANOVA, permute the group labels $X$ relative to $Y_{null}$. This breaks the association while preserving the correlation structure in the error term.
5. **Run Test**: Perform the statistical test on $(X_{permuted}, Y_{null})$.

This ensures the null hypothesis is true (no mean difference) but the data has the desired non-independence.

### 3.3 Monte Carlo Simulation
- **Replications**: $N_{rep} = 10,000$ per configuration (Test $\times$ Dependency $\times$ Strength).
- **Significance**: $\alpha = 0.05$.
- **Metric**: Observed Type I Error Rate = (Count of $p < 0.05$) / $N_{rep}$.
- **Precision Verification**: Calculate the 95% Clopper-Pearson CI width. If width > 0.01 (±0.5%), log a warning (SC-003).

### 3.4 Statistical Rigor & Assumptions
- **Multiple Comparisons**: When testing multiple dependency strengths ($r=0.1, 0.2, 0.3, 0.5$), we will report the trend but **not** adjust the alpha for the simulation itself, as the simulation *is* the experiment to observe the trend. However, if we perform a trend test (e.g., logistic regression of significance vs. $r$), we will report the p-value.
- **Power Analysis**: For US-3, we will inject a known effect size ($\delta=1.0\sigma$) into the dependent data and measure power.
- **Collinearity**: If predictors are definitionally related (e.g., sum of parts), we will not claim independent effects. We will report descriptive correlations.
- **Causal Claims**: None. The study is purely **associational** regarding the relationship between dependency strength and error rate inflation. No causal inference on the dataset variables themselves is claimed.

## 4. Compute Feasibility

- **Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, 7GB RAM).
- **Strategy**:
 - **CPU-First**: All simulations use `numpy` vectorization. No GPU required for standard statistical tests.
 - **Memory**: Streaming or chunked processing for HAR if needed. Wine/Adult fit easily.
 - **Time**: 10,000 replications of a t-test on $N=1000$ takes milliseconds. 10k reps $\times$ 5 dependency levels $\times$ 3 tests $\approx$ 150k tests total. Even with overhead, this is well under a standard workday.
- **No GPU Escape Hatch Needed**: The statistical tests (t, F, Chi-sq) are lightweight. No transformer fine-tuning or diffusion models are involved.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use Real UCI Data** | Satisfies FR-001 and Constitution II. Synthetic data cannot validate robustness on *public dataset* structures. |
| **Cluster-Effect Injection (vs Block Bootstrap)** | Block Bootstrap resamples data, altering N and distribution. Cluster-Effect Injection adds correlated noise, preserving N and distribution. |
| **Inject Dependency into Residuals** | Ensures the null hypothesis is true while preserving the correlation structure in the error term. |
| **10,000 Replications** | Meets SC-003 precision target ($\pm [deferred]$). [deferred] would be too noisy for small error rates. |
| **Clopper-Pearson CIs** | Required for accurate reporting of rare events (Type I errors) where Wald intervals fail. |
| **No Spatial Testing** | No verified datasets have spatial coordinates. Forcing a spatial test would be methodologically unsound. |
