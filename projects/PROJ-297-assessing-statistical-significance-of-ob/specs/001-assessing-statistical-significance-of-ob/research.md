# Research: Assessing Statistical Significance of Observed Correlations in Public Databases

## 1. Problem Statement & Methodology

The goal is to distinguish non-random association (signal) from random noise in multivariate datasets using network statistics derived from correlation matrices. Standard parametric tests (e.g., t-tests on correlations) assume specific distributions that may not hold for complex network metrics. We adopt a **permutation-based non-parametric approach**:

1. **Null Hypothesis ($H_0$)**: There is no association between variables; any observed correlation structure is due to random chance.
2. **Method**: Independently permute the values of each variable $N=1,000$ times. This preserves the marginal distribution of each variable (mean, variance, skew) but destroys all pairwise dependencies.
 * *Note*: Permutation count is 1,000 to ensure runtime feasibility on 2-CPU runners while maintaining sufficient p-value resolution (0.001) for α=0.05.
3. **Statistics**: For each permuted dataset, compute:
 * Mean Absolute Correlation ($\bar{|r|}$)
 * Edge Density ($D$): Proportion of pairs with $|r| > 0.3$
 * Max Absolute Correlation ($r_{max}$)
 * Average Clustering Coefficient ($C$)
 * *Note*: Clustering coefficient is calculated exactly using `networkx.average_clustering`. For datasets with >50 variables, the permutation count for this specific statistic is reduced to 500 to ensure runtime, while other statistics use [deferred].
4. **P-value**: Two-sided empirical p-value: $p = \frac{\text{count}(|stat_{perm}| \ge |stat_{obs}|) + 1}{N + 1}$.
5. **Correction**: Apply Benjamini-Yekutieli (BY) to the set of all tests (valid datasets × 4 statistics) to control FDR at 0.05.
 * *Note*: Constitution Principle VII requires amendment to mandate BY instead of BH due to arbitrary dependence of network statistics.

## 2. Dataset Strategy

The project requires a set of multivariate datasets from the UCI Machine Learning Repository. Per the "Verified Accuracy" principle, we use direct, verified URLs from the UCI archive.

**Primary Dataset List (Verified Sources):**

| Dataset Name | Source URL | Variable Count Check | Status |
|:--- |:--- |:--- |:--- |
| Wine | ` | Must be $\ge 20$ | Conditional |
| Abalone | ` | Must be $\ge 20$ | Conditional |
| Breast Cancer | ` | Must be $\ge 20$ | Conditional |
| Student Performance | ` | Must be $\ge 20$ | Conditional |
| Air Quality | ` | Must be $\ge 20$ | Conditional |
| Concrete | ` | Must be $\ge 20$ | Conditional |

**Fallback Dataset Strategy**:
If the primary list yields fewer than 3 valid datasets (after dropping rows with missing values and removing constant variables, and checking for >=20 continuous variables), the pipeline will automatically query the UCI repository for the next available multivariate datasets with >=20 continuous variables. Potential fallback candidates include 'Parkinsons', 'Libras', 'Isolet', 'Seeds', and 'Wine Quality'. The pipeline will continue until 3 valid datasets are found or the UCI repository is exhausted.

**Data Availability Gate**:
* The pipeline will attempt to load each dataset.
* Rows with missing values will be dropped.
* Constant variables will be removed.
* If a dataset has < 20 continuous variables after cleaning, it is **excluded**.
* If fewer than 3 valid datasets remain after the fallback strategy, the pipeline **halts** with an error. This ensures the study has sufficient power and scope.

**Note on Variable Counts**: Standard UCI versions of "Wine" (13 variables) and "Breast Cancer" (9 variables) typically have < 20 variables. The pipeline will exclude them if they fail the check. The "Student Performance" and "Air Quality" datasets are more likely to meet the threshold. The "Concrete" dataset has 9 variables (excluding the target) and may also be excluded. The "Abalone" dataset has 8 variables (excluding target) and may be excluded. The fallback strategy ensures the study can proceed even if the primary list fails.

## 3. Statistical Rigor & Assumptions

* **Multiple Comparisons**: We test $K$ hypotheses (where $K$ = valid datasets × 4). Using Benjamini-Yekutieli (BY) is required because network statistics are highly correlated (dependent tests). Constitution Principle VII requires amendment to reflect this.
* **Causal Framing**: All results are framed as "non-random association". No causal claims are made.
* **Permutation Validity**: Independent permutation destroys pairwise structure but preserves marginals. This is valid for testing the null hypothesis of independence.
* **Collinearity**: Network statistics (density, mean correlation) are derived from the same matrix. They are dependent; BY handles this.
* **Power**: With $N=1,000$, the resolution of p-values is $1/1001 \approx 0.001$. This is sufficient for $\alpha=0.05$.
* **Spearman Correlation Handling**: Spearman correlation matrices are computed for exploratory comparison (satisfying FR-002). However, they are **excluded** from the primary network graph construction, null model generation, and significance testing. Including Spearman would substantially increase the number of tests, requiring a stricter correction and potentially reducing power for the primary Pearson-based hypothesis. This decision maintains a bounded test scope and statistical rigor.

## 4. Compute Feasibility

* **Hardware**: GitHub Actions (2 CPU, 7GB RAM).
* **Strategy**:
 * Data is loaded into memory (pandas).
 * Permutations are vectorized using `numpy` where possible.
 * 1,000 permutations × valid datasets is computationally feasible within 6 hours on CPU.
 * **Clustering Coefficient**: Calculated exactly using `networkx`. The dynamic reduction of permutation count for clustering in large datasets ensures this step completes within the time limit.
 * **Runtime Monitoring**: The pipeline will log runtime per dataset. If a single dataset exceeds 1 hour, a warning is issued, but the pipeline continues.

## 5. Sensitivity Analysis

* **Thresholds**: $|r| \in \{0.1, 0.2, 0.3, 0.4, 0.5\}$.
* **Output**: A table showing the count of significant findings (after BY correction) for each threshold.
* **Robustness**: If the number of significant findings varies drastically across thresholds, the findings are considered less robust.