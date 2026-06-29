# Proxy Susceptibility Score Method

## Overview

This document specifies the proxy susceptibility score computation method used
in the Bayesian hierarchical modeling of misinformation cascade size. The score
is derived from historical user network context to avoid circular validation
with the outcome variable.

## Formula (FR-003 Clarification)

The proxy susceptibility score is computed per user using the following binary
threshold formula:

```
susceptibility_score = (historical_degree >= 2 AND historical_shares >= 1) ? 1.0: 0.0
```

Where:
- `historical_degree`: The average degree of the user's connections in the
 pre-cascade network context (computed from historical network data, NOT from
 the cascade graph itself to avoid circularity).
- `historical_shares`: The number of times the user has shared content in the
 historical period preceding the cascade.

## Rationale

This formula captures users who are both:
1. **Well-connected** (degree >= 2): Having multiple connections increases the
 potential for content propagation through their network.
2. **Active sharers** (shares >= 1): Demonstrating prior sharing behavior
 indicates a propensity to amplify content.

Users meeting both criteria receive a susceptibility score of 1.0, indicating
higher likelihood of amplifying misinformation. Users failing either criterion
receive 0.0.

## Implementation

The computation is implemented in `code/pipeline/user_susceptibility.py` with
the following behavior:

- Input: CSV file containing `historical_degree` and `historical_shares` columns
- Output: CSV file with an added `susceptibility_score` column
- Missing columns default to 0, resulting in a score of 0.0

## Usage in Pipeline

The susceptibility score is computed as part of the feature engineering stage
(Phase 3, T016) and is included as a predictor in the Bayesian hierarchical
model. The score contributes to the fixed effects component of the model,
estimating the impact of user susceptibility on cascade size.

## Fallback Behavior

If historical network data is unavailable for a user, the fallback behavior is:
- Default `historical_degree` to 0
- Default `historical_shares` to 0
- Resulting susceptibility score: 0.0

This conservative approach ensures that users with missing data are not
incorrectly classified as highly susceptible.

## References

- FR-003: Feature Requirements Clarification
- T062: Implement proxy susceptibility score with formula
- T016: Implement user_susceptibility.py to compute the susceptibility score
- T017: Synthetic dataset generation using the same formula
- data-model.md: FeatureSet schema definition
- contracts/features.csv: JSON schema for feature output validation
