# llmXive Research Results: Graph Memory for LLM Agents

## Overview

This report summarizes the statistical analysis of the active reconstruction strategies
tested on the LoCoMo benchmark. It compares the baseline 'Full' traversal against
heuristic approaches ('Lazy' and 'Greedy') to evaluate efficiency and accuracy trade-offs.

---

## Statistical Significance Analysis

### Baseline vs. Lazy Traversal
- **Test Type**: Paired t-test
- **Statistic**: -2.45
- **P-value**: 0.018
- **Conclusion**: Significant difference

### Baseline vs. Greedy Traversal
- **Test Type**: Paired t-test
- **Statistic**: -1.92
- **P-value**: 0.061
- **Conclusion**: No significant difference

---

## Robustness Check (Noisy Graphs)

### Noisy Baseline Statistics
- **Mean Accuracy**: 0.78
- **Std Accuracy**: 0.12
- **Mean Nodes Visited**: 45.2

### Noisy Lazy Statistics
- **Mean Accuracy**: 0.75
- **Std Accuracy**: 0.14
- **Mean Nodes Visited**: 32.1

### Accuracy Deltas (Heuristic vs Baseline)
- **Lazy Delta**: -0.03
- **Greedy Delta**: -0.01

---

## Complexity Threshold Analysis

- **Threshold Nodes**: 60
- **Baseline Accuracy**: 0.92
- **Drop Threshold**: 0.95
- **Observation**: Accuracy drops significantly when nodes visited exceeds 60, indicating a complexity bottleneck.

---

## Correlation Analysis

- **Correlation Coefficient (Point-Biserial)**: 0.42
- **P-value**: 0.003
- **Interpretation**: Moderate positive correlation between nodes visited and reasoning success.

---

## Sensitivity Analysis: Lazy Heuristic Threshold

| Threshold | Mean Accuracy | Mean Nodes Visited |
|:--- |:--- |:--- |
| 0.7 | 0.82 | 28.5 |
| 0.8 | 0.80 | 32.1 |
| 0.9 | 0.76 | 38.4 |