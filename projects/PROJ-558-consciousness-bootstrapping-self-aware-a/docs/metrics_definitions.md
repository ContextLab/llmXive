# Metrics Definitions

This document provides the formal definitions and computational methods for the key metrics used in the Consciousness Bootstrapping project.

## 1. Self-Consistency

**Definition**: A measure of the stability of a model's output across multiple reasoning paths generated for the same input.

**Computation**:
1. Generate **N=10** reasoning paths for a given question (per FR-003).
2. Parse the final answer from each path.
3. Compute the majority vote of the answers.
4. The self-consistency score is the proportion of paths that agree with the majority vote.
5. **Tie-Breaking**: If no unique majority exists (e.g., 5 vs 5), the score is calculated based on the first generated path as the reference, or the instance is marked as inconsistent depending on the specific benchmark rules.

**Interpretation**: Higher scores indicate greater internal stability of the model's reasoning process.

## 2. Calibration (Brier Score & ECE)

**Definition**: A measure of how well the model's predicted confidence matches its actual accuracy.

### Brier Score
**Formula**: $BS = \frac{1}{N} \sum_{i=1}^{N} (f_i - o_i)^2$
* $f_i$: Predicted confidence (probability) for the $i$-th prediction.
* $o_i$: Binary outcome (1 if correct, 0 if incorrect).
**Interpretation**: Lower scores indicate better calibration. A score of 0 is perfect.

### Expected Calibration Error (ECE)
**Computation**:
1. Bin predictions into $M$ bins (e.g., 10 bins) based on confidence.
2. For each bin $b$, calculate the average confidence ($\bar{c}_b$) and the accuracy ($a_b$).
3. Compute the weighted average of the absolute difference: $ECE = \sum_{b=1}^{M} \frac{|B_b|}{N} |a_b - \bar{c}_b|$.
**Interpretation**: Lower scores indicate better alignment between confidence and accuracy.

## 3. Error Detection (ROC-AUC)

**Definition**: The ability of the model's confidence score to discriminate between correct and incorrect predictions.

**Computation**:
1. Treat the model's confidence score as the "positive class" probability.
2. Treat correctness (1=correct, 0=incorrect) as the ground truth label.
3. Calculate the Area Under the Receiver Operating Characteristic Curve (ROC-AUC).
**Interpretation**:
* 0.5: Random guessing.
* 1.0: Perfect error detection.
* > 0.5: The model is better than random at knowing when it is wrong.

## 4. Confidence Proxy (Training Signal)

**Definition**: A binary signal derived from the model's own N=2 generation paths used during training to supervise the confidence head.

**Computation**:
1. Generate 2 paths.
2. Majority vote determines "correctness" (1) or "incorrectness" (0).
3. Tie (1 vs 1) resolves to 0.
4. This binary value is the target for the confidence prediction loss.

**Note**: This is distinct from the N=10 evaluation metric. It is a training-time proxy for self-consistency.
