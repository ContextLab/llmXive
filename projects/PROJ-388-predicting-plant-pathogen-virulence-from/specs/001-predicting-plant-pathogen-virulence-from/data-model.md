# Data Model: Predicting Plant Pathogen Virulence

## Entity Definitions

### Isolate
A unique biological sample.
- **Attributes**:
  - `isolate_id`: String (Unique identifier, e.g., "Fusarium_001")
  - `species`: String (e.g., "Fusarium graminearum")
  - `genome_accession`: String (NCBI Accession, e.g., "GCA_000001234.5")
  - `phenotype_score`: Float (0.0 to 1.0, or NaN if missing)
  - `source_url`: String (URL to the specific record)

### SpeciesAggregate
A grouped dataset where phenotypic scores are averaged across isolates of the same species.
- **Attributes**:
  - `species_id`: String (e.g., "Fusarium_graminearum")
  - `mean_phenotype_score`: Float (Average disease severity)
  - `isolate_count`: Integer (Number of isolates aggregated)
  - `source`: String (e.g., "Literature_Aggregation")

### GenomicFeature
A binary or count feature derived from the genome.
- **Attributes**:
  - `feature_id`: String (e.g., "PHI_12345", "PWM_TF_01")
  - `feature_type`: Enum ("gene_presence", "tf_binding_count")
  - `isolate_id`: String (Foreign key)
  - `value`: Integer (0 or 1 for presence, count for TF)

### PhylogeneticTree
A Newick formatted tree constructed from housekeeping genes.
- **Attributes**:
  - `tree_id`: String
  - `newick_string`: String
  - `source`: String (e.g., "Core_Gene_Constructed")
  - `method`: String (e.g., "Maximum_Likelihood")
  - `is_ultrametric`: Boolean

### PhylogeneticCovarianceMatrix
The correlation structure matrix derived from the tree, used for PGLS.
- **Attributes**:
  - `matrix_id`: String
  - `tree_id`: String (Foreign key)
  - `covariance_matrix`: Array (2D float array)
  - `method`: String (e.g., "Brownian_Motion")

### AnalysisResult
The output of the correlation analysis.
- **Attributes**:
  - `feature_id`: String
  - `correlation_coefficient`: Float (ρ)
  - `p_value`: Float
  - `adjusted_p_value`: Float (FDR-corrected)
  - `is_significant`: Boolean (Adjusted p < 0.05)
  - `effect_size_category`: Enum ("Weak", "Moderate", "Strong")
  - `analysis_mode`: Enum ("Isolate_Level", "Species_Aggregate_Descriptive")

### DescriptiveSummary
Output for cases where N < 10 (e.g., species-level fallback).
- **Attributes**:
  - `species_id`: String
  - `mean_phenotype_score`: Float
  - `top_features`: Array (List of top feature IDs by raw correlation)
  - `note`: String (e.g., "No statistical testing performed due to N < 10")

## Data Flow

1.  **Raw Data**:
    -   `data/raw/genomes/`: FASTA files downloaded from NCBI.
    -   `data/raw/phenotypes/`: TSV/CSV from PHI-base or literature.
2.  **Processed Data**:
    -   `data/processed/feature_matrix.csv`: Isolate x Feature matrix.
    -   `data/processed/phenotype_vector.csv`: Isolate x Score.
    -   `data/processed/tree.newick`: Phylogenetic tree.
    -   `data/processed/phylo_covariance_matrix.npy`: Covariance matrix.
3.  **Output Data**:
    -   `data/results/correlation_table.csv`: Full results (if N >= 10).
    -   `data/results/descriptive_summary.json`: Descriptive summary (if N < 10).
    -   `data/results/significant_features.json`: Filtered list.

## Constraints
- **Missing Data**: `phenotype_score` can be NaN. Rows with NaN are excluded from analysis but logged.
- **Feature Values**: `value` must be non-negative integer.
- **Correlation**: `correlation_coefficient` must be in [-1, 1].
- **Statistical Validity**: If `analysis_mode` is "Species_Aggregate_Descriptive", `adjusted_p_value` must be null and `is_significant` must be false.