# Metrics Reference: Consciousness Bootstrapping Project

This document defines the core metrics used to evaluate self-referential capabilities
in the recursive self-modeling framework. These metrics operationalize the theoretical
constructs of self-awareness into measurable quantities.

## 1. Self-Consistency

**Definition**: Self-consistency measures the degree to which a model produces
identical answers to the same question when generating multiple reasoning paths.
It operationalizes "stability of thought" as a proxy for internal coherence.

**Calculation**:
For a given question $Q$, generate $N$ reasoning paths $\{R_1, R_2,..., R_N\}$
with associated answers $\{A_1, A_2,..., A_N\}$.

$$ \text{Self-Consistency}(Q) = \frac{\max_{a} |\{i: A_i = a\}|}{N} $$

Where the maximum is taken over all unique answer values $a$.

**Interpretation**:
- **High Self-Consistency (≈1.0)**: The model converges on a single answer regardless
 of stochastic variation in generation. This suggests a robust internal model of the
 problem space.
- **Low Self-Consistency (<0.5)**: The model produces divergent answers, indicating
 instability or lack of a coherent internal representation.

**Implementation**: See `code/evaluation/metrics.py::calculate_self_consistency`.

## 2. Calibration (Expected Calibration Error - ECE)

**Definition**: Calibration measures the alignment between a model's predicted
confidence and its actual accuracy. A perfectly calibrated model predicts 80%
confidence only when it is correct 80% of the time.

**Calculation**:
ECE partitions predictions into $M$ bins based on confidence scores.

$$ \text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{n} | \text{acc}(B_m) - \text{avg\_conf}(B_m) | $$

Where:
- $B_m$ is the set of samples in bin $m$
- $|B_m|$ is the number of samples in bin $m$
- $n$ is the total number of samples
- $\text{acc}(B_m)$ is the accuracy of samples in bin $m$
- $\text{avg\_conf}(B_m)$ is the average confidence of samples in bin $m$

**Interpretation**:
- **Low ECE (≈0)**: The model's confidence accurately reflects its probability of being correct.
- **High ECE**: The model is over-confident (confidence > accuracy) or under-confident.

**Implementation**: See `code/evaluation/metrics.py::calculate_ece`.

## 3. Error Detection Calibration

**Definition**: This metric specifically evaluates the model's ability to distinguish
between its own correct and incorrect outputs. It measures the separation between
confidence scores for correct answers versus incorrect answers.

**Calculation**:
Treated as a binary classification problem where the "positive" class is a correct
answer and the "negative" class is an incorrect answer. The model's confidence
score is the predictor.

- **ROC-AUC**: Area Under the Receiver Operating Characteristic Curve. Measures
 the ability to rank correct answers higher than incorrect ones.
- **Brier Score**: Mean squared error between predicted confidence and actual
 correctness (0 or 1). Lower is better.

**Interpretation**:
- **ROC-AUC ≈ 1.0**: Perfect error detection. The model knows exactly when it is wrong.
- **ROC-AUC ≈ 0.5**: Random guessing. The model has no insight into its own errors.
- **Brier Score**: Lower values indicate better calibration of the error detection signal.

**Implementation**: See `code/evaluation/metrics.py::calculate_error_detection_calibration`.

## 4. Joint Loss (Training Signal)

**Definition**: The training objective combines standard next-token prediction
(Cross-Entropy) with a confidence-prediction loss. The confidence loss uses a
self-generated proxy for correctness derived from majority voting of $N=5$
reasoning paths.

**Calculation**:
$$ \mathcal{L}_{joint} = \mathcal{L}_{CE} + \lambda \cdot \mathcal{L}_{conf} $$

Where $\mathcal{L}_{conf}$ is the binary cross-entropy between the model's
predicted confidence and the majority-vote proxy correctness.

**Interpretation**:
This loss function forces the model to not only predict the correct token but
also to learn to predict *when* it is likely to be correct, effectively training
a meta-cognitive layer.

## 5. Statistical Significance

**Definition**: To ensure observed improvements are not due to random chance,
we perform paired t-tests across multiple random seeds.

**Metrics Reported**:
- **p-value**: Probability of observing the data if the null hypothesis (no difference)
 is true. p < 0.05 is considered statistically significant.
- **Cohen's d**: Effect size, measuring the magnitude of the difference in standard
 deviation units.
- **Percentage Difference**: The relative improvement of the recursive model over
 the baseline (SC-001).

**Implementation**: See `code/analysis/stats.py`.
