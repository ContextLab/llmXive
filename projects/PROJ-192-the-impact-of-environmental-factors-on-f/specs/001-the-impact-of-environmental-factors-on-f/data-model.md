# Data Model: Impact of Environmental Factors on Fungal Community Structure in Soil

## Overview
This document defines the data structures used throughout the pipeline. All data is stored in `data/` (raw/derived) and validated against schemas in `contracts/`.

## Key Entities

### 1. ASV Table
*   **Description**: A sparse matrix of Amplicon Sequence Variant counts per sample.
*   **Format**: `scipy.sparse.csr_matrix` in memory; saved as `.npz` or `.csv` (dense) if small.
*   **Columns**: ASV IDs (strings).
*   **Rows**: Sample IDs (strings).
*   **Values**: Integer counts.

### 2. Environmental Matrix
*   **Description**: A dataframe of scaled abiotic variables per sample.
*   **Format**: CSV (`data/metadata/harmonized.csv`).
*   **Columns**:
    *   `sample_id`: String (unique).
    *   `pH`: Float.
    *   `nitrogen`: Float (mg/kg or ppm).
    *   `phosphorus`: Float (mg/kg or ppm).
    *   `potassium`: Float (mg/kg or ppm).
    *   `temperature`: Float (°C).
    *   `moisture`: Float (%).
    *   `biome`: String (standardized ontology).
    *   `study_id`: String (source identifier).

### 3. Distance Matrices
*   **Description**: Pairwise dissimilarity matrices.
*   **Format**: `scipy.spatial.distance` condensed array or `.npy`.
*   **Types**:
    *   `bray_curtis`: Community beta-diversity.
    *   `euclidean`: Environmental distance.

### 4. RDA Model Object
*   **Description**: Statistical model linking environment to community.
*   **Format**: Pickled object (`.pkl`) containing model coefficients, R², and significance.
*   **Attributes**: `r_squared`, `p_value`, `fdr_p_value`, `variance_explained`.

### 5. Stratum
*   **Description**: Subset of data for biome-specific analysis.
*   **Format**: Filtered ASV Table and Environmental Matrix.

### 6. Sampling Report
*   **Description**: Log of subsampling events.
*   **Format**: CSV (`results/sampling_report.csv`).
*   **Columns**: `dataset_id`, `original_n`, `sampled_n`, `ratio`, `timestamp`.

## Data Flow

1.  **Ingestion**: Raw FASTQs (if available) → `data/raw-seq/`.
2.  **Preprocessing**: FASTQs → ASV Table (`data/processed/asv_table.npz`).
3.  **Harmonization**: Raw Metadata → `data/metadata/harmonized.csv`.
4.  **Imputation**: `harmonized.csv` (with NAs) → `data/metadata/imputed.csv`.
5.  **Analysis**: ASV Table + Imputed Metadata → `results/permanova_summary.csv`, `results/db_rda_variance.csv`.
6.  **Reporting**: `results/sensitivity_analysis.csv`, `results/robustness_summary.md`.

## Constraints

*   **Immutability**: Raw files in `data/raw-seq/` are never modified.
*   **Checksums**: All files in `data/` and `results/` have corresponding `.sha256` files.
*   **Memory**: Large matrices are processed in chunks or subsampled.
