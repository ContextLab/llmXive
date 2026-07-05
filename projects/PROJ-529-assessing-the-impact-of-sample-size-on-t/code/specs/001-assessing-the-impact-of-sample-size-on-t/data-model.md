# Data Model Specification

## Entities

### MetaAnalysis
Represents a single meta-analysis study from the corpus.
- `meta_id`: Unique identifier (string).
- `source`: Origin (e.g., "Cochrane", "Campbell", "Simulation").
- `total_studies`: Total number of studies (N) in the full meta-analysis (integer).
- `effect_sizes`: List of effect sizes (float).
- `standard_errors`: List of standard errors (float).
- `outcome_type`: Type of outcome (e.g., "continuous", "binary").

### Subsample
Represents a single bootstrap iteration for a specific k.
- `subsample_id`: Unique identifier (string).
- `meta_id`: Reference to parent MetaAnalysis.
- `k`: Number of studies in this subsample (integer).
- `seed`: Random seed used for generation (integer).
- `estimator_type`: "FE" or "RE" (string).
- `pooled_effect`: Calculated pooled effect size (float).
- `pooled_se`: Standard error of the pooled effect (float).
- `ci_lower`: Lower bound of 95% CI (float).
- `ci_upper`: Upper bound of 95% CI (float).

### StabilityMetric
Aggregated metrics for a specific k and meta-analysis.
- `meta_id`: Reference to MetaAnalysis.
- `k`: Study count (integer).
- `sd_effects`: Standard deviation of pooled effects across all subsamples for this k (float).
- `coverage_rate`: Proportion of subsample CIs containing the full-sample estimate (float).
- `n_subsamples`: Number of subsamples generated (integer).

## Storage Formats
- **Raw Data**: JSON/CSV in `data/raw/`.
- **Processed Data**: Parquet in `data/processed/` for efficient columnar access.
- **Metrics**: CSV in `data/processed/` for analysis.
