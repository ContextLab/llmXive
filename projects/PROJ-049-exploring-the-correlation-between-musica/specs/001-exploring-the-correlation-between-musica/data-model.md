# Data Model: Exploring the Correlation Between Musical Preference and Personality Traits

## 1. Raw Dataset Schema (`dataset.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Raw BFI‑2 and Last.fm Linked Dataset"
type: object
required:
  - user_id
  - lastfm_username
  - openness_score
  - conscientiousness_score
  - extraversion_score
  - agreeableness_score
  - neuroticism_score
  - age
  - gender
  - country
  - listening_history
properties:
  user_id:
    type: string
    description: "Hashed participant identifier."
  lastfm_username:
    type: string
    description: "Username on Last.fm used for linking."
  openness_score:
    type: number
    minimum: 0
    maximum: 100
  conscientiousness_score:
    type: number
    minimum: 0
    maximum: 100
  extraversion_score:
    type: number
    minimum: 0
    maximum: 100
  agreeableness_score:
    type: number
    minimum: 0
    maximum: 100
  neuroticism_score:
    type: number
    minimum: 0
    maximum: 100
  age:
    type: integer
    minimum: 0
  gender:
    type: string
    enum: ["Male", "Female", "Other"]
  country:
    type: string
  listening_history:
    type: object
    description: "Mapping from raw genre tag to total listening minutes for this user."
    additionalProperties:
      type: number
      minimum: 0
```

## 2. Processed Dataset Schema (`processed_dataset.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Processed Dataset for Analysis"
type: object
required:
  - user_id
  - openness_score
  - conscientiousness_score
  - extraversion_score
  - agreeableness_score
  - neuroticism_score
  - age
  - gender_onehot
  - country_onehot
  - total_minutes
  - genre_proportions
  - genre_ilr
properties:
  user_id:
    type: string
  openness_score:
    type: number
  conscientiousness_score:
    type: number
  extraversion_score:
    type: number
  agreeableness_score:
    type: number
  neuroticism_score:
    type: number
  age:
    type: integer
  gender_onehot:
    type: object
    additionalProperties:
      type: integer
      enum: [0,1]
  country_onehot:
    type: object
    additionalProperties:
      type: integer
      enum: [0,1]
  total_minutes:
    type: number
    minimum: 0
  genre_proportions:
    type: object
    description: "Proportion of total listening minutes per standardized genre (Rock, Pop, …, Other)."
    additionalProperties:
      type: number
      minimum: 0
      maximum: 1
  genre_ilr:
    type: object
    description: "ILR‑transformed compositional vector derived from `genre_proportions`."
    additionalProperties:
      type: number
```

## 3. Analysis Output Schema (`analysis_output.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Combined Analysis Output Schema"
type: object
required:
  - correlation_results
  - regression_results
  - diagnostics
properties:
  correlation_results:
    $ref: "./correlation_results.schema.yaml"
  regression_results:
    $ref: "./regression_results.schema.yaml"
  diagnostics:
    type: array
    items:
      type: object
      required:
        - model_trait
        - issue
        - action
      properties:
        model_trait:
          type: string
        issue:
          type: string
        action:
          type: string
```

## 4. Correlation Results Schema (`correlation_results.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Spearman Correlation Results Schema"
type: array
items:
  type: object
  required:
    - trait
    - genre
    - spearman_rho
    - p_value
    - adjusted_p_value
    - is_significant
    - cohens_d
    - ci_lower
    - ci_upper
  properties:
    trait:
      type: string
      enum:
        - "openness"
        - "conscientiousness"
        - "extraversion"
        - "agreeableness"
        - "neuroticism"
    genre:
      type: string
      enum:
        - "Rock"
        - "Pop"
        - "Hip-Hop"
        - "Classical"
        - "Electronic"
        - "Jazz"
        - "Folk"
        - "Country"
        - "Metal"
        - "Other"
    spearman_rho:
      type: number
      minimum: -1
      maximum: 1
    p_value:
      type: number
      minimum: 0
      maximum: 1
    adjusted_p_value:
      type: number
      minimum: 0
      maximum: 1
    is_significant:
      type: boolean
    cohens_d:
      type: number
    ci_lower:
      type: number
    ci_upper:
      type: number
```

## 5. Regression Results Schema (`regression_results.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ILR‑Based Multiple Regression Results"
type: array
items:
  type: object
  required:
    - trait
    - predictor
    - coefficient
    - std_error
    - p_value
    - adjusted_p_value
    - is_significant
  properties:
    trait:
      type: string
      enum:
        - "openness"
        - "conscientiousness"
        - "extraversion"
        - "agreeableness"
        - "neuroticism"
    predictor:
      type: string
      description: "One of the ILR components, age, gender_onehot, or country_onehot."
    coefficient:
      type: number
    std_error:
      type: number
    p_value:
      type: number
      minimum: 0
      maximum: 1
    adjusted_p_value:
      type: number
      minimum: 0
      maximum: 1
    is_significant:
      type: boolean
```

## 6. Report Schema (`report.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Final Results Report"
type: object
required:
  - summary_statistics
  - significant_findings
  - limitations
properties:
  summary_statistics:
    type: object
    description: "Counts of total tests, significant after correction, and power analysis outcome."
    required:
      - total_tests
      - significant_tests
      - required_sample_size
      - actual_sample_size
      - power_note
    properties:
      total_tests:
        type: integer
      significant_tests:
        type: integer
      required_sample_size:
        type: integer
      actual_sample_size:
        type: integer
      power_note:
        type: string
  significant_findings:
    type: array
    items:
      $ref: "./correlation_results.schema.yaml#/items"
  limitations:
    type: string
    description: "Narrative description of data or methodological constraints."
```

## 7. Results Schema (`results.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Coefficient Deltas Schema"
description: "Schema for results/coefficient_deltas.csv containing regression coefficient changes and validity status."
type: object
required:
  - trait
  - genre
  - beta_baseline
  - beta_full
  - delta
  - vif
  - validity_status
properties:
  trait:
    type: string
    description: "Big Five trait name."
  genre:
    type: string
    description: "Standardized genre name."
  beta_baseline:
    type: number
    description: "Beta coefficient from baseline model (Trait only)."
  beta_full:
    type: number
    description: "Beta coefficient from full model (Trait + Covariates)."
  delta:
    type: number
    description: "Difference beta_full - beta_baseline."
  vif:
    type: number
    description: "Variance Inflation Factor for the full model."
    minimum: 1
  validity_status:
    type: string
    description: "Flag indicating whether delta exceeds 10 % change threshold (e.g., \"valid\"; \"exceeds_threshold\")."
```
