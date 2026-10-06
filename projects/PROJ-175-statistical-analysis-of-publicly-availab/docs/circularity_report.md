# Circularity Report: Proxy Label Derivation

## Summary
This analysis utilized Recipe1M ratings as a proxy for compatibility labels (Task T019b).

## Circularity Violation
**Principle VI Violation**: The outcome variable (`compatibility_label`) is derived directly from the `rating` column of the Recipe1M corpus, which is the same source used to generate predictor features (embeddings, co-occurrence).

## Impact
- **Leakage**: The model is trained to predict a target that is statistically dependent on the training features' source distribution.
- **Interpretation**: Results reflect internal corpus correlations, not independent causal relationships.

## Threshold Used
Median Rating: Calculated dynamically from the dataset.

## Recommendation
Results must be interpreted as "Associative Strength within Recipe1M" rather than "Predictive Generalization".