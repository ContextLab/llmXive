# Data Model: The Role of Epigenetic Drift in Adaptive Landscape Exploration

## 1. Overview

This document defines the data structures used throughout the pipeline, ensuring strict adherence to the **Multi-Omic Data Integrity** principle. Data flows from raw repository downloads to unified variance matrices, then to statistical results. **Crucially, variance is calculated using a Leave-One-Generation-Out (LOGO) jackknife to ensure independence between predictor and outcome samples.**

## 2. Core Entities

### 2.1 OmicsDataset
Represents a raw data collection from GEO/ENCODE.
-   **Fields**:
    -   `accession_id`: Unique identifier (e.g., GSE12345).
    -   `organism`: String (mouse, C. elegans, Drosophila).
    -   `data_type`: String (methylation, rna_seq).
    -   `condition`: String (fluctuating, constant).
    -   `stressor_type`: String (optional, e.g., "temperature", "nutrient"). **Added to control for confounding.**
    -   `generations`: Integer (count of generations).
    -   `fluctuation_timescale`: String (optional, e.g., "daily", "hourly").
    -   `source_url`: String (Verified URL).
    -   `checksum`: String (SHA-256 of raw file).

### 2.2 GeneVarianceProfile
Derived entity containing calculated variances for a specific gene. **Uses LOGO jackknife to ensure disjoint sample sets.**
-   **Fields**:
    -   `gene_id`: String (e.g., ENSMUSG00000000001).
    -   `epigenetic_variance`: Float (CV of methylation, normalized, calculated on **odd generations**).
    -   `expression_variance`: Float (Variance of normalized counts, calculated on **even generations**).
    -   `organism`: String.
    -   `condition`: String.
    -   `stressor_type`: String (optional).
    -   `generation_count`: Integer.
    -   `disjoint_samples`: Boolean (True if variance calculated on disjoint sets).
    -   `uncertainty_interval`: Tuple (Float, Float) (95% CI for variance estimate).
    -   `is_valid`: Boolean (True if both variances > 0 and data present).

### 2.3 CorrelationResult
Entity storing the result of a statistical analysis run.
-   **Fields**:
    -   `analysis_id`: String (UUID).
    -   `rho`: Float (Spearman correlation coefficient).
    -   `p_value_theoretical`: Float.
    -   `p_value_empirical`: Float (from permutation test).
    -   `sample_size`: Integer (number of genes analyzed).
    -   `condition`: String.
    -   `stressor_type`: String (optional).
    -   `threshold_generations`: Integer.
    -   `temporal_resolution_flag`: String (e.g., "sufficient", "insufficient"). **Added for Principle VII.**
    -   `associational_only`: Boolean (Always True). **Explicitly marks the result as non-causal.**
    -   `timestamp`: ISO8601.

## 3. Data Flow

1.  **Ingestion**: Raw files (Parquet/CSV) downloaded from verified URLs -> `data/raw/`.
2.  **Preprocessing**:
    -   `code/preprocess/methyl.py`: Reads raw methylation -> Normalizes -> Calculates variance on **odd generations** -> Outputs `methyl_variance_odd.csv`.
    -   `code/preprocess/rna_seq.py`: Reads raw RNA-seq -> Normalizes -> Calculates variance on **even generations** -> Outputs `rna_variance_even.csv`.
3.  **Integration**:
    -   `code/analysis/correlation.py`: Merges `methyl_variance_odd.csv` and `rna_variance_even.csv` on `gene_id`.
    -   Filters out invalid rows (zero variance, missing data).
4.  **Analysis**:
    -   Computes Spearman's $\rho$ and performs permutation test.
    -   **Checks temporal resolution**: If N<3 or timescale missing, sets `temporal_resolution_flag: "insufficient"`.
    -   Outputs `correlation_results.json`.
5.  **Visualization**:
    -   `code/viz/plots.py`: Reads `correlation_results.json` and `GeneVarianceProfile` data -> Generates `scatter_plot.png`.

## 4. Constraints & Validation

-   **Immutability**: Raw files in `data/raw/` are never modified. Derivations are written to new files.
-   **Checksums**: Every file in `data/` must have a recorded SHA-256 checksum in the project state YAML.
-   **Separation**: Methylation and RNA-seq processing modules are isolated to prevent cross-contamination.
-   **Disjoint Samples**: Variance calculation **MUST** use disjoint generation sets (LOGO) to avoid circular validation.
-   **Zero Variance**: Genes with zero variance in both layers are explicitly excluded to prevent division by zero errors.
-   **Temporal Flag**: If `temporal_resolution_flag` is "insufficient", the result is excluded from the final association claim.
