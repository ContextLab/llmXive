# Data Model: Predicting Coral Resilience to Thermal Stress

## 1. Overview

This document defines the data structures used throughout the pipeline. All data is processed in memory or written to temporary files in `data/` and `code/` directories. No persistent database is used.

## 2. Core Entities

### 2.1 Variant Record
Represents a single genetic variant (SNP).
- **Fields**:
  - `chromosome`: String (e.g., "1", "2", "X").
  - `position`: Integer (Genomic coordinate).
  - `id`: String (rsID or custom ID).
  - `ref_allele`: String (Reference allele, e.g., "A").
  - `alt_allele`: String (Alternative allele, e.g., "T").
  - `maf`: Float (Minor Allele Frequency).
  - `missingness`: Float (Proportion of missing calls).
  - `genotypes`: Array of integers (0, 1, 2, or -9 for missing) for each individual.

### 2.2 Phenotype Record (Flexible)
Represents a sample (individual or population).
- **Fields**:
  - `sample_id`: String (Unique identifier for individual) **OR** `population_id` (Unique identifier for population).
  - `survival`: Integer (1 = Survived, 0 = Died) **OR** `mean_survival` (Float, continuous metric for population).
  - `n_individuals`: Integer (Number of individuals in the population, if population-level).
  - `temperature_exposure`: Float (Optional, continuous metric).
  - `population`: String (Optional, population label).

### 2.3 Significant Hit
A variant record that passes statistical significance.
- **Fields**:
  - `variant_id`: String.
  - `p_value`: Float.
  - `q_value`: Float (FDR corrected).
  - `chromosome`: String.
  - `position`: Integer.
  - `gene_annotation`: String (Mapped gene name, if available).

### 2.4 Pathway
A biological functional group.
- **Fields**:
  - `pathway_id`: String.
  - `pathway_name`: String (e.g., "Heat Shock Protein binding").
  - `genes`: List of Strings (Gene IDs).
  - `enrichment_p_value`: Float.
  - `adjusted_p_value`: Float (FDR corrected).
  - `source_species`: String (e.g., "Homo sapiens", "Nematostella vectensis").
  - `confidence_level`: String (e.g., "High", "Medium", "Low").
  - `null_model_adjusted`: Boolean (True if null model correction was applied).

### 2.5 Principal Component
Derived covariate for stratification.
- **Fields**:
  - `pc_id`: Integer (1, 2, 3).
  - `eigenvalue`: Float.
  - `loadings`: Dictionary mapping `sample_id` to Float value.

## 3. Data Flow

1. **Raw Input**: VCF file (text) + Metadata file (CSV/TSV).
2. **Ingested**: `VariantRecord` and `PhenotypeRecord` objects in Pandas DataFrames.
3. **Filtered**: Subset of `VariantRecord` (MAF > 0.05, missingness < 10%).
4. **PLINK Binary**: `.bed`, `.bim`, `.fam` files (intermediate).
5. **PCA Output**: `PrincipalComponent` objects (top 3).
6. **GWAS Output**: `SignificantHit` list (p-values, q-values).
7. **Enrichment Output**: `Pathway` list.
8. **Final Report**: JSON/YAML summary and PNG plots.

## 4. Constraints & Validation

- **Memory**: All intermediate DataFrames must be processed in chunks or converted to binary formats if size > 6 GB.
- **Integrity**: Checksums must be recorded for raw files. Derived files must be regenerated if raw files change.
- **Type Safety**: All numeric fields (p-values, MAF) must be floats. Missing values must be explicitly marked (e.g., -9 or NaN) and handled by the analysis logic.
- **Schema Compliance**: The `filter.py` module must validate its output against `dataset.schema.yaml` to ensure the filtered data matches the required structure.