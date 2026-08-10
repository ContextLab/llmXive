# Circularity Report

## Methodology

Compatibility labels were derived from Recipe1M ratings, which are part of the same corpus used for flavor similarity embeddings.

This creates a circular dependency where the predictor (similarity) and outcome (compatibility) are both derived from the same dataset.

## Implications

- The model may overfit to corpus-specific patterns rather than generalizable compatibility rules.
- Results should be interpreted as correlational within the Recipe1M corpus, not causal.
- Future work should validate findings on independent datasets (e.g., Counterfactual Recipe Generation).

## Threshold Used

Median rating threshold: 3.85

## Recommendation

Consider this analysis as a proxy for true compatibility until independent validation is available.
