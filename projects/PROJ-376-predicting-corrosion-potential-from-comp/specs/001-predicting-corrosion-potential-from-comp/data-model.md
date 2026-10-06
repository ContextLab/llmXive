# Data Model: Predicting Corrosion Potential from Composition and Environment

## Overview

This document defines the data structures, schemas, and transformations used in the corrosion potential prediction pipeline. It ensures that all data ingestion, processing, and modeling steps adhere to a strict schema, preventing data leakage and ensuring reproducibility.

## Entity Definitions

### 1. AlloyRecord
Represents a specific metallic alloy with its elemental composition.
*   **Specific Alloy Designation**: Unique string identifier (e.g., "SS304", "Inconel625").
*   **Base Metal Family**: Categorical (e.g., "Fe-based", "Ni-based").
*   **Elemental Composition**: Dictionary of element symbol to weight fraction (float, 0.0-1.0). Sum of all fractions must be 1.0.
*   **Metadata**: Source ID, publication year (optional).

### 2. EnvironmentRecord
Represents the testing conditions for a corrosion measurement.
*   **pH**: Float (continuous). Valid range: 0.0 - 14.0.
*   **Temperature**: Float (continuous). Unit: Celsius.
*   **Electrolyte Type**: Categorical (e.g., "Saline", "Acidic", "Alkaline", "Neutral").
*   **Agitation**: Categorical (e.g., "Static", "Flowing").

### 3. CorrosionMeasurement
Represents the target variable linked to an AlloyRecord and EnvironmentRecord.
*   **Corrosion Potential**: Float. Unit: millivolts (mV) vs Standard Hydrogen Electrode (SHE).
*   **Measurement Method**: String (e.g., "ASTM G59", "Open Circuit Potential").
*   **Record ID**: Unique identifier linking Alloy, Environment, and Measurement.

### 4. ModelResult
Output of the training phase.
*   **Model Type**: String (e.g., "RandomForest", "GradientBoosting").
*   **Hyperparameters**: Dictionary of model settings.
*   **Metrics**: Dictionary containing R², RMSE, and Null Baseline comparison.
*   **Feature Importance**: Dictionary of feature name to importance score and p-value.

## Data Flow & Transformations

1.  **Ingestion**: Raw data (JSONL/CSV) is downloaded and stored in `data/raw/`.
2.  **Validation**: `validate_schema.py` checks for:
    *   Non-null values for composition, pH, temperature, corrosion.
    *   pH in [0, 14].
    *   Sum of weight fractions = 1.0 (within tolerance).
    *   Minimum 500 valid records.
    *   Minimum 10 unique `specific_alloy_designation` values.
3.  **Preprocessing**:
    *   Missing pH/Temp/Corrosion rows are **dropped** (logged).
    *   pH > 14 or < 0 rows are **flagged** and moved to `data/processed/extreme_conditions.csv`.
    *   Categorical variables (Electrolyte) are one-hot encoded.
    *   Elemental compositions are transformed using **Centred Log-Ratio (CLR)**.
4.  **Splitting**:
    *   **Group Split**: Groups are defined by `specific_alloy_designation`.
    *   **Train**: All records for a set of alloys.
    *   **Test**: All records for a held-out set of alloys (e.g., 1-2 alloys).
    *   **Fallback**: If 10-14 alloys, use GroupKFold(k=5).
    *   **Validation**: Zero overlap check between train/test alloy IDs.

## File Formats

*   **Raw Data**: JSONL or CSV (preserved as downloaded).
*   **Processed Data**: Parquet (for efficient I/O and type safety) or CSV.
*   **Logs**: JSONL (structured logs for pipeline steps).
*   **Schemas**: YAML (for contract validation).

## Assumptions & Constraints

*   **Composition Normalization**: The pipeline assumes the raw data provides weight fractions that sum to 1.0. If not, a normalization step is applied, and the original values are logged.
*   **pH Scale**: The standard aqueous pH scale (0-14) is assumed. Non-aqueous or extreme conditions are handled separately.
*   **Corrosion Potential**: Values are assumed to be vs SHE. If vs another reference (e.g., Ag/AgCl), a conversion factor is applied if documented; otherwise, the record is flagged.
*   **Compositional Data**: Feature importance on raw weight fractions is descriptive only due to the closure problem. A CLR transformation is the primary method used to mitigate this.