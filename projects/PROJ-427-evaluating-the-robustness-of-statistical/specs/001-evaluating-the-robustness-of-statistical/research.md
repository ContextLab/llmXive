# Research: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Problem Statement

Standard statistical inference (t-tests, ANOVA, regression) assumes data quality. Real-world data often contains errors: random value corruption, category misclassification, and missing values. This research quantifies the robustness of these methods by systematically injecting errors at controlled rates and measuring the degradation of inference metrics (Type I error, CI coverage, effect size bias).

## Dataset Strategy

The project utilizes **verified datasets** from the UCI Machine Learning Repository (hosted on HuggingFace) to ensure reproducibility and format stability. As per the spec, we select 5-10 diverse datasets, ensuring at least 2 numerical and 2 categorical variables for valid testing of all statistical methods.

| Dataset Name | Source URL (Verified) | Variable Types | Suitability for Tests |
|:--- |:--- |:--- |:--- |
| **UCI HAR** | ` | Numerical (Sensors) + Categorical (Activity) | T-test, ANOVA (Activity groups), Regression |
| **UCI Bank Marketing** | `https://huggingface.co/datasets/UCI/bank-marketing/resolve/main/bank-full.csv` | Mixed (Numerical/Categorical) | Chi-squared, Regression |
| **UCI Wine Quality** | `https://huggingface.co/datasets/UCI/wine-quality/resolve/main/winequality-red.csv` | Numerical | ANOVA (Quality groups), Regression |
| **UCI Adult** | `https://huggingface.co/datasets/UCI/adult/resolve/main/adult.csv` | Mixed (Categorical/Numerical) | Chi-squared, Regression |
| **Synthetic Null** | *Generated* | Numerical | Type I Error Validation (FR-007) |
| **Synthetic Effect** | *Generated* | Numerical | CI Coverage & Bias Validation (FR-006) |

**Note on Datasets**:
- **UCI HAR**: Contains 'Activity' labels for grouping; suitable for ANOVA/T-test.
- **UCI Bank Marketing**: Contains 'y' (purchase) and 'job' (categorical) for Chi-squared.
- **UCI Wine Quality**: Contains 'quality' (1-10) for ANOVA.
- **UCI Adult**: Contains 'income' (categorical) and 'age' (numerical) for Chi-squared/Regression.
- **Synthetic Data**: Generated programmatically with known population parameters ($\mu_{true}$, $\delta_{true}$) to serve as the "Ground Truth" for measuring bias and CI coverage. This is necessary because real-world datasets do not have a known "true" population parameter to compare against for bias calculation.

**Dataset Selection Rationale**:
- **UCI HAR**: High-dimensional numerical data, suitable for testing t-tests and ANOVA on sensor features with natural groupings.
- **UCI Bank Marketing**: Contains categorical purchase behavior, ideal for chi-squared tests.
- **Synthetic Data**: Used exclusively for validating the *internal logic* of the pipeline (ensuring it correctly measures known truths). Real-data robustness is measured empirically.

## Methodology

### 1. Data Preparation & Ground Truth Generation (FR-001, FR-006, FR-007)
- **Real Data**: Download and clean verified datasets.
 - **Cleaning**: For datasets with existing missing values (e.g., 'MCAR' named datasets), impute missing values (mean/mode) or drop rows *before* the experiment to establish a true 'clean' baseline.
 - **Grouping**: T-tests and ANOVA are **only** executed on datasets with **existing natural categorical labels** (e.g., 'Activity' in HAR, 'Quality' in Wine). Datasets without natural groups are skipped for T-test/ANOVA to avoid artificial ground truth (no k-means clustering).
 - **Cardinality Check**: Chi-squared tests are skipped if categorical variables have < 2 unique values.
- **Synthetic Data**: Generate datasets where the population parameters are *known*.
 - *Null Hypothesis Data*: Generate two groups with identical means ($\mu_1 = \mu_2$) to measure Type I error.
 - *Effect Size Data*: Generate groups with a known difference $\delta$ to measure effect size bias and CI coverage.
 - *Note*: Synthetic data is used **only** to validate the pipeline's ability to measure known truths. It is not used to claim generalizability to real-world distributions.

### 2. Error Injection (FR-002)
Three error types are injected at rates: **[deferred], [deferred], [deferred], [deferred]**.
- **Random Value Replacement**: For numerical columns, replace a value with a draw from the **empirical distribution** of the original column (bootstrapping). This preserves the distribution's shape (skew/kurtosis) while introducing noise, isolating the 'error' effect from 'distributional shift'.
- **Category Misclassification**: For categorical columns, randomly swap the label with another valid category in the dataset.
- **MCAR Missingness**: Randomly set values to `NaN` with probability $p$ (the error rate).

