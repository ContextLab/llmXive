# Research: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Methodology Overview

This research quantifies the stability of machine learning models by measuring the variance in their performance across different data subsets. The core hypothesis is that model stability is inversely related to dataset size and complexity. We employ a **Repeated K-Fold Cross-Validation** protocol (10 folds × 10 repeats = 100 runs for large datasets; adaptive folds for small datasets) to generate a robust empirical distribution of performance metrics (Accuracy, F1) for each model-dataset pair.

### Statistical Framework

1. **Stability Metric**: The primary metric is **Log-Transformed Variance** (log(σ²)) of Accuracy and F1 scores. This measures **absolute stability** independent of the mean performance (task difficulty), avoiding the tautology where CV (σ/μ) is mathematically tied to mean accuracy. Coefficient of Variation (CV) is retained as a secondary descriptive metric only.
2. **Correlation Analysis**: **Spearman rank correlation** is computed between **log(variance)** and **log(n_samples)** and **log(n_features)**. This transformation is pre-specified and applied unconditionally to handle non-normality and non-linearity, avoiding data-dependent decisions.
3. **Collinearity Control**: Variance Inflation Factors (VIF) are calculated for n_samples and n_features. If VIF > 5, the analysis switches to **partial correlation** or **multivariate regression** to control for collinearity, rather than relying on univariate tests.
4. **Hypothesis Testing**: A non-parametric **Permutation Test** compares the distributions of **squared deviations from the mean** (variance proxies) across the three models (Logistic Regression, Random Forest, Linear SVM) for each dataset. The test permutes model labels to assess if the variance distributions differ significantly.
5. **Multiple Comparison Correction**: The **Benjamini-Hochberg (BH)** procedure is applied to the set of all correlation and permutation p-values to control the False Discovery Rate (FDR), as mandated by FR-007.

## Dataset Strategy

The study requires a diverse set of binary classification datasets spanning a wide range of sample sizes and feature dimensions. We prioritize **open, directly downloadable datasets** to ensure reproducibility on CI runners without authentication. The following **Verified Datasets** table lists the 15 specific datasets selected, all of which are native binary classification tasks from OpenML/UCI.

### Verified Datasets

The datasets below were selected by the **Reference-Validator Agent** to ensure they are binary classification tasks, open, and span the required sample size range (N=101 to N=48,842).

