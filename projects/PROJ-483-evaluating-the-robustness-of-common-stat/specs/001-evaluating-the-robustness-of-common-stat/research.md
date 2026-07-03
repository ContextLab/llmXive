# Research: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

## Research Question
How do non-independence structures (temporal, hierarchical, spatial) in public datasets inflate Type I error rates and reduce statistical power for standard parametric tests (t-test, ANOVA, chi-squared), and which test-structure combinations are most vulnerable?

## Dataset Strategy

The project relies exclusively on the following verified datasets. Each dataset is evaluated for suitability based on variable types (continuous for t-test/ANOVA, categorical for chi-squared) and sample size (sufficient for statistical power).

| Dataset Name | Source URL | Variable Suitability | Notes on Suitability |
|:--- |:--- |:--- |:--- |
| **UCI HAR** | ` | Continuous (t-test/ANOVA) | Human Activity Recognition; continuous sensor features. Suitable for temporal dependency injection. |
| **UCI Shopper** | ` | Categorical/Continuous | Transactional data. Suitable for chi-squared (categorical) and t-test (spending). Temporal/Spatial injection applied to features based on transaction ID/timestamp. |
| **Synthetic Null Generator** | *N/A (Internal)* | Continuous/Categorical | Used for Type I error baseline. Generates independent X and Y, then injects dependency. Replaces invalid "Functional ANOVA" and "UCI DROP" sources. |

**Excluded Datasets**:
- **Functional ANOVA**: Removed. The source URL points to pre-computed results (JSON), not raw data suitable for dependency injection.
- **UCI DROP**: Removed. Text-based QA data lacks the continuous/categorical numerical variables required for t-test/ANOVA/chi-squared tests.
- **AggregatedMetric**: Removed. No verified source found.

**Dataset Selection Rationale**:
- **UCI HAR** and **UCI Shopper** are selected as primary candidates due to their structured nature and verified availability.
- **Sampling Strategy**: To ensure execution within the 7GB RAM limit, datasets with $N > 10,000$ will be randomly sampled to $N=2,000$ *before* dependency injection. This preserves distributional properties while reducing memory footprint.
- **Synthetic Data**: For Type I error estimation, we will generate synthetic data under the true null hypothesis (independent X and Y) to ensure the baseline is valid. Real datasets are used for descriptive validation and power analysis.

## Methodology & Simulation Design

### 1. Null Hypothesis Construction (FR-002) - "Generate-then-Inject" Paradigm
To establish a ground truth of "no effect" while violating the i.i.d. assumption, we strictly follow this protocol. **Permutation of labels on dependent data is explicitly rejected** as it fails to generate a valid null distribution when data points are non-exchangeable.

**For Type I Error Estimation (T-Test, ANOVA, Chi-Squared):**
1. **Generate**: Create synthetic data where X (predictor) and Y (outcome) are **independent** and identically distributed (i.i.d.).
 - *Continuous*: Draw X, Y from $N(0, 1)$.
 - *Categorical*: Draw X, Y from independent categorical distributions.
 - *Result*: The null hypothesis ($H_0: \text{no effect}$) is true by construction.
2. **Inject**: Apply the dependency structure (AR(1), Block Bootstrap, Spatial) **only to X** or **to the error term** of Y.
 - *Crucial*: Do NOT inject dependency into the joint distribution of X and Y in a way that creates a correlation between them. The dependency must exist within the variables themselves (e.g., temporal autocorrelation in X) or within the error structure, while X and Y remain uncorrelated.
 - *Result*: The test assumes independence (i.i.d.), but the data has a dependency structure. The null hypothesis (no effect) remains true.
3. **Test**: Run the statistical test. A significant result ($p < 0.05$) is a **Type I error**.

**For Power Analysis (US-3):**
1. **Generate**: Create data with a true effect (e.g., mean shift $\delta$ in Y based on X).
2. **Inject**: Apply dependency to X or the error term.
3. **Test**: Run the statistical test. A significant result is a **True Positive**.

**Chi-Squared Specifics**:
- Generate two independent categorical variables.
- Apply **Block Bootstrap** to the rows (observations) to induce hierarchical dependency.
- This violates the i.i.d. assumption of the chi-squared test while keeping the variables conditionally independent.