### 3. Statistical Analysis (FR-003, FR-004)
For each dataset (clean and corrupted) and each simulation iteration:
- **T-Test**: Compare two groups (only if natural groups exist). Record p-value, 95% CI, Cohen's d.
- **ANOVA**: Compare >2 groups (only if natural groups exist). Record F-statistic, p-value.
- **Chi-Squared**: Test independence of categorical variables (only if cardinality >= 2). Record $\chi^2$, p-value.
- **Linear Regression**: Predict continuous outcome. Record coefficients, 95% CI, $R^2$.

**Metrics Calculation**:
- **Empirical Type I Error Rate**: Proportion of tests where $p < 0.05$ given the null hypothesis is *true* (from **Synthetic Null** data or **Real Data** via label permutation).
- **CI Coverage**: Proportion of 95% CIs that contain the *true* parameter (from **Synthetic Effect** data only). *Note: CI Coverage is NOT calculated for Real Data as the true parameter is unknown.*
- **Effect Size Bias**: $|\hat{\delta} - \delta_{true}|$ (from **Synthetic Effect** data only). *Note: Bias is NOT calculated for Real Data.*
- **Statistical Power**: For **MCAR** + Listwise Deletion, the primary metric is **Power Loss** (reduced effective N), not Type I Error Inflation (which is theoretically zero for MCAR).

### 4. Aggregation & Visualization (FR-005)
- Aggregate results across simulation iterations (e.g., 1000 runs per configuration).
- Generate degradation curves: X-axis = Error Rate, Y-axis = Metric (Type I Error, Coverage, Power).
- Generate summary tables comparing test robustness.

## Statistical Rigor & Assumptions

### Multiple Comparisons
While the simulation runs many tests, the primary focus is on the *rate* of Type I error under the null. We do not apply Bonferroni correction to the *simulation results* themselves, as we are estimating the error rate of the test, not making a single inference from one dataset. However, when reporting the final "robustness" of a method, we will clearly distinguish between the *nominal* $\alpha$ (0.05) and the *empirical* Type I error rate.

### Sample Size & Power
- **Synthetic Data**: Sample sizes ($N$) will be chosen to ensure adequate power in the clean state (e.g., $N=100$ per group) to detect the intended effect size.
- **Missing Data**: MCAR missingness reduces effective $N$. We will explicitly report the power loss (reduced sample size) as a confounding factor, distinguishing it from Type I error inflation.

### Causal Inference
This study is **observational** regarding the relationship between data errors and statistical distortion. We are not claiming a causal mechanism for the error injection (which is artificial) but rather measuring the *associational* degradation of statistical properties. No randomization of "error" is needed as the error is algorithmically imposed.

### Measurement Validity
- **Instruments**: Standard statistical tests (`scipy.stats`, `statsmodels`) are used. These are well-validated.
- **Collinearity**: In regression tests, we will ensure predictors are not definitionally related to the outcome to avoid trivial bias. If collinearity exists, it will be noted, and independent effects will not be claimed.

### Computational Feasibility
- **Hardware**: 2 CPU cores, 7GB RAM.
- **Strategy**:
 - Use `numpy` vectorization for error injection.
 - Process datasets in chunks if memory is tight (unlikely for 5-10 UCI datasets).
 - Limit simulation iterations to a sufficient number per configuration to ensure stable error rate estimates.
 - No GPU required.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Synthetic Data for Ground Truth** | Real datasets lack known population parameters ($\mu_{true}$, $\delta_{true}$). Synthetic data is required to calculate "Bias" and "CI Coverage" accurately (SC-002, SC-003). Synthetic data is used *only* for internal validation, not to claim generalizability. |
| **No K-Means for Grouping** | K-means clustering creates artificial groups that guarantee statistical significance, invalidating the robustness test. T-tests/ANOVA are only run on datasets with natural labels. |
| **Bootstrapped Replacement** | Replacing values from the empirical distribution preserves the original distribution's shape, isolating the 'error' effect from 'distributional shift'. |
| **MCAR Metric: Power Loss** | MCAR + Listwise Deletion does not inflate Type I Error. The correct metric for MCAR degradation is Statistical Power (reduced N). |
| **Error Rates: [deferred], [deferred], [deferred], [deferred]** | Covers low to high error scenarios, allowing detection of non-linear degradation thresholds. |
| **Real Data: Type I Error via Permutation** | For real data, Type I Error is measured by permuting labels (breaking the true relationship) and testing for false rejections. |
