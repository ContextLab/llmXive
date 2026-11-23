# Data Model: Predicting Plant Herbivore Resistance

## Overview

This document defines the data structures used throughout the pipeline, ensuring alignment with the functional requirements (FR-001 to FR-008) and the project constitution (Data Hygiene, Reproducibility).

## Key Entities

### 1. RawMetabolomicRecord
Represents the raw data row as extracted from the source file.
*   `sample_id`: String (Unique identifier)
*   `genotype_id`: String (Plant genotype)
*   `metadata`: Dictionary (Raw key-value pairs from source)
*   `raw_values`: Dictionary (Metabolite names -> raw abundance values)
*   `resistance_raw`: String or Float (Raw resistance metric from metadata)

### 2. ProcessedSample
The cleaned, normalized, and imputed data row ready for modeling.
*   `sample_id`: String
*   `genotype_id`: String
*   `resistance_score`: Float (Normalized numeric value)
*   `metabolite_abundances`: List of Float (Normalized, imputed values)
*   `imputation_flag`: Boolean (True if any value was imputed)
*   `batch_id`: String or Null (Extracted from metadata if present)
*   `herbivore_density`: Float or Null (If available, else Null)

### 3. ModelOutput
The result of the predictive model.
*   `model_id`: String (Hash of training data + params)
*   `feature_importance`: List of Tuple (Metabolite Name, Importance Score)
*   `performance_metrics`: Dictionary (R², MSE, Accuracy if classification)
*   `top_metabolites`: List of String (Top 20 ranked metabolites)

### 4. ValidationResult
The result of statistical validation.
*   `permutation_p_value`: Float
*   `is_significant`: Boolean
*   `adjusted_q_values`: Dictionary (Metabolite Name -> q-value)
*   `significant_metabolites`: List of String (Metabolites with q < 0.10)

## Data Flow

1.  **Ingestion**: `RawMetabolomicRecord` -> `ProcessedSample` (via normalization, imputation).
2.  **Training**: `ProcessedSample` (Train Set) -> `ModelOutput`.
3.  **Validation**: `ModelOutput` + `ProcessedSample` (Test Set) -> `ValidationResult`.
4.  **Reporting**: `ModelOutput` + `ValidationResult` -> Final Report.

## Storage Schema

*   **Raw Data**: `data/raw/<accession_id>_raw.csv` (Checksummed, immutable).
*   **Processed Data**: `data/processed/<accession_id>_processed.csv` (Derived).
*   **Model Artifacts**: `data/processed/<accession_id>_model.pkl` (if needed for reproducibility) or just the output CSVs.
*   **Results**: `data/processed/<accession_id>_results.json`.

## Constraints

*   **Immutability**: Raw files are never modified.
*   **Checksums**: All files in `data/raw` must have a corresponding `.sha256` file.
*   **PII**: No personally identifiable information allowed (public data assumed PII-free, but scanned).
