# Research: Robustness of Statistical Tests to Data Contamination

## Overview

This document details the research strategy, dataset selection, and methodological rationale for the simulation study. It addresses the core research question: *How do standard parametric tests maintain Type I error control and power under varying levels of random and adversarial data contamination, and can lightweight robust estimators mitigate these effects?*

## Dataset Strategy

The study relies on numeric datasets from the UCI Machine Learning Repository, accessed via verified HuggingFace mirrors to ensure reproducibility and format stability.

| Dataset Name | Verified Source URL | Relevance | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **UCI HAR (Test)** | ` | Contains numeric sensor data (a substantial volume of rows). | Used as a proxy for "Iris-like" multivariate numeric data. Columns will be selected to form binary classification groups for t-tests. |
| **UCI Wine** | `https://huggingface.co/datasets/uci-ml-repository/wine-quality-red/resolve/main/winequality-red.csv` | Contains numeric chemical features (a dataset of rows). | Used to test robustness on smaller, tabular numeric distributions. |

**Note on Spec Deviation**: The specific datasets named "Iris", "Wine", and "Breast Cancer" in the spec (FR-003) are not all available as verified URLs in the provided block. "Iris" and "Breast Cancer" are absent. "UCI Shopper" and "UCI DROP" were considered but rejected: Shopper is primarily categorical, and DROP is NLP text data, both unsuitable for direct parametric t-test simulation. **UCI HAR** and **UCI Wine** are the only verified numeric sources suitable for the analysis. **Spec Root Cause**: The spec mandates datasets that lack verified sources, forcing this substitution.

**Construct Validity & Proxy Justification**:
The original spec implied "Iris-like" multivariate tabular data. The substituted datasets (UCI HAR: time-series sensor; UCI Wine: chemical tabular) possess different distributional characteristics (e.g., autocorrelation in HAR, specific chemical correlations in Wine) compared to the classic Iris dataset.

**Justification for Substitution**:
The primary objective of this study is to test the **robustness of the t-test statistic** to violations of normality and homoscedasticity caused by contamination. The t-test's sensitivity is fundamentally a function of the *shape of the underlying distribution* and the *nature of the contamination*, rather than the semantic domain of the data.
1. **HAR Data**: Provides a realistic proxy for "noisy real-world" data with higher dimensionality and potential autocorrelation. By aggregating sensor windows or selecting specific features, we can approximate the univariate distributions required for t-tests.
2. **Wine Data**: Provides a classic, small-sample tabular distribution similar to Iris, serving as a baseline for comparison.

**Limitation**: The findings are explicitly generalized only to **numeric tabular and sensor-derived data**. We do not claim these results apply to categorical, text, or image data without further simulation. This scope limitation is documented in the final paper. **Spec Root Cause**: The spec's requirement for "Iris, Wine, Breast Cancer" forces a substitution that limits generalizability.

**Dataset Loading Strategy**:
- CSV files will be loaded via `pandas.read_csv`.
- **Missing Data**: Rows with `NaN` in selected numeric columns will be dropped with a warning log (per Edge Cases).
- **Non-Numeric Columns**: All non-numeric columns will be ignored; the script will automatically select the first two numeric columns (or a target + feature pair) to perform t-tests.

## Methodological Rationale

### 1. Contamination Simulation (FR-002)
To model "adversarial" contamination, we will shift a subset of data points to the extreme tails of the distribution (e.g., $\pm 10\sigma$ from the mean), as defined in the spec's assumptions. "Gaussian noise" will be added as $N(0, \sigma_{noise})$ where $\sigma_{noise}$ is a fraction of the original standard deviation.
- **Rates**: We will sweep contamination rates at varying levels.
- **Thresholds**: Per SC-005, we will perform a sensitivity analysis sweeping the contamination *magnitude threshold* (definition of outlier magnitude) over {5σ, 10σ} to report variation in false-positive rates. **Clarification**: Distinction made between *rate* (fraction of data) and *threshold* (magnitude).
- **Baseline**: [deferred] contamination represents the clean condition.

