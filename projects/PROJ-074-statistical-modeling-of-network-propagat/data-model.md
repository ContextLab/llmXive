# Data Model Specification

This document defines the data schemas used throughout the Bayesian hierarchical modeling pipeline for misinformation cascade size analysis.

## Overview

The pipeline processes three main data artifacts:
1. **Cascade**: Raw cascade data from JSON edge-list files
2. **FeatureSet**: Engineered features for modeling
3. **ModelOutput**: Posterior samples and summaries from Bayesian inference

## Cascade Schema

Cascades are ingested as JSON edge-list files with the following structure:

```json
{
 "cascade_id": "string",
 "nodes": [
 {
 "node_id": "string",
 "timestamp": "ISO8601 UTC",
 "user_id": "string",
 "message_id": "string",
 "platform_id": "string",
 "historical_degree": "integer",
 "historical_shares": "integer"
 }
 ],
 "edges": [
 {
 "source": "string",
 "target": "string"
 }
 ]
}
```

**Validation Rules:**
- All timestamps must be normalized to UTC (ISO8601 format)
- Required fields: `node_id`, `timestamp`, `cascade_id`
- Cascades exceeding 2,000 nodes are logged to `skipped_cascades.log` and skipped
- Only JSON edge-list format is accepted

## FeatureSet Schema

The FeatureSet is a tabular dataset (CSV) containing engineered features for each cascade. This schema must align with `contracts/features.json`.

```csv
cascade_id,user_id,message_id,platform_id,susceptibility_score,mean_degree,std_degree,clustering_coefficient,mean_betweenness,cascade_size
```

**Required Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `cascade_id` | string | Unique cascade identifier |
| `user_id` | string | User who initiated the cascade |
| `message_id` | string | Message identifier |
| `platform_id` | string | Social media platform |
| `susceptibility_score` | float (0.0-1.0) | Proxy susceptibility score per FR-003 |
| `mean_degree` | float | Mean degree of nodes in pre-cascade network context |
| `std_degree` | float | Standard deviation of degree distribution |
| `clustering_coefficient` | float | Average clustering coefficient |
| `mean_betweenness` | float | Mean betweenness centrality |
| `cascade_size` | integer | Total number of nodes in cascade (outcome variable) |

**Optional Additional Columns:**
- Any additional numeric predictor columns are permitted
- All numeric columns must have no missing values

**Validation:**
- All required columns must be present
- No missing values in any column
- All numeric columns must be finite (no NaN, inf)
- Schema validation against `contracts/features.json` is performed before model fitting

## ModelOutput Schema

Posterior samples are stored in NetCDF format (`model_trace.nc`), and summaries are exported as CSV (`posterior_summary.csv`).

### posterior_summary.csv Schema

```csv
predictor,mean,sd,lower_95,upper_95,prob_nonzero,direction_consistent
```

**Required Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `predictor` | string | Predictor variable name |
| `mean` | float | Posterior mean estimate |
| `sd` | float | Posterior standard deviation |
| `lower_95` | float | 2.5th percentile (95% CI lower bound) |
| `upper_95` | float | 97.5th percentile (95% CI upper bound) |
| `prob_nonzero` | float | Posterior probability of non-zero effect |
| `direction_consistent` | boolean | TRUE if effect sign matches across folds |

## Validation Pipeline Integration

FeatureSet validation is integrated into the pipeline as follows:

1. **Pre-processing**: `validate_all_cascades()` in `code/pipeline/utils.py` validates cascade JSON files against schema
2. **Feature Engineering**: After feature extraction, `validate_features()` checks that `features.csv` matches the FeatureSet schema
3. **Model Fitting**: Pipeline aborts if validation fails with clear error messages

Validation is enforced via:
- JSON schema validation using `jsonschema` library
- Column completeness checks
- Missing value detection
- Type consistency verification

## References

- `contracts/features.json`: JSON Schema for FeatureSet validation
- `contracts/posterior_summary.json`: JSON Schema for model output validation
- `quickstart.md`: Pipeline execution instructions
- `model_spec.yaml`: Model specification with priors and hyperparameters