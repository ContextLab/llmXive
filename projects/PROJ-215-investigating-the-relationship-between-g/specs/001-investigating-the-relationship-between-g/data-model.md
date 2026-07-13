# Data Model: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

## Entities

### 1. MicrobiomeSample
Represents a single subject's microbiome profile.
- `sample_id`: str (Unique identifier)
- `otu_counts`: dict (Taxon ID -> Count) or sparse matrix row
- `sequencing_depth`: int (Total reads)
- `alpha_diversity`: dict (e.g., `{"shannon": float, "simpson": float}`)
- `beta_diversity_coords`: list[float] (PCoA coordinates, e.g., [PC1, PC2, ...])

### 2. MentalHealthRecord
Represents a subject's mental health assessment.
- `sample_id`: str (Foreign key to MicrobiomeSample)
- `phq9_score`: float (0-27)
- `gad7_score`: float (Optional, 0-21, may be null if data unavailable)
- `age`: int (Optional, may be null if not in dataset)
- `bmi`: float (Optional, may be null if not in dataset)
- `diet_category`: str (Optional, e.g., "vegetarian", "omnivore")

### 3. AssociationResult
Represents a statistical finding.
- `variable_name`: str (Taxon ID or "Shannon")
- `correlation_coef`: float
- `p_value`: float
- `adjusted_p_value`: float (q-value)
- `p_value_delta`: float (|p_adjusted - p_unadjusted|)
- `effect_direction`: str ("positive", "negative")
- `covariates_adjusted`: list[str] (e.g., ["age", "bmi"])
- `significant`: bool (True if adjusted_p_value < 0.05)

## Data Flow

1.  **Raw Data**: Downloaded Parquet/CSV files (`data/raw/`).
2.  **Merged Dataset**: `MicrobiomeSample` + `MentalHealthRecord` joined on `sample_id`.
    - *Filter*: Remove rows where `phq9_score` is null.
    - *Filter*: Remove rows where `otu_counts` sum is 0.
    - *Gate*: If merge fails (no common IDs), **HALT** and report "Data Gap".
3.  **Preprocessed Dataset**:
    - Rarefied or VST-transformed OTU table.
    - Filtered taxa (<0.1% prevalence).
    - Calculated diversity metrics.
4.  **Analysis Output**: `AssociationResult` table (CSV/JSON).
5.  **Visualization Data**: PCoA coordinates and heatmap matrices.

## Storage Schema

- **Raw**: `data/raw/agp_microbiome.parquet`, `data/raw/phq9_scores.parquet` (if linked)
- **Processed**: `data/processed/merged_clean.parquet`, `data/processed/diversity_metrics.parquet`
- **Results**: `data/results/associations.csv`, `data/results/pcoa_coords.csv`

## Data Quality Rules

- **Completeness**: `phq9_score` must be non-null for analysis.
- **Range**: `phq9_score` must be 0 ≤ x ≤ 27.
- **Consistency**: `sample_id` must be unique across merged tables.
- **Prevalence**: Taxa with prevalence < 0.1% are excluded.
- **Linkage**: `sample_id` must exist in both OTU table and metadata. If not, analysis is aborted.