# Research: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Overview

This research document defines the dataset strategy, statistical methods, and computational approach for assessing model stability. It addresses the core research question: *How does the stability of standard machine learning models (measured by the Coefficient of Variation of performance metrics) relate to dataset properties (sample size, feature count), and are some algorithms inherently more stable than others?*

## Dataset Strategy

The project requires multiple binary classification datasets from the OpenML repository. Per the project constraints and the "Verified datasets" block provided in the specification, we will utilize the following verified OpenML IDs. These IDs are confirmed to be binary classification tasks and span a broad required sample size range.

**Verified Datasets List (Source: OpenML Verified List)**:
The following 15 datasets are verified binary classification tasks available via `sklearn.datasets.fetch_openml`. They span the required sample size diversity (Constitution Principle VII).

| Dataset Name | OpenML ID | Approx. Samples | Features | Binary? | Verification Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Pima Indians Diabetes | [Dataset Size] | 768 | 8 | Yes | Verified binary target. |
| Breast Cancer (Wisconsin) | A substantial number of instances | 683 | 30 | Yes | Verified binary target. |
| Ionosphere | [Significant dataset] | 351 | 34 | Yes | Verified binary target. |
| Sonar | | 208 | 60 | Yes | Verified binary target. |
| Liver Disorders (Bupa) | a moderate sample size | 345 | 6 | Yes | Verified binary target. |
| Heart Disease (Cleveland) | a substantial dataset | 303 | 13 | Yes | Verified binary target. |
| German Credit | approximately 30 | 1000 | 20 | Yes | Verified binary target. |
| Adult Income | [Dataset Size] | 48842 | 14 | Yes | Verified binary target. |
| Spambase | [a subset of instances] | 4601 | 57 | Yes | Verified binary target. |
| WDBC (Diagnosis) | large-scale dataset | 569 | 30 | Yes | Verified binary target. |
| Vehicle (Bus vs Others) | A significant number | 846 | 18 | Yes | **Binarized**: Class 'Bus' vs. {Car, Van, Saab}. Canonical subset defined. |
| SPECT Heart | A substantial dataset | 260 | 22 | Yes | Verified binary target. |
| Haberman's Survival | A dataset containing a moderate number of observations and features | 306 | 3 | Yes | Verified binary target. |
| Credit Approval | A large dataset | 690 | 15 | Yes | Verified binary target. |
| Tic-Tac-Toe (Endgame) | a substantial dataset | 958 | 9 | Yes | Verified binary target. |

**Dataset Selection Protocol**:
1. **Primary Source**: We will load the 15 datasets listed above using `sklearn.datasets.fetch_openml(data_id=<ID>)`.
2. **Verification**: Each dataset will be checked to ensure:
   - Target is binary (2 classes). For ID 1518, the target is binarized to 'Bus' vs. 'Others' as a canonical subset.
 - Sample size is between 100 and [deferred].
   - No missing values that cannot be imputed (handled by pipeline).
3. **Diversity**: The selected list explicitly covers the range from ~200 samples (Sonar) to [deferred] (Adult), satisfying Constitution Principle VII.

## Statistical Methods

### 1. Repeated K-Fold Cross-Validation
- **Protocol**: 10 folds, 10 repeats = 100 evaluations per (dataset, model) pair.
- **Models**: Logistic Regression, Random Forest (n_estimators=100), Linear SVM.
- **Metrics**: Accuracy and F1-score recorded for every fold.
- **Preprocessing**: Median imputation for numeric, mode for categorical. **Critical**: Imputers must be fit on the training fold only to prevent data leakage.

### 2. Coefficient of Variation (CV) & Log-Log Transformation
- **Formula**: $CV = \frac{\sigma}{\mu}$
- **Application**: Calculated for Accuracy and F1 scores across the 100 evaluations for each model-dataset pair.
- **Transformation**: To address the non-linear relationship between CV and sample size (CV ∝ 1/√n) and the bounded nature of Accuracy, we will perform a **log-log linear regression**:
  $$ \log(CV) = \beta_0 + \beta_1 \log(n_{samples}) + \epsilon $$
- **Rationale**: This linearizes the expected inverse-square-root relationship. The hypothesis test is **H0: β1 = -0.5** (no deviation from theoretical scaling), not H0: β1 = 0. This avoids the tautology where raw CV vs. n is guaranteed to correlate.
- **Handling Zero Variance**: If $\sigma = 0$ (deterministic outcome), the CV will be set to a small epsilon or excluded from the log-transform to prevent `log(0)`.

### 3. Correlation Analysis (Log-Log)
- **Variables**: Regress $\log(CV_{accuracy})$ and $\log(CV_{f1})$ against $\log(n_{samples})$ and $\log(n_{features})$.
- **Hypothesis**: $H_0: \beta_1 = -0.5$ (No deviation from expected scaling).
- **Assumption**: Residuals of the log-log regression should be approximately normal.

### 4. Permutation Test for Variance Differences
- **Method**: Permutation test on the **variance of the performance metrics** directly.
- **Test Statistic**: Absolute difference of variances between two models (e.g., $|Var_{LR} - Var_{RF}|$).
- **Comparison**: Compare variance distributions of the three models for each dataset.
- **Null Hypothesis**: The variances of the performance metrics are drawn from the same distribution across models.
- **Implementation**: 10,000 permutations.
- **Note on Heteroscedasticity**: We acknowledge that variance depends on the mean (binomial variance). The test compares the *observed* variances of the metrics. If mean performance differs significantly between models, we will also report the standardized variance (variance / mean^2) as a robustness check.

### 5. Multiple-Comparison Correction
- **Method**: **Holm-Bonferroni** procedure.
- **Scope**: Applied to the set of all p-values generated from correlation tests and permutation tests across the 15 datasets.
- **Goal**: Control the **Family-Wise Error Rate (FWER)** as per FR-007 and SC-005.

### Robustness Checks
- **CV Instability**: For datasets where mean accuracy $\mu > 0.95$, the CV may explode artificially. In these cases, we will also compute the **Standard Error of the Mean (SEM = $\sigma / \sqrt{N}$)** and **Log-Odds Variance** as alternative stability metrics to ensure robustness.
- **Mean-Variance Dependency**: For models with significantly different mean accuracies, we will report the standardized variance to account for heteroscedasticity.

## Compute Feasibility

- **CPU-First**: All models (LR, RF, LinearSVM) are computationally lightweight and will run on the GitHub Actions CPU runner.
- **Memory**: Datasets will be loaded sequentially. If a dataset exceeds available RAM, it will be processed in chunks or sampled (with logging).
- **Time Budget**: 15 datasets × 3 models × 100 runs = 4,500 runs. Assuming an average of 1-2 seconds per run (small/medium datasets), total time is well within the 6-hour limit.
- **GPU**: Not required. No transformer or diffusion models are used.

## Decision/Rationale

| Method | CPU or GPU? | Rationale |
|--------|-------------|-----------|
| Repeated CV | CPU | Standard scikit-learn models are efficient on CPU. |
| Log-Log Regression | CPU | Trivial computation. |
| Permutation Test | CPU | 10k permutations of small vectors (100 elements) is fast on CPU. |
| Data Loading | CPU | Streaming/sequential loading fits within RAM limits. |

No GPU escape hatch is needed for this project.