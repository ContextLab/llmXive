# Data Model: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

## Overview

This document defines the data structures used in the project, ensuring alignment with the `spec.md` and the `plan.md`. The data model is designed to be lightweight, compatible with the CPU-only CI environment, and strictly typed via YAML schemas.

## Core Entities

### 1. Subject
Represents a single participant.
*   `subject_id`: String (Unique identifier).
*   `diagnosis`: String ("ADHD" or "Control").
*   `adhd_rs_score`: Float (Total score, optional).
*   `subscale_inattention`: Float (Optional).
*   `subscale_hyperactivity`: Float (Optional).
*   `mean_fd`: Float (Mean Framewise Displacement).
*   `scrub_fraction`: Float (Fraction of volumes removed).
*   `exclusion_reason`: String (Optional, e.g., "short_time_series", "missing_phenotype").

### 2. ParcelTimeSeries
Represents the preprocessed BOLD signal for a single parcel.
*   `subject_id`: String.
*   `parcel_id`: Integer (1-200).
*   `time_series`: List[Float] (Length N=120).
*   `entropy_value`: Float (Computed Sample Entropy).
*   `variance`: Float (Variance of the time series).
*   `imputed`: Boolean (True if entropy was imputed due to zero variance).

### 3. FeatureMatrix
The aggregated feature set for modeling.
*   `subject_id`: String.
*   `entropy_features`: List[Float] (Length 200).
*   `connectivity_features`: List[Float] (Length 200, PCA reduced).
*   `label_continuous`: Float (ADHD-RS score).
*   `label_binary`: Integer (0=Control, 1=ADHD).
*   `selected_features`: List[Integer] (Indices of features selected after RFE/L1).

### 4. ModelMetrics
Results from cross-validation and testing.
*   `model_type`: String ("entropy", "connectivity", "combined").
*   `metric_type`: String ("pearson_r", "auc").
*   `mean_value`: Float.
*   `std_value`: Float.
*   `p_value_permutation`: Float.
*   `fdr_significant_parcels`: List[Integer].

## Data Flow

1.  **Raw Data** (fMRI NIfTI, Phenotype CSV) -> **Preprocessing** (Scrubbing, Truncation, Motion Regression) -> **Parcel Time Series**.
2.  **Parcel Time Series** -> **Entropy Calculation** -> **Entropy Feature Vector**.
3.  **Parcel Time Series** -> **Connectivity Matrix** -> **PCA** -> **Connectivity Feature Vector**.
4.  **Feature Vectors** -> **Feature Selection** -> **Reduced Feature Vector**.
5.  **Reduced Feature Vectors** + **Labels** -> **Model Training** -> **ModelMetrics**.

## Storage Format

All intermediate and final data will be stored in **CSV** (for tabular data) and **NIfTI** (for imaging, if retained).
*   `data/processed/subject_entropy_features.csv`: The primary feature matrix.
*   `data/processed/exclusions.log`: Log of excluded subjects.
*   `data/processed/model_metrics.json`: Aggregated performance metrics.

## Validation Rules

*   **Entropy Range**: Values must be in [0.1, 1.5].
*   **Time Series Length**: Exactly 120 for all included subjects.
*   **Missing Values**: Must be imputed (median) before modeling.
*   **Diagnosis**: Must be binary (0/1) for classification tasks.
*   **Motion Confound**: If |r(entropy, FD)| > 0.3, a warning is logged.
