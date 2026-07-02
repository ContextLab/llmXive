# Data Model: Predict Plant Disease Resistance from Multi‑omics Data

## 1. Overview

This document defines the data structures for the plant disease resistance prediction pipeline. It covers the input data (raw and processed), the feature tables, and the output artifacts.

## 2. Entity Definitions

### Sample
A single plant individual with available data.
*   `sample_id`: Unique identifier (string).
*   `phenotype`: Resistance score (float) or label (string: "Resistant", "Susceptible").
*   `metadata`: Dictionary containing species, pathogen, experimental conditions.

### Genomic Feature (SNP)
A genetic variant.
*   `snp_id`: Unique identifier (e.g., "chr1:12345:A:T").
*   `chromosome`: Chromosome name.
*   `position`: Genomic coordinate.
*   `allele_ref`: Reference allele.
*   `allele_alt`: Alternate allele.
*   `genotype`: Genotype value (0, 1, 2 for homozygous ref, heterozygous, homozygous alt).

### Metabolomic Feature
A detected metabolite.
*   `metabolite_id`: Unique identifier (e.g., "HMDB12345").
*   `name`: Common name.
*   `intensity`: Normalized intensity value.

## 3. Data Flow & Transformations

### Raw Data
*   **Input**: FASTQ files (genomics), MS spectra files (metabolomics), Phenotype CSV.
*   **Storage**: `data/raw/` (preserved, checksummed).
*   **Synthetic Fallback**: If real data is missing, `data/raw/synthetic_data.h5` is generated with the same structure.

### Preprocessed Data
*   **SNP Matrix**: `samples x variants` (0, 1, 2). Missing values imputed or filtered.
*   **Metabolite Matrix**: `samples x metabolites` (normalized intensity).
*   **Phenotype Vector**: `samples x 1`.
*   **Aligned Feature Table**: Concatenation of SNP and Metabolite matrices, filtered to only samples present in all three.
    *   *Constraint*: If `n_samples < 100`, pipeline halts (FR-007).

### Output Artifacts
*   **Model**: Serialized sklearn/xgboost model object.
*   **Feature Importance**: CSV of top 50 SNPs and metabolites with p-values and effect sizes.
*   **Metrics**: JSON file containing CV accuracy, permutation p-value, VIF diagnostics.
*   **Selection Frequency**: CSV of feature IDs, thresholds, and selection frequency (FR-003).

## 4. Schema Definitions (Contracts)

The following schemas are defined in `contracts/`:
1.  `dataset.schema.yaml`: Validates the structure of the input/processed data (including synthetic data).
2.  `output.schema.yaml`: Validates the structure of the results (metrics, features).

These schemas are used to validate the output of the synthetic data generator and the final pipeline results.