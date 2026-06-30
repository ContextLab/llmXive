# Data Model: Predicting Plant Defense Compound Production

## Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    POPULATION ||--|{ GENOMIC_VARIANT : "has variants"
    POPULATION ||--|{ ENVIRONMENTAL_CONTEXT : "located in"
    POPULATION ||--|{ DEFENSE_COMPOUND : "produces"
    POPULATION ||--|{ PCA_COVARIATE : "has structure control"
    
    POPULATION {
        string population_id PK
        float latitude
        float longitude
        string source_study
    }
    
    GENOMIC_VARIANT {
        string population_id FK
        float heterozygosity
        float nucleotide_diversity
        string vcf_file_path
    }
    
    ENVIRONMENTAL_CONTEXT {
        string population_id FK
        float mean_temp
        float total_precip
        float soil_ph
    }
    
    DEFENSE_COMPOUND {
        string population_id FK
        string compound_id
        float concentration
    }
    
    PCA_COVARIATE {
        string population_id FK
        float pc_1
        float pc_2
        float pc_3
        ...
    }
```

## Schema Definitions

### Population (Primary Unit)
-   `population_id`: String (Unique ID, e.g., "At-1001-001")
-   `latitude`: Float (Decimal degrees)
-   `longitude`: Float (Decimal degrees)
-   `source_study`: String (Identifier for the study/database source)

### Genomic Metrics (Derived)
-   `population_id`: String (FK)
-   `heterozygosity`: Float (0.0 to 1.0)
-   `nucleotide_diversity`: Float (Pi)
-   `missingness_rate`: Float (0.0 to 1.0)

### Environmental Context
-   `population_id`: String (FK)
-   `mean_annual_temp`: Float (°C)
-   `annual_precipitation`: Float (mm)
-   `soil_ph`: Float (0-14)

### PCA Covariates (Control for Structure)
-   `population_id`: String (FK)
-   `pc_1`: Float (Principal Component 1)
-   `pc_2`: Float (Principal Component 2)
-   `pc_3`: Float (Principal Component 3)
-   `pc_N`: Float (Top N components used for control)

### Defense Compound (Outcome)
-   `population_id`: String (FK)
-   `compound_id`: String (e.g., "Glucosinolate-01")
-   `concentration`: Float (Z-score normalized per study)

## Data Flow

1.  **Raw Ingestion**: VCF -> `data/raw/vcf/`; Environmental Parquet -> `data/raw/env/`; Compound CSV -> `data/raw/compounds/`. (Or Mock Generation).
2.  **Validation**: Check for non-null IDs. Log missing populations.
3.  **Aggregation**: VCF -> `heterozygosity` (per population); Env -> `mean_temp` (per population).
4.  **Structure Control**: VCF -> PCA -> `pc_1...pc_N` (per population).
5.  **Merge**: Inner join on `population_id`. Listwise deletion for missing modalities.
6.  **Feature Matrix**: `[heterozygosity, nucleotide_diversity, mean_temp, pc_1, pc_2, ...]` -> `X`.
7.  **Target Vector**: `[concentration]` -> `y`.