| Dataset Name (Source) | OpenML ID | Verified URL | N_samples | N_features | Usage Strategy |
|-----------------------|-----------|--------------|-----------|------------|----------------|
| UCI Wine | a moderate number of instances | ` | 178 | 13 | Low N, Low Features |
| UCI Zoo | [a subset] | ` | 101 | 16 | Low N, Low Features |
| UCI Heart (Cleveland) | A subset of the dataset | ` | 303 | 13 | Low N, Medium Features |
| UCI Breast Cancer (Wisconsin) | A substantial dataset | ` | 569 | 30 | Low N, High Features |
| UCI Pima Indians Diabetes | A dataset of moderate size | ` | 768 | 8 | Medium N, Low Features |
| UCI Credit Approval | a moderate-sized dataset | ` | 690 | 15 | Medium N, Medium Features |
| UCI Ionosphere | a moderate number of instances | ` | 351 | 34 | Medium N, High Features |
| UCI Sonar | [dataset size] | ` | 208 | 60 | Medium N, High Features |
| UCI Bank Marketing | a subset of the dataset | ` | 45211 | 17 | High N, Medium Features |
| UCI Adult (Income) | a subset of instances | ` | 48842 | 14 | High N, Medium Features |
| UCI Covertype | [variable feature count] | ` | 581012 | 54 | High N, High Features (Sampled) |
| UCI Magic Gamma Telescope | a dataset of moderate scale | ` | 19020 | 10 | Medium N, Medium Features |
| UCI Haberman Survival | a dataset of moderate size | ` | 306 | 3 | Low N, Low Features |
| UCI Liver Disorders | [dataset size] | ` | 345 | 6 | Low N, Low Features |
| UCI Breast Cancer (Original) | a substantial dataset | ` | 683 | 9 | Low N, Low Features |

*Summary*: The selected 15 datasets span **N=101 to N=48,842** (excluding Covertype which is sampled to fit constraints) and feature dimensions from 3 to 60. All are native binary classification tasks.

**Dataset Selection Protocol**:
1. **Ingestion**: Load the verified URLs via `openml` library or direct HTTP fetch.
2. **Filtering**: Select 15 distinct datasets that meet the N_samples ∈ [100, 100000] and binary target criteria.
3. **Diversity Check**: Ensure the selected set covers low (<1000), medium (1k-10k), and high (>10k) sample sizes. **If the set does not span the full range, the pipeline halts with a critical error.**
4. **Fallback**: No fallback. The pipeline requires a diverse set of datasets to satisfy the correlation analysis requirements.

**Data Availability & Feasibility**:
- **Streaming**: Large datasets (e.g., Adult, Covertype) will be processed using `datasets.load_dataset(..., streaming=True)` or chunked loading to avoid OOM errors on the 7 GB RAM runner.
- **Caching**: Once downloaded, files are stored in `data/` with SHA-256 checksums recorded.
- **No Gated Data**: No datasets requiring registration (e.g., ADNI, UK Biobank) are used.

## Statistical Rigor & Assumptions

### Multiple Comparison Correction
- **Method**: Benjamini-Hochberg (BH) procedure.
- **Justification**: FR-007 requires FWER/FDR control. BH is preferred over Bonferroni for exploratory analysis with N=15 tests to maintain statistical power while controlling false positives.
- **Implementation**: `statsmodels.stats.multitest.multipletests` with method `'fdr_bh'`.

### Power & Sample Size
- **Evaluations**: **100 total evaluations** per model-dataset pair.
- **Adaptive Folds**: For datasets with N < 200, the fold count K is reduced (e.g., K=5) to ensure the test set size is sufficient (≥10 samples), while maintaining exactly 100 evaluations (K folds × R repeats = 100).
- **Limitation**: For very small datasets, the variance estimate may be noisy, but the adaptive strategy ensures the statistical power (number of evaluations) remains constant.

### Causal & Measurement Validity
- **Associational Claims**: The study identifies correlations between dataset properties and stability. No causal claims are made regarding dataset size *causing* instability; rather, it is a predictive relationship.
- **Collinearity**: N_samples and N_features may be correlated. The plan will calculate VIF; if VIF > 5, partial correlation or multivariate regression will be used to isolate the effect of sample size.
- **Zero Variance**: If a model achieves [deferred] accuracy on all 100 runs (std=0), the log-variance is undefined. These cases are handled by assigning a log-variance of -999 (a sufficiently small number) and excluding them from log-log regression, while including them in the Spearman correlation on raw log-variance.

## Compute Feasibility

- **CPU-First**: All models (Logistic Regression, Random Forest, Linear SVM) are CPU-tractable.
- **Memory**: Streaming ensures memory usage remains within acceptable limits for the target hardware.
- **Time**: [deferred] model fits. With average fit time < 1 second per fold (small datasets) to 30 seconds (large datasets), the total runtime is estimated at 2-4 hours on 2-core CPU, well within the 6-hour limit.
- **GPU Escape Hatch**: **Not applicable.** The Constitution mandates CPU-only execution for this project scope.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Insufficient Binary Datasets** | Cannot reach 15 datasets. | Pipeline halts with critical error if the verified set does not span the required range. |
| **Network Failure** | Pipeline halts. | Implement `try/except` blocks around download; skip failed dataset, log warning, continue (only if >15 valid remain). |
| **Zero Variance** | Log-variance calculation crash. | Handle `std=0` explicitly; assign log-variance = -999. |
| **Time Budget Exceeded** | Job timeout. | Add a "progress check" every 10 datasets; if runtime > 4h, reduce repeats to 5 (log warning) or stop. |
