# Data Model: 001-predict-plant-disease-resistance

## Overview

This document defines the data structures for the plant disease resistance prediction pipeline. The model ensures alignment between genomic (SNP) and metabolomic features with phenotypic resistance scores.

## Key Entities

### Sample
A single plant individual with complete data modalities.
- **Attributes**:
  - `sample_id`: Unique identifier (string).
  - `study_accession`: Source study ID (e.g., SRP123456).
  - `resistance_phenotype`: Either a continuous score (float) or categorical label (string: "resistant"/"susceptible").
  - `metadata`: Dictionary of additional biological info (species, tissue type).

### FeatureTable
Aligned matrix of features.
- **Structure**:
  - `snps`: DataFrame (samples × SNPs). Values: 0, 1, 2 (allele counts) or missing.
  - `metabolites`: DataFrame (samples × Metabolites). Values: normalized intensity (float).
  - `phenotypes`: Series (samples). Values: resistance score/label.

### ModelOutput
Results from the training and validation pipeline.
- **Attributes**:
  - `metrics`: Dictionary (accuracy, AUC, R², null_baseline).
  - `selected_features`: List of top SNPs and metabolites with p-values and effect sizes.
  - `permutation_p_value`: Float.
  - `vif_diagnostics`: Dictionary of VIF scores for selected features.

## Data Flow

1. **Raw Data**: Downloaded from NCBI SRA (FASTQ) and MetaboLights (raw spectra).
2. **Processed Data**:
   - `snp_matrix.csv`: Aligned SNP matrix.
   - `metabolite_matrix.csv`: Normalized metabolite matrix.
   - `phenotype.csv`: Resistance labels.
3. **Analysis Data**: Combined `feature_table.csv` (samples × features) with phenotype.
4. **Output**: `results.json`, `biomarkers.csv`, `validation_report.txt`.

## Constraints

- **Sample Size**: Minimum 100 paired samples required (FR-007, FR-008).
- **Missing Data**: Samples with missing modalities are excluded (FR-001).
- **Data Integrity**: All raw files checksummed; derived files versioned.
