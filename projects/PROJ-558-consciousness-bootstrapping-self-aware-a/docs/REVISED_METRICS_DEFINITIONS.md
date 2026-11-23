# Reviewer-Resolved Metrics Definitions

This document clarifies the definitions of key metrics used in the Consciousness Bootstrapping project, addressing ambiguities raised during the review process and ensuring alignment with the specification.

## 1. Self-Consistency Score

**Definition**: The fraction of times the model produces the same final answer when generating N=5 independent reasoning paths for a single question.

**Calculation**:
1. For each question in the benchmark dataset, generate N=5 independent reasoning paths.
2. Extract the final answer from each path.
3. Count the frequency of each unique answer.
4. The self-consistency score for that question is `max_frequency / N`.
5. The overall score is the mean of per-question scores across the dataset.

**Tie-Breaking Rule**: If no strict majority exists (e.g., a 2-2-1 split), the proxy signal defaults to 0 (incorrect) for training purposes. For evaluation, the most frequent answer is still used, but the confidence score reflects the split.

**Significance**: This metric operationalizes the model's ability to maintain a stable internal representation of its own reasoning process. High self-consistency suggests the model is not merely sampling randomly but is converging on a coherent internal state.

## 2. Error Detection Calibration (Brier Score & ECE)

**Definition**: Measures how well the model's predicted confidence scores align with its actual accuracy.

**Brier Score**:
- **Formula**: `B = (1/N) * Σ (confidence_i - actual_i)^2`
- **Where**: `actual_i` is 1 if the answer is correct, 0 otherwise.
- **Interpretation**: Lower is better. A perfect model has a Brier score of 0.

**Expected Calibration Error (ECE)**:
- **Method**: Bin confidence scores into equal-width bins (e.g., 10 bins).
- **Calculation**: For each bin, calculate the difference between the average confidence and the observed accuracy. Weight by the number of samples in the bin.
- **Edge Case Handling**: If a bin contains zero samples, the observed accuracy for that bin is set to 0.0 to prevent division by zero.

**Significance**: A well-calibrated model is "honest" about its uncertainty. This is critical for the "examined life" concept—a system that cannot distinguish between its confident errors and confident correct answers lacks true self-awareness.

## 3. Internal Self-Consistency Proxy (Training Objective)

**Definition**: A proxy signal derived from internal generation used to train the confidence prediction head without external teacher labels.

**Mechanism**:
1. For a given training item, the model generates N=5 reasoning paths.
2. The majority vote of these paths determines a binary "proxy correctness" signal.
3. The model's predicted confidence for the final answer is compared against this proxy.
4. **Tie-Breaking**: If no strict majority (e.g., 2-2-1), the proxy defaults to 0 (incorrect).

**Philosophical Operationalization**: This mechanism allows the model to "learn to trust itself" by comparing its momentary confidence against the stability of its own reasoning. It avoids the tautology of "teacher-student" distillation by using the model's own emergent consensus as the ground truth.

## 4. Percentage Difference in Self-Consistency (SC-001)

**Definition**: The relative improvement in self-consistency between the recursive and baseline models.

**Formula**: `((Recursive_Mean - Baseline_Mean) / Baseline_Mean) * 100`

**Significance**: This metric directly quantifies the impact of temporal recursive self-attention on the model's internal coherence. A positive value indicates that the recursive architecture successfully bootstraps a more stable self-model.

## 5. Sensitivity Analysis Metrics

**Definition**: Measures how the error detection performance varies across different confidence thresholds.

**Metrics Tracked**:
- **False Positive Rate (FPR)**: Fraction of correct answers incorrectly flagged as errors.
- **False Negative Rate (FNR)**: Fraction of incorrect answers missed by the error detector.
- **Delta Metrics**: The change in FPR/FNR compared to a baseline threshold.

**Thresholds Tested**: {0.4, 0.5, 0.6}

**Significance**: This analysis determines the robustness of the error detection mechanism. A system that only works at a single, arbitrary threshold is fragile; a robust system maintains performance across a range of thresholds.
