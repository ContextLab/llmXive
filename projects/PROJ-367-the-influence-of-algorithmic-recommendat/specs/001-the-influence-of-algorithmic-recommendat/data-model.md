# Data Model: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Key Entities

### UserSession
Represents a single observation window for a specific user.
- **Attributes**:
  - `user_id`: Unique identifier for the learner.
  - `session_id`: Unique identifier for the session.
  - `recommended_categories`: List of category strings (derived from VLE access logs).
  - `enrolled_categories`: List of category strings the user actually enrolled in.
  - `recommendation_diversity_score`: Calculated Shannon entropy of `recommended_categories`.
  - `learner_diversity_score`: Calculated Shannon entropy of `enrolled_categories` (or null).

### Baseline_Interest_Vector
A vector representing the user's historical topic preferences.
- **Attributes**:
  - `user_id`: Link to `UserSession`.
  - `category_frequencies`: Dictionary mapping category names to counts/frequencies from pre-study history.
  - `normalized_vector`: Probability distribution over categories.

### ModelResult
Output object from the statistical modeling phase.
- **Attributes**:
  - `coefficient`: Estimated effect of `Recommendation_Diversity` on `Learner_Diversity`.
  - `std_error`: Standard error of the coefficient.
  - `p_value`: P-value for the coefficient.
  - `weights`: Array of propensity scores/weights used.
  - `vif`: Variance Inflation Factor for baseline controls.
  - `convergence_status`: Boolean indicating model convergence.

## Data Flow

1. **Ingestion**: Raw OULAD data -> `cleaned_data.parquet` (validated schema).
2. **Preprocessing**: `cleaned_data.parquet` -> `diversity_scores.json` (entropy calculated, categories merged).
3. **Modeling**: `diversity_scores.json` + `baseline_vectors` -> `model_results.csv`.
4. **Robustness**: `model_results.csv` -> `sensitivity_analysis.csv`, `permutation_test_results.json`.

## Schema Definitions

### Input Schema (Raw Data)
- `user_id`: String
- `session_id`: String
- `recommended_categories`: List[String] (JSON array or comma-separated string)
- `enrolled_categories`: List[String] (JSON array or comma-separated string)
- `pre_study_history`: List[String] (optional, for baseline calculation)

### Output Schema (Processed)
- `user_id`: String
- `session_id`: String
- `recommendation_diversity_score`: Float (nullable)
- `learner_diversity_score`: Float (nullable)
- `baseline_vector`: Dictionary (String -> Float)
- `weight`: Float
- `model_coefficient`: Float
- `model_p_value`: Float

## Assumptions & Constraints

- **Missing Data**: Rows with empty `enrolled_categories` are excluded from the final regression but logged.
- **Semantic Merging**: Categories are merged if semantic similarity < threshold (default 0.05).
- **Baseline Imputation**: Users with no pre-study history receive a uniform baseline vector.
- **Small Sample**: If N < 30, GLS is used instead of weighted regression.