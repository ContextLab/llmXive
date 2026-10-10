# Data Model: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Overview

This document defines the data entities, transformations, and schemas required for the project. All data artifacts must conform to the schemas defined in `contracts/`. Runtime validation will be enforced via Pydantic models.

## Entities

### 1. Species
- `species_name` (str): Scientific name (e.g., *Arabidopsis thaliana*).  
- `phylogenetic_clade` (str): Clade identifier for stratification.  
- `genome_status` (str): `"available"` or `"missing"`.  
- `metabolome_status` (str): `"available"` or `"missing"`.  
- `genome_size_mb` (float): Assembly size (used for filtering > 500 MB).

### 2. BGC Feature
- `species_name` (str): FK to Species.  
- `bgc_type` (str): Predicted class (e.g., `"terpenoid"`, `"alkaloid"`, `"unknown"`).  
- `count` (int): Number of BGCs of this type.  
- `presence` (bool): `true` if `count > 0`.  
- `mapping_source` (str): `"MIBiG"` or `"Pfam"` (fallback).

### 3. Metabolite Target
- `species_name` (str): FK to Species.  
- `inchikey` (str): Unique chemical identifier.  
- `abundance_raw` (float): Raw abundance.  
- `abundance_log` (float): `log(abundance_raw + 1)`.  
- `compound_class` (str): Chemical class (e.g., `"flavonoid"`).

### 4. Model Output
- `model_type` (str): `"RandomForest"`, `"ElasticNet"`, `"GradientBoosting"`, or `"PGLS"`.  
- `r_squared` (float): Coefficient of determination.  
- `pearson_r` (float): Pearson correlation coefficient.  
- `p_value` (float): Significance against phylogenetic permutation baseline.  
- `feature_importance` (dict): Feature → importance score.  
- `cross_val_scores` (list[float]): R² scores from the chosen validation method.  
- `cv_method` (str): `"LOO"`, `"5Fold"` or `"Bootstrap"` (recorded as `"LOO"` for N < 20, `"5Fold"` for N ≥ 20, `"Bootstrap"` when bootstrapping is used).  

## Data Flow

1. **Raw** – Downloaded FASTA/GFF (genomes) and CSV/TSV (metabolites).  
2. **Intermediate** – `bgc_predictions.json`, `metabolite_harmonized.csv`, `tree_pruned.nwk`.  
3. **Processed** – `aligned_matrix.csv` (final feature‑target matrix), optional `pca_features.csv`.  
4. **Final** – `model_metrics.json`, `sensitivity_analysis.csv`.

## Validation & Hygiene

- After each transformation step (download, antiSMASH parsing, alignment, PCA, model training, evaluation) the resulting artifact is validated against its corresponding JSON schema in `contracts/` using Pydantic.  
- Checksums are computed for all raw and derived files; checksum records are stored in the project state file.  
- Zero‑BGC rows are **preserved** during alignment; they are treated as valid data points with `count = 0` and `presence = 0` (addresses Edge‑Case requirement).  

Numeric fields are validated for realistic ranges (e.g., R² ∈ [‑1, 1], counts ≥ 0). Missing values are explicitly handled (filtered or imputed with documented method).

---


