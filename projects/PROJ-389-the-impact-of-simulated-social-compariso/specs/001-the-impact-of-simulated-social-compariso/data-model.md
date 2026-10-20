# Data Model: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

## Overview
The pipeline produces three core artifacts that are validated against JSON‑Schema contracts located in `contracts/`.

| Artifact | Description | Format | Contract |
|----------|-------------|--------|----------|
| `raw_user_comments.parquet` | Aggregated per‑user comment stream (exposure content only). | Parquet | N/A (raw source) |
| `processed_features.csv` | One row per `user_id` with all predictor variables, additional covariates, and `self_eval_score`. | CSV | `contracts/processed_features.schema.yaml` |
| `regression_results.csv` | Results of hierarchical regression, including interaction coefficients, corrected p‑values, VIF scores, and subgroup metadata. | CSV | `contracts/regression_results.schema.yaml` |

## Processed Features Schema (`contracts/processed_features.schema.yaml`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Processed Features"
type: object
required:
  - user_id
  - exposure_level
  - authenticity_score
  - engagement_proxy
  - curated_aesthetic_score
  - self_eval_score
properties:
  user_id:
    type: string
    description: "Unique Reddit user identifier"
  exposure_level:
    type: number
    description: "Weighted subreddit‑wide exposure proxy (0‑1) derived from subreddit‑level comment volume, not from the user’s own comments"
  authenticity_score:
    type: number
    description: "Rule‑based vulnerability‑marker score (0‑1)"
  engagement_proxy:
    type: number
    description: "Average comment depth or thread participation count"
  curated_aesthetic_score:
    type: number
    description: "Fraction of comments containing markdown formatting or image links"
  self_eval_score:
    type: number
    description: "Sentiment‑adjusted first‑person pronoun ratio derived **solely** from the user’s own comments"
  total_comment_count:
    type: integer
    description: "Total number of comments authored by the user"
  subreddit_popularity_score:
    type: number
    description: "Aggregate popularity (comment count) of subreddits the user posted in"
  month_of_activity:
    type: integer
    description: "Month (1‑12) of the dominant activity period for the user"
  demographic_proxy:
    type: string
    description: "Derived demographic label (e.g., \"young_female\", \"older_male\", \"unknown\")"
  notes:
    type: string
    description: "Optional log notes (e.g., low‑variance skip flag, imputation flag)"
```

## Regression Results Schema (`contracts/regression_results.schema.yaml`)
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Regression Results"
type: object
required:
  - model_id
  - subgroup
  - coefficients
  - p_values
  - corrected_p_values
  - interaction_term_significant
  - vif_scores
  - sample_size
properties:
  model_id:
    type: string
    description: "Identifier for the regression model (e.g., \"model3_interaction\")"
  subgroup:
    type: string
    description: "Demographic subgroup label (\"global\" if no stratification)"
  coefficients:
    type: object
    description: "Mapping from predictor name to estimated coefficient"
    additionalProperties:
      type: number
  p_values:
    type: object
    description: "Raw p‑values for each predictor"
    additionalProperties:
      type: number
  corrected_p_values:
    type: object
    description: "Benjamini‑Hochberg FDR‑adjusted p‑values"
    additionalProperties:
      type: number
  interaction_term_significant:
    type: boolean
    description: "True if the interaction term's corrected p‑value < 0.05"
  vif_scores:
    type: object
    description: "Variance Inflation Factor for each predictor"
    additionalProperties:
      type: number
  sample_size:
    type: integer
    description: "Number of observations used in this regression"
  notes:
    type: string
    description: "Optional free‑text notes (e.g., low‑variance skip, collinearity warning)"
```

All schemas are single‑document YAML files with quoted strings where needed.

---

