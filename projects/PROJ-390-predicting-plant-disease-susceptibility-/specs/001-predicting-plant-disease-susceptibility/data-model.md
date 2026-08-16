# Data Model: Predicting Plant Disease Susceptibility

## Overview

This document defines the data structures, schemas, and relationships for the genomic-environmental fusion pipeline. The data model supports the ingestion of raw reads, the generation of variant frequency vectors, the integration of environmental metadata, and the output of model predictions.

## Entity Definitions

### 1. Sample
Represents a single plant specimen.
*   **Attributes**:
    *   `sample_id` (string): Unique identifier (e.g., SRA Run ID).
    *   `species` (string): Crop species (Wheat, Rice, Maize, Tomato, Soybean).
    *   `collection_date` (date): Date of sample collection.
    *   `location` (object): `{latitude, longitude}`.
    *   `disease_status` (string): Target label (Susceptible, Resistant, Unknown).
    *   `phenotype_source` (string): **Mandatory**. Independent source of the disease label (e.g., "Field Trial ID: XYZ-123"). If missing, sample is excluded (FR-010).
    *   `source_type` (string): "Real" or "Synthetic".

### 2. GenomicFeature
Represents a genomic variant derived from SRA reads.
*   **Attributes**:
    *   `variant_id` (string): Chromosome:Position:Ref:Alt.
    *   `frequency` (float): Allele frequency in the sample.
    *   `type` (string): SNP, INDEL.
    *   `collinearity_status` (string): "Retained", "Pruned", "PCA-Reduced".

### 3. EnvironmentalFeature
Represents environmental context.
*   **Attributes**:
    *   `variable` (string): "temperature", "precipitation", "humidity".
    *   `value` (float): Measured value.
    *   `unit` (string): "Celsius", "mm", "%".
    *   `imputed` (boolean): True if value was imputed.

### 4. ModelOutput
Represents the result of the predictive model.
*   **Attributes**:
    *   `model_type` (string): "RandomForest" or "SVM".
    *   `sample_id` (string): Reference to Sample.
    *   `predicted_probability` (float): Probability of susceptibility.
    *   `predicted_class` (string): "Susceptible" or "Resistant".
    *   `feature_importance` (map): {feature_name: importance_score}.
    *   `variance_explanation` (float): **Mandatory**. Percentage of variance explained by this feature group.

## Data Flow

1.  **Raw Ingestion**: `SRA_Raw.fastq` -> `Environmental_Raw.json`.
2.  **Label Validation**: `label_validation.log` (Phase 0.5).
3.  **Processing**: `Variant_Frequencies.csv`, `Environmental_Clean.csv`.
4.  **Dimensionality Reduction**: `reduced_feature_matrix.csv` (PCA/LD pruning).
5.  **Fusion**: `feature_matrix.csv` (merged, imputed with k-NN).
6.  **Modeling**: `model_performance.json`, `predictions.csv`, `variance_decomposition.json`.

## Schema Constraints

*   **Missing Values**: The `feature_matrix` MUST have zero missing values after imputation (FR-004).
*   **Imputation Method**: MUST be **k-NN** (Constitution Principle VI).
*   **Collinearity**: Features with $r^2 > 0.8$ MUST be marked as "Pruned" (FR-009).
*   **Labels**: `disease_status` MUST be derived from an independent source (FR-010) and documented in `phenotype_source`.
*   **Data Completeness**: The system MUST report `missing_values_before_imputation` percentage (SC-005).

## File Formats

*   **Input**: FASTQ (SRA), JSON (Environmental).
*   **Intermediate**: CSV (Variant Frequencies), CSV (Environmental), `label_validation.log`.
*   **Final**: CSV (Feature Matrix), JSON (Model Metrics), PNG (Plots).