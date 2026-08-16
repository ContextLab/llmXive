# Data Model: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Overview

This document defines the data structures, schemas, and relationships used in the analysis pipeline. The data flows from raw ingestion through transformation to final statistical results.

## Entities

### UserSession
Represents a single observation window for a specific user.
- **Attributes**:
  - `user_id`: Unique identifier for the user.
  - `session_id`: Unique identifier for the session.
  - `recommended_categories`: List of category strings provided by the algorithm.
  - `enrolled_categories`: List of category strings selected by the user.
  - `recommendation_diversity_score`: Shannon entropy of `recommended_categories`.
  - `learner_diversity_score`: Shannon entropy of `enrolled_categories`.
  - `baseline_interest_vector`: Vector representing historical preferences.
  - `propensity_score`: Estimated probability of receiving a diverse recommendation.
  - `weight`: Propensity score weight for regression.

### DiversityScore
A scalar value representing the Shannon entropy of a category distribution.
- **Attributes**:
  - `value`: Float (entropy value).
  - `base`: Integer (log base, default 2).
  - `is_valid`: Boolean (false if input list is empty).

### ModelResult
The output object containing model statistics.
- **Attributes**:
  - `coefficient`: Float (effect of recommendation diversity).
  - `standard_error`: Float.
  - `p_value`: Float.
  - `vif`: Float (Variance Inflation Factor).
  - `convergence_status`: Boolean.
  - `method`: String ("Weighted Regression", "GLS", or "Robust Linear Regression").
  - `e_value`: Float (sensitivity to unmeasured confounding).

## Data Flow

1. **Raw Data**: CSV/Parquet with `user_id`, `session_id`, `recommended_categories`, `enrolled_categories`.
2. **Processed Data**: JSON/Parquet with calculated `recommendation_diversity_score`, `learner_diversity_score`, `baseline_interest_vector`.
3. **Weighted Data**: Dataframe with `weight` column added.
4. **Results**: JSON/CSV with `ModelResult` objects and diagnostic metrics.

## Schema Definitions

### Input Schema (Raw)
- `user_id`: string
- `session_id`: string
- `recommended_categories`: list of strings
- `enrolled_categories`: list of strings

### Intermediate Schema (Processed)
- `user_id`: string
- `session_id`: string
- `recommendation_diversity_score`: float (nullable)
- `learner_diversity_score`: float (nullable)
- `baseline_interest_vector`: list of floats
- `propensity_score`: float
- `weight`: float

### Output Schema (Results)
- `coefficient`: float
- `standard_error`: float
- `p_value`: float
- `vif`: float
- `method`: string
- `e_value`: float
- `sensitivity_analysis`: list of {threshold, coefficient, p_value}
- `permutation_p_value`: float

## Assumptions & Constraints

- **Missing Data**: If `enrolled_categories` is empty, `learner_diversity_score` is null and the row is excluded from regression.
- **Baseline Vector**: If no prior history, a uniform distribution is imputed (documented).
- **Collinearity**: If VIF > 5.0, a warning is logged, and the result is flagged.
- **Small Sample**: If unique users < 30, GLS is used instead of weighted regression.
- **Synthetic Data**: If no verified real-world dataset is found, the data is generated synthetically with a fixed seed. The results are interpreted as a methodological demonstration.
