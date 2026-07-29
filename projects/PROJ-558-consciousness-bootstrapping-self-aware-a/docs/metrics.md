# Measured Metrics: Definitions and Methodology

This document defines the metrics computed by the Consciousness Bootstrapping pipeline.
These metrics are used to evaluate the self-awareness, calibration, and error detection
capabilities of the recursive self-modeling architecture.

## 1. Self-Consistency

**Definition**: Self-consistency measures the model's ability to produce the same answer
across multiple independent reasoning paths generated under stochastic sampling.
It is a proxy for the stability of the model's internal reasoning process.

**Computation**:
For a given question $Q$, generate $N=10$ reasoning paths $\{P_1, P_2,..., P_N\}$
using temperature $T=0.7$ and top-p $p=0.9$. Extract the final answer $A_i$ from each path.
The self-consistency score is the proportion of paths that agree on the most frequent answer:

$$ SC(Q) = \frac{\max_{a} |\{i: A_i = a\}|}{N} $$

**Interpretation**:
- **High SC (near 1.0)**: The model converges on a single answer regardless of sampling noise,
 suggesting a robust internal logic.
- **Low SC**: The model's output is highly sensitive to sampling noise, indicating instability
 or lack of a definitive internal state.

**Implementation**: See `code/evaluation/metrics.py` -> `calculate_self_consistency`.

## 2. Brier Score

**Definition**: The Brier score measures the accuracy of probabilistic predictions.
In this context, it evaluates how well the model's predicted confidence matches the
actual correctness of its answers.

**Computation**:
Given a set of $M$ predictions where each prediction $i$ has a predicted confidence $c_i \in [0, 1]$
and a binary correctness label $y_i \in \{0, 1\}$ (1 if correct, 0 otherwise):

$$ BS = \frac{1}{M} \sum_{i=1}^{M} (c_i - y_i)^2 $$

**Interpretation**:
- **Lower is better**. A score of 0.0 indicates perfect calibration (confidence always equals correctness).
- A score of 0.25 corresponds to random guessing with 50% confidence on binary outcomes.

**Implementation**: See `code/evaluation/metrics.py` -> `calculate_brier_score`.

## 3. Expected Calibration Error (ECE)

**Definition**: ECE quantifies the gap between a model's average confidence and its average accuracy
across bins of predicted confidence. It measures the degree to which the model is over-confident
or under-confident.

**Computation**:
1. Bin the $M$ predictions into $B$ bins (default $B=10$) based on predicted confidence $c_i$.
2. For each bin $b$, compute the average confidence $\bar{c}_b$ and the accuracy $\bar{y}_b$ (fraction of correct answers).
3. Compute the weighted average of the absolute difference between accuracy and confidence:

$$ ECE = \sum_{b=1}^{B} \frac{|B_b|}{M} |\bar{y}_b - \bar{c}_b| $$

Where $|B_b|$ is the number of samples in bin $b$.

**Interpretation**:
- **Lower is better**. ECE = 0 implies perfect calibration.
- High ECE indicates a systematic mismatch between the model's self-assessment and reality.

**Implementation**: See `code/evaluation/metrics.py` -> `calculate_ece`.
*Note*: Raw binning data is computed internally but not persisted as a separate artifact to reduce storage overhead,
per FR-004. Only the final scalar ECE is reported.

## 4. ROC-AUC (Receiver Operating Characteristic - Area Under Curve)

**Definition**: ROC-AUC evaluates the model's ability to distinguish between correct and incorrect predictions
based on its confidence scores. It measures the trade-off between true positive rate and false positive rate
across all possible confidence thresholds.

**Computation**:
1. Treat the predicted confidence $c_i$ as the score for the positive class (correctness).
2. Compute the True Positive Rate (TPR) and False Positive Rate (FPR) at various thresholds.
3. Calculate the area under the ROC curve.

**Interpretation**:
- **Higher is better**.
- 0.5: No discrimination ability (random guessing).
- 1.0: Perfect discrimination (high confidence always correct, low confidence always incorrect).

**Implementation**: See `code/evaluation/metrics.py` -> `calculate_roc_auc`.

## 5. Percentage Difference in Self-Consistency (SC-Diff)

**Definition**: A comparative metric used in the statistical analysis phase to quantify the improvement
of the recursive model over the baseline model.

**Computation**:
Let $SC_{recursive}$ be the mean self-consistency score of the recursive model and
$SC_{baseline}$ be the mean self-consistency score of the baseline model.

$$ SC\text{-}Diff = \frac{SC_{recursive} - SC_{baseline}}{SC_{baseline}} \times 100\% $$

**Interpretation**:
- **Positive value**: The recursive model exhibits higher self-consistency than the baseline.
- **Negative value**: The baseline model is more consistent.
- This metric is reported in `artifacts/results/statistical_report.json`.

**Implementation**: See `code/analysis/stats.py` -> `calculate_percentage_difference`.

## 6. Sensitivity Analysis Metrics

**Definition**: Metrics that evaluate how the model's error detection rates change as a function of
the confidence threshold used to flag potential errors.

**Computed Columns**:
- **Threshold**: The confidence cutoff value.
- **False Positive Rate (FPR)**: Fraction of correct answers incorrectly flagged as errors (confidence < threshold).
- **False Negative Rate (FNR)**: Fraction of incorrect answers missed (confidence >= threshold).
- **FPR Delta / FNR Delta**: Change in rates relative to a baseline threshold (e.g., 0.5).

**Implementation**: See `code/analysis/stats.py` -> `run_sensitivity_analysis`.

---
*Generated by the Consciousness Bootstrapping Pipeline (PROJ-558).*
