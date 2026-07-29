# Metrics Reference: Consciousness Bootstrapping Project

This document defines the core metrics used to evaluate self-referential reasoning
and meta-cognitive calibration in the `PROJ-558-consciousness-bootstrapping` pipeline.
These metrics are computed by `code/evaluation/metrics.py` and analyzed by
`code/analysis/stats.py`.

## 1. Self-Consistency (SC)

**Definition**: The proportion of times a model generates the same final answer
across multiple independent reasoning paths for a single query.

**Methodology**:
1. For a given question $Q$, generate $N$ reasoning paths (default $N=10$) using
 stochastic decoding (temperature $T=0.7$, top-$p=0.9$).
2. Extract the final answer from each path.
3. Perform a majority vote.
4. The Self-Consistency score is $1.0$ if a strict majority exists and matches the
 ground truth (for evaluation), or simply the frequency of the majority answer
 (for raw consistency measurement).

**Tie-Breaking Rule**: If no strict majority exists (e.g., a 2-2-1 split in a 5-path
generation, or a 3-2 split where the majority is incorrect relative to ground truth),
the proxy signal defaults to `0` (incorrect). This prevents false confidence in
ambiguous reasoning.

**Significance**: High self-consistency suggests the model has converged on a stable
internal representation of the solution, a prerequisite for reliable introspection.

## 2. Error Detection Calibration (EDC)

**Definition**: A measure of how well the model's predicted confidence scores
correlate with actual correctness.

**Sub-metrics**:

### 2.1 Brier Score
The mean squared difference between predicted probabilities and actual binary outcomes.
$$ Brier = \frac{1}{N} \sum_{i=1}^{N} (f_i - o_i)^2 $$
Where $f_i$ is the predicted confidence and $o_i$ is 1 if correct, 0 otherwise.
Lower scores indicate better calibration.

### 2.2 Expected Calibration Error (ECE)
ECE measures the gap between accuracy and confidence across bins.
1. Bin predictions into $M$ intervals (default $M=10$) based on confidence.
2. For each bin $b$, calculate average confidence ($avg\_conf_b$) and accuracy ($acc_b$).
3. Compute weighted average of the absolute difference:
 $$ ECE = \sum_{b=1}^{M} \frac{|B_b|}{N} |acc_b - avg\_conf_b| $$
Lower ECE indicates the model's confidence aligns with its actual performance.

### 2.3 ROC-AUC
The Area Under the Receiver Operating Characteristic Curve, treating confidence
scores as prediction scores for correctness. Measures the ability to distinguish
between correct and incorrect generations.

## 3. Statistical Significance Metrics

**Definition**: Metrics derived in `code/analysis/stats.py` to determine if
improvements in the recursive model over the baseline are statistically significant.

### 3.1 Percentage Difference in Self-Consistency (SC-001)
Calculated as:
$$ \%Diff = \frac{SC_{recursive} - SC_{baseline}}{SC_{baseline}} \times 100 $$
This metric is explicitly reported in `artifacts/results/statistical_report.json`.

### 3.2 Paired T-Test
Used to compare the performance of the recursive vs. baseline models across
multiple seeds. The null hypothesis is that the mean difference in performance
is zero.

### 3.3 Cohen's d (Effect Size)
Measures the standardized difference between two means:
$$ d = \frac{\bar{x}_1 - \bar{x}_2}{s_{pooled}} $$
Indicates the magnitude of the improvement, independent of sample size.

### 3.4 Bonferroni Correction
Applied to p-values when performing multiple comparisons to control the family-wise
error rate. Adjusted p-value = $p_{raw} \times k$, where $k$ is the number of tests.

## 4. Sensitivity Analysis

**Definition**: Evaluation of model performance across a discrete set of confidence
thresholds to determine the robustness of the error detection mechanism.

**Output Columns**:
- `threshold`: The confidence cutoff used.
- `false_positive_rate`: Rate of incorrect answers labeled as "confident/correct".
- `false_negative_rate`: Rate of correct answers labeled as "unconfident/incorrect".
- `fp_rate_delta`, `fn_rate_delta`: Variation relative to the baseline model.

**Implementation**: Performed by `run_sensitivity_analysis` in `code/analysis/stats.py`
without relying on raw binning artifacts.
