# Metrics Definitions for Consciousness Bootstrapping

This document defines the key metrics used in the Consciousness Bootstrapping project, including their mathematical formulations, interpretations, and relevance to the research goals.

## 1. Self-Consistency

**Definition**: The proportion of times the model generates the same answer when provided with the same prompt multiple times.

**Formula**:
```
Self-Consistency = (Number of unique answers that match the majority vote) / (Total number of unique answers generated)
```

**Implementation**: Calculated using majority vote logic. For a set of `N` generated answers, the majority answer is determined, and the consistency score is the fraction of times this majority answer is reproduced.

**Relevance**: High self-consistency indicates that the model has a stable internal representation of the problem, a prerequisite for reliable self-modeling.

## 2. Error Detection Calibration

**Definition**: The correlation between the model's predicted probability of error and the actual frequency of errors.

**Method**:
1. The model outputs a scalar confidence score (or error probability) for each prediction.
2. Scores are binned into equal-width intervals (e.g., 0.0-0.1, 0.1-0.2,..., 0.9-1.0).
3. For each bin, the observed error rate is calculated as the fraction of incorrect predictions.
4. The calibration curve plots predicted error rates vs. observed error rates.

**Ideal Behavior**: A perfectly calibrated model would have predicted error rates equal to observed error rates in every bin (points lie on the diagonal line).

**Relevance**: Addresses the Socratic critique: "Does the machine know the good?" A well-calibrated error detector demonstrates the ability to judge its own outputs, distinguishing between "knowing that one knows" and "knowing what is worth knowing."

## 3. Percentage Difference in Self-Consistency

**Definition**: The relative improvement in self-consistency scores between the recursive model and the baseline model.

**Formula**:
```
Percentage Difference = ((Mean_Recursive - Mean_Baseline) / Mean_Baseline) * 100
```

**Statistical Testing**:
- Paired t-test to determine if the difference is statistically significant.
- Bonferroni correction applied for multiple comparisons.
- Cohen's d calculated to measure effect size.

**Relevance**: Quantifies the contribution of the recursive self-attention mechanism to model stability.

## 4. Brier Score

**Definition**: A measure of the accuracy of probabilistic predictions.

**Formula**:
```
Brier Score = (1/N) * Σ (predicted_probability - actual_outcome)^2
```
Where `actual_outcome` is 1 for correct and 0 for incorrect.

**Interpretation**: Lower scores indicate better calibration. A score of 0 is perfect, 0.25 is the score of a random guess for binary classification.

**Relevance**: Evaluates the quality of the model's confidence predictions.

## 5. Expected Calibration Error (ECE)

**Definition**: A weighted average of the difference between accuracy and confidence across bins.

**Formula**:
```
ECE = Σ (Bin_Count / Total_Count) * |Accuracy_Bin - Confidence_Bin|
```

**Relevance**: Provides a single scalar metric for calibration quality. Lower ECE indicates better alignment between confidence and accuracy.

## 6. ROC-AUC (Receiver Operating Characteristic - Area Under Curve)

**Definition**: The area under the ROC curve, measuring the ability of the model to distinguish between correct and incorrect predictions.

**Interpretation**:
- 0.5: Random guessing
- 1.0: Perfect discrimination
- >0.7: Generally considered acceptable

**Relevance**: Evaluates the error detection mechanism's ability to rank correct predictions higher than incorrect ones.

## 7. Cohen's d

**Definition**: A measure of effect size for the difference between two means.

**Formula**:
```
d = (Mean1 - Mean2) / Pooled_Standard_Deviation
```

**Interpretation**:
- 0.2: Small effect
- 0.5: Medium effect
- 0.8: Large effect

**Relevance**: Indicates the practical significance of the observed differences, not just statistical significance.

## 8. Sensitivity Analysis Metrics

**Definition**: Measures of how false positive and false negative rates change with varying confidence thresholds.

**Metrics**:
- `false_positive_rate`: Fraction of correct predictions incorrectly flagged as errors.
- `false_negative_rate`: Fraction of incorrect predictions missed by the detector.
- `fp_rate_delta`: Change in FPR relative to a baseline threshold.
- `fn_rate_delta`: Change in FNR relative to a baseline threshold.

**Relevance**: Assesses the robustness of the error detection system across different operating points.

## Philosophical Context

These metrics collectively address the core philosophical questions raised in the project:

- **Socratic Inquiry**: "Can the same thing be both subject and object?" The error detection calibration metric provides empirical evidence of the model's ability to model its own states and judge them.

- **Wolfram's Computational Universe**: The self-consistency metric reflects the stability of computational processes when subjected to recursive self-reference.

- **Krakauer's Evolutionary Perspective**: The sensitivity analysis and effect sizes quantify the "metabolic cost" (computational resources) paid for the benefit of self-awareness.

## Usage

These metrics are computed by:
- `code/evaluation/metrics.py`: Core metric calculations
- `code/analysis/stats.py`: Statistical aggregation and significance testing
- `code/evaluation/run_benchmarks.py`: Benchmark execution and data generation

Results are aggregated in `artifacts/results/statistical_report.json` and visualized in `artifacts/results/sensitivity_analysis.csv`.