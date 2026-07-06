# Data Model: Predicting Plant Stress Response

## 1. Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to model output. All data is stored in CSV/Parquet format to ensure reproducibility and ease of inspection.

## 2. Entity Definitions

### 2.1 Raw Dataset Metadata
Represents the source of the data before processing.

| Field | Type | Description |
| :--- | :--- | :--- |
| `accession_id` | string | Unique ID (e.g., GSE12345, PXD000123) |
| `source` | string | "NCBI_GEO" or "ProteomeXchange" |
| `species` | string | "Arabidopsis", "Oryza_sativa", "Triticum_aestivum" |
| `stress_type` | string | "Drought", "Salinity", "Heat" |
| `download_date` | date | ISO 8601 date of fetch |
| `checksum` | string | SHA-256 of the raw file |
| `sample_size` | integer | Number of samples in the dataset (for FR-001 selection) |
| `publication_date` | date | Date of publication (for FR-001 tie-breaking) |

### 2.2 Processed Sample (Unified Matrix)
The core analysis unit after merging proteomic and transcriptomic data.

| Field | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | string | Unique identifier for the sample |
| `species` | string | Plant species |
| `stress_type` | string | Stress condition |
| `protein_1` | float | Normalized abundance of Protein 1 (imputed) |
| `protein_2` | float | Normalized abundance of Protein 2 |
| ... | ... | ... |
| `gene_1` | float | Normalized expression of Gene 1 (target) |
| `gene_2` | float | Normalized expression of Gene 2 |
| ... | ... | ... |
| `is_training` | boolean | True if in training set |
| `protein_residual_1` | float | Residualized protein abundance (Stress-Blind Baseline) |
| ... | ... | ... |

*Note: The actual number of protein/gene columns is dynamic based on the intersection of identifiers. Residualized features are generated during the Stress-Blind Baseline step.*

### 2.3 Model Output
Results from the training and evaluation phase.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "RandomForest" or "SVR" |
| `train_stress` | string | Stress type used for training |
| `test_stress` | string | Stress type used for testing (can be same or different) |
| `r2_score` | float | Coefficient of determination |
| `rmse` | float | Root Mean Squared Error |
| `n_samples` | integer | Number of samples in the test set |
| `feature_importance` | list | List of (protein_name, score) tuples |
| `validation_strategy` | string | "within_stress_cv", "cross_stress", "target_permutation", "stress_blind_baseline" |

### 2.4 Data Completeness Metric
Calculated metric for SC-004.

| Field | Type | Description |
| :--- | :--- | :--- |
| `query_species` | string | Species queried |
| `query_stress` | string | Stress queried |
| `initial_datasets` | integer | Total datasets found matching query |
| `retained_datasets` | integer | Datasets successfully merged and retained |
| `completeness_percentage` | float | (retained / initial) * 100 |

## 3. Data Flow

1.  **Ingestion**: Raw files (CSV/TSV) -> `RawDatasetMetadata` -> `download.py` -> `data/raw/`.
2.  **Normalization**: `data/raw/*` -> `normalize.py` -> `data/processed/normalized.csv` (proteins only).
3.  **Merging**: `data/processed/normalized.csv` + Transcriptomic data -> `merge.py` -> `data/processed/unified_matrix.csv`.
4.  **Modeling**: `data/processed/unified_matrix.csv` -> `train.py` (with Stress-Blind Baseline) -> `results/metrics.json`.
5.  **Reporting**: `results/metrics.json` -> `plots.py` -> `results/figures/*.png`.

## 4. Constraints & Validation

*   **Missing Values**: No `NaN` allowed in the final `unified_matrix.csv` after MinProb imputation.
*   **Identifier Consistency**: All protein IDs must be UniProt; all gene IDs must be Ensembl.
*   **Stress Labels**: Must be one of: `Drought`, `Salinity`, `Heat`.
*   **Preprocessing**: All normalization and imputation must be performed within CV folds to prevent data leakage (SC-005).