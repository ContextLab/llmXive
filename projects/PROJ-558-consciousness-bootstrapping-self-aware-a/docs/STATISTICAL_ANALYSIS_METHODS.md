# Statistical Analysis Methods

This document describes the statistical methods used in the Consciousness
Bootstrapping project for evaluating model performance and significance.

## Paired T-Test

### Purpose

To determine whether the difference in performance metrics (e.g., self-consistency
scores) between the recursive and baseline models is statistically significant.

### Implementation

The `run_paired_ttest` function in `code/analysis/stats.py` uses `scipy.stats.ttest_rel`
to perform a paired t-test on the performance scores from each seed.

```python
from scipy import stats

def run_paired_ttest(recursive_scores, baseline_scores):
 """
 Perform paired t-test between recursive and baseline model scores.

 Args:
 recursive_scores: List of scores from recursive model across seeds.
 baseline_scores: List of scores from baseline model across seeds.

 Returns:
 t_statistic: The t-value of the test.
 p_value: The two-tailed p-value.
 """
 t_stat, p_val = stats.ttest_rel(recursive_scores, baseline_scores)
 return t_stat, p_val
```

### Assumptions

1. **Paired Observations**: Scores are paired by seed (same seed used for both models).
2. **Normality**: The differences between pairs are approximately normally distributed.
 (With small sample sizes, this assumption is difficult to verify, but the t-test
 is robust to moderate deviations.)
3. **Independence**: Seeds are independent of each other.

## Bonferroni Correction

### Purpose

To control the family-wise error rate when performing multiple hypothesis tests.
In this project, we test multiple metrics (self-consistency, Brier score, ECE),
so we apply Bonferroni correction to avoid false positives.

### Implementation

The `bonferroni_correction` function adjusts p-values by multiplying by the number
of tests performed.

```python
def bonferroni_correction(p_value, n_tests):
 """
 Apply Bonferroni correction to a p-value.

 Args:
 p_value: The raw p-value.
 n_tests: The number of hypothesis tests performed.

 Returns:
 corrected_p_value: The Bonferroni-corrected p-value.
 """
 corrected_p = p_value * n_tests
 return min(corrected_p, 1.0) # Cap at 1.0
```

### Usage

If we test 3 metrics (self-consistency, Brier score, ECE), the correction factor
is 3. A raw p-value of 0.02 becomes 0.06 after correction.

## Cohen's D (Effect Size)

### Purpose

To quantify the magnitude of the difference between recursive and baseline models,
independent of sample size.

### Implementation

Cohen's d is calculated as the mean difference divided by the pooled standard deviation.

```python
def calculate_cohen_d(group1, group2):
 """
 Calculate Cohen's d effect size.

 Args:
 group1: Scores from group 1 (recursive).
 group2: Scores from group 2 (baseline).

 Returns:
 cohens_d: The effect size.
 """
 mean_diff = np.mean(group1) - np.mean(group2)
 std_pooled = np.sqrt((np.std(group1, ddof=1)**2 + np.std(group2, ddof=1)**2) / 2)
 return mean_diff / std_pooled
```

### Interpretation

- **Small**: |d| ≈ 0.2
- **Medium**: |d| ≈ 0.5
- **Large**: |d| ≈ 0.8

## Confidence Intervals

### Purpose

To estimate the range within which the true mean difference between models lies,
with a specified level of confidence (typically 95%).

### Implementation

```python
def calculate_confidence_interval(mean_diff, std_diff, n, confidence=0.95):
 """
 Calculate confidence interval for the mean difference.

 Args:
 mean_diff: Mean of the differences.
 std_diff: Standard deviation of the differences.
 n: Number of pairs (seeds).
 confidence: Confidence level (default 0.95).

 Returns:
 lower_bound: Lower bound of the CI.
 upper_bound: Upper bound of the CI.
 """
 from scipy import stats
 t_crit = stats.t.ppf((1 + confidence) / 2, df=n-1)
 margin_error = t_crit * (std_diff / np.sqrt(n))
 return mean_diff - margin_error, mean_diff + margin_error
```

## Percentage Difference

### Purpose

To express the relative improvement of the recursive model over the baseline
as a percentage, as required by spec.md SC-001.

### Implementation

```python
def calculate_percentage_difference(recursive_mean, baseline_mean):
 """
 Calculate percentage difference between recursive and baseline means.

 Formula: ((recursive - baseline) / baseline) * 100

 Args:
 recursive_mean: Mean score of recursive model.
 baseline_mean: Mean score of baseline model.

 Returns:
 percentage_diff: Percentage difference.
 """
 if baseline_mean == 0:
 raise ValueError("Baseline mean cannot be zero.")
 return ((recursive_mean - baseline_mean) / baseline_mean) * 100
```

## Sensitivity Analysis

### Purpose

To evaluate how the model's error detection performance varies with different
confidence thresholds. This helps identify the optimal threshold for practical use.

### Thresholds Tested

The project tests the discrete set: **{0.4, 0.5, 0.6}**.

### Metrics Calculated

For each threshold:
- **False Positive Rate (FPR)**: Proportion of correct predictions incorrectly
 flagged as errors.
- **False Negative Rate (FNR)**: Proportion of errors incorrectly classified as correct.
- **Precision**: Proportion of flagged errors that are actual errors.
- **Recall**: Proportion of actual errors that are correctly flagged.
- **F1 Score**: Harmonic mean of precision and recall.

### Output Format

Results are saved to `artifacts/results/sensitivity_analysis.csv` with columns:
`threshold, false_positive_rate, false_negative_rate, precision, recall, f1_score`

## Filtering Converged Seeds

### Purpose

To ensure statistical comparisons are only made on seeds where the confidence
loss has converged, avoiding noise from non-converged training runs.

### Criteria

A seed is considered converged if:
1. The confidence loss stabilizes (variance < threshold in final epochs).
2. No OOM or training errors occurred.

Seeds failing these criteria are excluded from statistical analysis and listed
in the report's `seeds_excluded` field.

## References

- `code/analysis/stats.py`: Source implementation.
- `scipy.stats`: Statistical functions used.
- `spec.md`: Functional Requirements FR-005, FR-006, FR-007.