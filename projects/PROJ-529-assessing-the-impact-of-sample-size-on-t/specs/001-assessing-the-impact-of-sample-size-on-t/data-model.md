# Data Model

## Entities
- **MetaAnalysis**: Container for a single meta-analysis study.
 - `id`: Unique identifier
 - `studies`: List of Study objects
 - `pooled_effect`: Float
 - `pooled_se`: Float

- **Subsample**: A bootstrap sample of a MetaAnalysis.
 - `meta_id`: Reference to MetaAnalysis
 - `k`: Number of studies in subsample
 - `seed`: Random seed used
 - `effect_sizes`: List of floats
 - `ses`: List of floats

- **StabilityMetric**: Aggregated metric for a specific k.
 - `k`: Number of studies
 - `sd_effects`: Standard deviation of pooled effects across subsamples
 - `coverage_rate`: Proportion of CIs containing true effect