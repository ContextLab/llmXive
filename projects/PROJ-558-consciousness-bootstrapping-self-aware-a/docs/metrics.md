# Metrics and Statistical Analysis Documentation

This document provides detailed definitions and implementation notes for the metrics used in the Consciousness Bootstrapping project.

## 1. Self-Consistency Proxy

The core innovation of this project is the use of an **internal self-consistency proxy** to train the model to be aware of its own correctness.

### Implementation Details
* **Location**: `code/evaluation/loss_functions.py` (function `compute_self_consistency_proxy`)
* **Mechanism**:
 1. For a given training item, the model generates N=5 reasoning paths.
 2. The final answer is extracted from each path.
 3. A majority vote determines the "proxy correctness" signal.
 4. **Tie-Breaking**: If no strict majority exists, the proxy defaults to 0 (incorrect).

### Loss Function
The joint loss function combines standard cross-entropy with a confidence-prediction loss:
$$L_{joint} = L_{CE} + \lambda \cdot L_{confidence}$$

Where $L_{confidence}$ is the binary cross-entropy between the model's predicted confidence and the proxy correctness signal.

## 2. Calibration Metrics

Calibration measures the alignment between a model's confidence and its accuracy.

### Expected Calibration Error (ECE)
* **Location**: `code/evaluation/metrics.py` (function `calculate_ece`)
* **Bins**: Equal-width bins spanning [0.0, 1.0].
* **Edge Case**: If a bin has zero samples, observed accuracy is 0.0.

### Brier Score
* **Location**: `code/evaluation/metrics.py` (function `calculate_brier_score`)
* **Interpretation**: Lower is better. 0.0 is perfect.

### Calibration Curve
* **Location**: `code/evaluation/metrics.py` (function `calculate_calibration_curve`)
* **Output**: JSON object with `bin_edges`, `bin_counts`, `observed_accuracies`.
* **Usage**: Used for visualization and sensitivity analysis.

## 3. Statistical Tests

The project uses paired t-tests to determine if the recursive model's performance is statistically significantly better than the baseline.

### Paired t-test
* **Location**: `code/analysis/stats.py` (function `run_paired_ttest`)
* **Input**: Lists of metrics (e.g., self-consistency scores) for each seed.
* **Correction**: Bonferroni correction is applied for multiple comparisons.

### Cohen's d
* **Location**: `code/analysis/stats.py` (function `calculate_cohen_d`)
* **Purpose**: Measures the effect size (magnitude of difference).

### Percentage Difference
* **Location**: `code/analysis/stats.py` (function `calculate_percentage_difference`)
* **Formula**: $\frac{Mean_{recursive} - Mean_{baseline}}{Mean_{baseline}} \times 100$

## 4. Sensitivity Analysis

This analysis tests the robustness of the model's error detection capabilities across different confidence thresholds.

* **Location**: `code/analysis/stats.py` (function `run_sensitivity_analysis`)
* **Thresholds**: {0.4, 0.5, 0.6}
* **Metrics**: False Positive Rate (FPR), False Negative Rate (FNR), and their deltas between recursive and baseline models.
* **Output**: `artifacts/results/sensitivity_analysis.csv`

## 5. Data Hygiene

Per Constitution Principle III, all data sources are checksummed and recorded in `data/manifest.json`.

* **Training Data**: Pile (arXiv subset), truncated to 100k tokens.
* **Evaluation Data**: GSM8K, MMLU.
* **Verification**: Checksums are computed using SHA-256.