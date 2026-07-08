# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

## Entities

### Subject
Represents an individual participant.
- `subject_id`: Unique identifier (string).
- `baseline_microbiome`: Dictionary of taxon -> relative abundance.
- `post_vaccination_titer`: Log-transformed antibody titer (float).
- `pre_vaccination_titer`: Log-transformed antibody titer (float, optional).
- `responder_status`: Binary (0/1) based on threshold.
  - *Logic*: 
    - If `pre_vaccination_titer` exists for the subject: `responder_status = 1` if (Fold-Change ≥ 4 OR Absolute Titer ≥ 40) else `0`.
    - If `pre_vaccination_titer` is missing: `responder_status = 1` if (Absolute Titer ≥ 40) else `0`. (Fallback mode).
- `shannon_diversity`: Calculated diversity index (float).
- `responder_mode`: String ("Seroconversion", "Absolute", "Mixed", "Absolute_Fallback").

### Taxon
Represents a microbial taxon.
- `taxon_id`: Unique identifier (string, e.g., "Genus_species").
- `abundance_vector`: List of relative abundances across subjects.
- `clr_abundance_vector`: List of CLR-transformed values.
- `correlation_coefficient`: Spearman rho with titer.
- `raw_p_value`: Raw p-value from correlation test.
- `adjusted_p_value`: BH-corrected p-value.
- `is_significant`: Boolean (adjusted_p < 0.05).

### CorrelationResult
Aggregated output of the correlation phase.
- `taxon_id`: Reference to Taxon.
- `coefficient`: Float.
- `p_value_raw`: Float.
- `p_value_adj`: Float.
- `significant`: Boolean.

### ModelPerformance
Aggregated output of the modeling phase.
- `fold`: Integer (1-5).
- `accuracy`: Float.
- `precision`: Float.
- `recall`: Float.
- `f1_score`: Float.
- `feature_importance`: Dictionary of taxon -> importance.
- `threshold`: Float (the threshold used for this fold).

## Data Flow

1.  **Ingestion**: Raw data (CSV/Parquet) -> `data/raw/`.
2.  **Filtering**: `data/raw/` -> `data/processed/filtered.csv` (Subjects with complete data).
3.  **Zero-Variance Removal**: `filtered.csv` -> `data/processed/filtered_no_zero_var.csv` (T019).
4.  **Transformation**: `filtered_no_zero_var.csv` -> `data/processed/cleared_default.csv` (CLR, Shannon, Pseudocount 1e-6).
5.  **Correlation**: `cleared_default.csv` -> `data/results/correlations.csv` (Coefficients, P-values).
6.  **Modeling**: `cleared_default.csv` + `correlations.csv` -> `data/results/model_metrics.json` (CV results).
7.  **Sensitivity**: `model_metrics.json` -> `data/results/sensitivity_analysis.csv`.
8.  **Comparison**: `model_metrics.json` + `null_distribution.csv` -> `data/results/model_significance.json`.

## Constraints

- **Completeness**: No nulls in `baseline_microbiome` or `post_vaccination_titer`.
- **Uniqueness**: `subject_id` must be unique.
- **Range**: `responder_status` ∈ {0, 1}.
- **Threshold**: `adjusted_p_value` must be calculated via BH correction.
- **Fallback**: If `pre_vaccination_titer` is missing for all subjects, `responder_mode` must be "Absolute_Fallback".
- **Zero-Variance**: Taxa with zero variance must be excluded before CLR transformation.