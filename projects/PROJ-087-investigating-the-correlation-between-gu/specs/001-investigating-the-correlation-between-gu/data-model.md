# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## 1. Key Entities

### Sample
A unique biological specimen.
*   **Attributes**: `sample_id` (string), `antibiotic_use_last_3mo` (boolean), `sleep_efficiency` (float, optional), `sleep_duration` (float, optional), `sleep_quality` (float, optional - proxy), `age` (int), `bmi` (float), `diet_category` (string).
*   **Constraints**: `sample_id` is unique. `antibiotic_use_last_3mo` must be boolean. At least one sleep metric must be present.

### DiversityMetric
Derived values for a specific Sample.
*   **Attributes**: `sample_id` (string), `shannon_index` (float), `simpson_index` (float).
*   **Constraints**: Non-negative floats. `NaN` if sample has zero counts.

### Taxon
A specific bacterial classification (OTU/ASV).
*   **Attributes**: `taxon_id` (string), `taxonomy_path` (string, e.g., "Firmicutes;Clostridia;...").
*   **Constraints**: Unique `taxon_id`.

### TaxonAbundance
Count data linking Taxon to Sample.
*   **Attributes**: `sample_id` (string), `taxon_id` (string), `count` (integer).
*   **Constraints**: Count >= 0.

### CorrelationResult
Output of statistical tests.
*   **Attributes**: `metric_pair` (string, e.g., "shannon_sleep_efficiency"), `r` (float), `p_value` (float), `p_adjusted` (float), `n` (int), `method` (string).
*   **Constraints**: `p_adjusted` derived via BH correction.

### AdjustedCorrelationResult
Output of confounder-adjusted tests.
*   **Attributes**: `metric_pair` (string), `r_partial` (float), `p_value` (float), `p_adjusted` (float), `n` (int), `covariates` (string).
*   **Constraints**: `r_partial` derived via Permutation-based Partial Correlation.

## 2. Data Flow

1.  **Raw Input**: OTU Count Table (Sample x Taxon) + Metadata (Sample x Attributes).
2.  **Filter**: Remove rows where `antibiotic_use_last_3mo == True` OR (no sleep metric is present).
3.  **Enrich**: Calculate `shannon_index`, `simpson_index` per sample.
4.  **Merge**: Join Diversity Metrics with Filtered Metadata.
5.  **Analyze**: Compute correlations (Diversity vs Sleep, Taxon vs Sleep).
6.  **Adjust**: Perform Permutation-based Partial Correlation for confounders.
7.  **Output**: `correlation_results.csv`, `adjusted_correlation_results.csv`, `analysis_data.csv`.

## 3. Schema Evolution

| Stage | File | Description |
| :--- | :--- | :--- |
| Raw | `raw/otu_counts.parquet` | Unfiltered OTU table. |
| Raw | `raw/metadata.csv` | Unfiltered metadata. |
| Processed | `processed/analysis_data.csv` | Filtered, merged, diversity-calculated. |
| Result | `results/correlation_results.csv` | Statistical output. |
| Result | `results/adjusted_correlation_results.csv` | Confounder-adjusted output. |
| Result | `results/sensitivity_analysis.csv` | Sensitivity sweep output. |