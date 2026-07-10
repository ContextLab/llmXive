# Data Model: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Overview

This document defines the data entities, transformations, and schemas required for the project. All data artifacts must conform to the schemas defined in `contracts/`. Runtime validation will be enforced via Pydantic models.

## Entities

### 1. Species
The fundamental unit of analysis.
- **Attributes**:
    - `species_name` (str): Scientific name (e.g., "Arabidopsis thaliana").
    - `phylogenetic_clade` (str): Clade identifier for stratification (e.g., "Brassicales").
    - `genome_status` (str): "available" or "missing".
    - `metabolome_status` (str): "available" or "missing".
    - `genome_size_mb` (float): Size of genome assembly (used for filtering >500MB).

### 2. BGC Feature
Predicted biosynthetic gene cluster.
- **Attributes**:
    - `species_name` (str): Foreign key to Species.
    - `bgc_type` (str): Predicted class (e.g., "terpenoid", "alkaloid", "unknown").
    - `count` (int): Number of BGCs of this type in the genome.
    - `presence` (bool): 1 if count > 0, else 0.
    - `mapping_source` (str): "MIBiG" or "Pfam" (to track fallback usage).

### 3. Metabolite Target
Quantitative metabolite abundance.
- **Attributes**:
    - `species_name` (str): Foreign key to Species.
    - `inchikey` (str): Unique chemical identifier.
    - `abundance_raw` (float): Raw abundance value.
    - `abundance_log` (float): Log-transformed value (log(raw + 1)).
    - `compound_class` (str): Chemical class (e.g., "flavonoid").

### 4. Model Output
Results of the regression analysis.
- **Attributes**:
    - `model_type` (str): "RF", "ElasticNet", "GradientBoosting", "PGLS".
    - `r_squared` (float): Coefficient of determination.
    - `pearson_r` (float): Correlation coefficient.
    - `p_value` (float): Significance against null.
    - `feature_importance` (dict): Map of feature name to importance score.
    - `cv_method` (str): "LOO" or "Bootstrap".

## Data Flow

1.  **Raw**: Downloaded FASTA, GFF, and CSV/TSV from NCBI/PMDB.
2.  **Intermediate**:
    - `bgc_predictions.json`: Output from antiSMASH wrapper.
    - `metabolite_harmonized.csv`: InChIKey-mapped abundance.
    - `tree_pruned.nwk`: Pruned phylogenetic tree.
3.  **Processed**:
    - `aligned_matrix.csv`: Final feature-target matrix (Species x Features).
    - `pca_components.csv`: Reduced dimensionality features (optional).
4.  **Final**:
    - `model_metrics.json`: Aggregated results.
    - `sensitivity_analysis.csv`: Results of threshold sweep.

## Schemas (Contracts)

The following schemas are defined in `contracts/` to ensure data integrity. All data loading functions will use Pydantic models to enforce these schemas at runtime.

- `dataset.schema.yaml`: Defines the structure of the aligned input matrix.
- `feature_matrix.schema.yaml`: Defines the BGC feature matrix.
- `model_output.schema.yaml`: Defines the structure of the regression results.

**Note**: All numeric fields must be validated for range (e.g., R² between -1 and 1, counts >= 0). Missing values must be explicitly handled (e.g., filtered or imputed with documented method).