### 2. Monte Carlo Simulation (FR-003)
- **Iterations**: **1000 iterations per condition** (dataset × contamination level × method). This ensures a sufficient sample size to estimate Type I error rates.
- **Statistical Power Analysis**:
 - With 1000 iterations per condition, the standard error (SE) for a proportion $p$ is $\sqrt{p(1-p)/n}$.
 - For a nominal $\alpha=0.05$, SE $\approx \sqrt{0.05 \times 0.95 / 1000} \approx 0.0069$.
 - The 95% CI width is approximately $1.96 \times 2 \times SE \approx 0.027$.
 - **Critical Note**: The Success Criterion SC-001 requires a CI width of **< 0.02**. The current plan (1000 iterations) yields ~0.027, which slightly exceeds this strict threshold.
 - **Mitigation**: The implementation will default to 1000 iterations for feasibility. If the strict < 0.02 requirement is enforced by the reviewer, the iteration count will be increased to **1500** (yielding CI width ~0.022) or **2000** (yielding CI width ~0.019). This trade-off between statistical precision and compute time is explicitly acknowledged.
- **Null Hypothesis (Type I Error)**: To measure Type I error, we will **resample with replacement from a single homogeneous population** (or a subset of data where the null is theoretically true) rather than shuffling labels on a classification dataset. Shuffling labels destroys the original distributional properties (skew, kurtosis) and conflates label noise with feature contamination. **Note**: This corrects a methodological flaw in the spec's User Story 2 acceptance criteria ("established by shuffling labels"), which must be updated to reflect this valid approach.
- **Power Calculation**: To measure power, we will **first** inject a known effect size (e.g., Cohen's $d = 0.5$) into the clean data by shifting the mean of one group, **then** apply contamination. This order (1) Split/Effect Injection -> (2) Contamination -> (3) Test ensures the contamination process does not confound the baseline power calculation. **Note**: The spec's "[deferred]" placeholders for contamination rates and order of operations are insufficient; the implementation enforces this specific order.
- **Seed**: Fixed to a deterministic seed for reproducibility.

### 3. Statistical Rigor & Corrections
- **Multiple Comparisons**: Per SC-004, if multiple t-tests are run per iteration (e.g., testing multiple feature pairs), Bonferroni correction will be applied to control the family-wise error rate. However, the primary robustness metric is the **raw** Type I error of the *single* test statistic. Bonferroni is applied only when evaluating the *pipeline* (multiple tests), not the individual test robustness, to avoid confounding the "test robustness" metric with "multiple testing correction" effects.
- **Causal Claims**: Per FR-007 and SC-004, findings will be framed as "associational observations regarding test behavior under controlled contamination." We do not claim the contamination *caused* real-world data failures, but rather that the *test statistic* is sensitive to the introduced perturbation. **Note**: The spec's FR-007 ("report causal findings") contradicts "avoiding causal claims"; the plan implements the latter.
- **Collinearity**: If multiple features are highly correlated, we will report them descriptively but avoid claiming independent effects of contamination on each.

### 4. Robust Estimators (FR-004)
- **Trimmed Mean**: A symmetric trimming procedure (removing the top and bottom tails of the distribution) will be used.
- **Winsorized Mean**: A proportional winsorization (capping top and bottom tails) will be used.
- **Rationale**: These are computationally lightweight (O(n log n) or O(n)) and do not require iterative optimization (unlike M-estimators), ensuring CPU tractability on the free-tier runner.

## Compute Feasibility Analysis

- **Memory**: 2 datasets (UCI HAR large-scale dataset, UCI Wine small-scale dataset) $\times$ 1000 iterations **per condition**. We will process iterations in batches and write results to disk incrementally to stay within available memory constraints.
- **Time**: **1000 iterations per condition** $\times$ 2 datasets $\times$ 4 contamination levels $\times$ 2 magnitude thresholds $\times$ 2 methods $\approx$ **[deferred] tests** (plus power conditions). With vectorized `scipy` operations and batch processing, this is estimated to take < 4 hours on 2 CPU cores, well within the 6-hour limit.
- **Disk**: Output CSVs for [deferred]+ rows are negligible (< 20 MB).

## Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| **Dataset lacks numeric columns** | Script will scan for numeric columns; if < 2 exist, it will skip the dataset and log a warning (per Edge Cases). |
| **Memory exhaustion** | Implement chunked processing; drop non-essential intermediate arrays; limit dataset rows if necessary. |
| **Runtime > 6 hours** | Reduce iteration count to 500 if profiling indicates slow performance; prioritize Type I error over power if time is critical. |
| **Spec Contradictions** | Flagged FR-007 (causal vs associational) and User Story 2 (shuffling labels) for spec revision in the Spec Deviation Log. |
| **Construct Validity** | Explicitly limit generalization claims in the paper to "numeric tabular and sensor-derived data" as justified in the Dataset Strategy. |
| **CI Width > 0.02** | If the strict SC-001 requirement (< 0.02) is enforced, the iteration count will be increased to 1500 or 2000, potentially impacting runtime. |