### 2. Dependency Injection Mechanisms (FR-003)
Three structures are implemented with tunable strength $r \in \{, 0.1, 0.2, 0.3, 0.5\}$:
- **Temporal (AR(1))**: $X_t = r X_{t-1} + \epsilon_t$. Implemented via `numpy` vectorized recursion. Applied to the predictor variable or the error term.
- **Hierarchical (Block Bootstrap)**: Data is resampled in contiguous blocks of size $B$. Blocks are resampled with replacement to simulate intra-cluster correlation. Applied to the row indices of the dataset.
- **Spatial (Kernel Smoothing)**:
 - **Proxy**: If a dataset lacks explicit spatial coordinates, a spatial proxy is derived **exclusively from the independent variables (features)**, strictly excluding the outcome variable.
 - **Method**: K-Means clustering on the feature subset to create cluster IDs. Dependency is injected by smoothing values within clusters.
 - **Constraint**: The outcome variable is never used to define the spatial structure, preventing definitional leakage.

### 3. Monte Carlo Simulation (FR-004, FR-005)
- **Replications**: 10,000 per configuration.
- **Tests**: Independent t-test, One-way ANOVA, Chi-squared test.
- **Metric**: Proportion of $p < 0.05$ (Type I Error) and Proportion of $p < 0.05$ under true effect (Power).
- **Confidence Intervals**: Clopper-Pearson exact intervals calculated for all error rates.
- **Logistic Regression**: As per Constitution Principle VII, a logistic regression model (p-value ~ dependency strength) is fitted for each configuration and saved to `results/logistic_models.pkl`.

### 4. Computational Feasibility (SC-004)
- **Vectorization**: All injection and testing loops are vectorized using `numpy` to avoid Python overhead.
- **Parallelism**: The replications are split into 4 batches ([deferred] each) processed sequentially to manage RAM, or parallelized via `multiprocessing` with shared memory if the runner allows (tested in CI).
- **Memory Cap**: Intermediate arrays are deleted immediately after aggregation.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: As this is a simulation study exploring error rates across conditions, the primary metric is the *observed* error rate. No family-wise error correction is applied to the *simulation results* themselves, as the goal is to measure the raw inflation. However, when reporting "thresholds" where error exceeds a predefined significance level, we will report the specific $r$ value with its confidence interval.
- **Power Justification**: A large number of replications provide a standard error of $\approx 0.002$ for a true rate of 0.05, satisfying the $\pm$ precision target (SC-003).
- **Causal Claims**: This is a simulation study. Claims are strictly about the *behavior of statistical tests* under specific data conditions, not about causal relationships in the real world.
- **Collinearity**: In the spatial proxy method, if the proxy variable is definitionally derived from the outcome, we will report the relationship descriptively and acknowledge the limitation, avoiding claims of "independent" effects. (Note: This is prevented by the "Feature-Only" proxy constraint).

## Edge Case Handling

- **Small Datasets ($N < 20$)**: These datasets will be skipped or flagged. The simulation requires sufficient degrees of freedom for the t-test/ANOVA to be valid.
- **Normality Violations**: The injected dependency may create non-normal distributions. The plan will report results for the standard tests (which assume normality) and, as a robustness check, the non-parametric equivalents (Mann-Whitney, Kruskal-Wallis) if time permits, but the primary focus remains on the parametric tests as per the spec.
- **Transaction Data (UCI Shopper)**: Dependency injection is applied to the feature space based on transaction timestamps or customer IDs. The label (purchase) is permuted *after* feature dependency is established to ensure the null is valid.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use "Generate-then-Inject"** | Resolves the "Inject-then-Permute" flaw. Ensures the null is true by construction while the i.i.d. assumption is violated. |
| **Synthetic Data for Type I Error** | Replaces invalid "Functional ANOVA" and "UCI DROP" sources. Guarantees a valid ground truth for error rate estimation. |
| **Feature-Only Spatial Proxy** | Prevents definitional leakage where the outcome influences the spatial structure. |
| **Vectorized NumPy** | Essential for fitting a large number of replications into 6 hours on 2 cores. |
| **Sample Large Datasets** | Prevents OOM errors on 7GB RAM runner while maintaining statistical properties. |
| **Reject Permutation for Type I Error** | Permutation on dependent data fails to generate a valid null distribution; synthetic generation is required. |