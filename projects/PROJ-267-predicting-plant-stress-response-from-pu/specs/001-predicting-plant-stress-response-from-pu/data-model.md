# Data Model: Predicting Plant Stress Response from Publicly Available Proteomic Data

## 1. Entity Relationship Overview

The data model supports the ingestion of raw proteomic and transcriptomic data, their harmonization via identifier mapping, and the creation of a unified training matrix.

### 1.1 Key Entities

-   **ProteomicSample**: A measurement of protein abundance for a specific sample.
-   **TranscriptomicSample**: A measurement of gene expression for a specific sample.
-   **StressCondition**: The environmental stress applied (Drought, Salinity, Heat).
-   **UnifiedMatrix**: The final dataset where rows are samples, columns are protein features, and the target is gene expression.

## 2. Data Flow

1.  **Raw Ingestion**: Downloaded files (GEO/ProteomeXchange) -> `data/raw/`.
2.  **Preprocessing**:
    -   Filter low-abundance proteins.
    -   Impute missing values (LCM).
    -   Map IDs (Protein -> Gene).
    -   Merge Proteomic + Transcriptomic.
    -   Output -> `data/processed/unified_matrix.csv`.
3.  **Modeling**:
    -   Split by Stress Condition.
    -   Train/Test split.
    -   Output -> `results/model_artifacts/`.

## 3. Schema Definitions

### 3.1 Raw Data Schema (Proteomic)

| Column | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | string | Unique sample identifier. |
| `protein_id` | string | Protein accession (e.g., UniProt). |
| `abundance` | float | Raw abundance value. |
| `stress` | string | Stress condition (Drought, Salinity, Heat). |
| `species` | string | Plant species (Arabidopsis, Rice, Wheat). |

### 3.2 Raw Data Schema (Transcriptomic)

| Column | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | string | Unique sample identifier (must match Proteomic). |
| `gene_id` | string | Gene accession (e.g., Ensembl). |
| `expression` | float | Raw expression count (TPM/FPKM). |
| `stress` | string | Stress condition. |
| `species` | string | Plant species. |

### 3.3 Unified Matrix Schema (Processed)

| Column | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | string | Unique sample ID. |
| `stress` | string | Stress condition. |
| `species` | string | Plant species. |
| `protein_1` | float | Normalized abundance of Protein 1. |
| `protein_2` | float | Normalized abundance of Protein 2. |
| ... | float | ... |
| `target_gene_expression` | float | Mapped gene expression (Target). |

## 4. Constraints & Rules

-   **Uniqueness**: `sample_id` + `protein_id` must be unique in raw proteomic data.
-   **Completeness**: Samples without a matching transcriptomic counterpart are dropped.
-   **Imputation**: Missing values in `abundance` are filled using LCM; missing values in `expression` are dropped (if >10% missing) or imputed (if <10%).
-   **Mapping**: Only rows where `protein_id` successfully maps to a `gene_id` are retained.
