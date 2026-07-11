# Data Model: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

## 1. Entity Relationship Overview

The data model is designed to support a linear pipeline: `Raw Data` -> `Preprocessed Data` -> `Connectivity Matrices` -> `Feature Vectors` -> `Model Predictions`.

### 1.1 Core Entities

1.  **Subject**: Represents a participant.
    -   `subject_id`: Unique string (e.g., "sub-001").
    -   `diagnosis`: Enum ("Schizophrenia", "Control").
    -   `motion_flag`: Boolean (True if >2mm motion).
    -   `medication_status`: String (or "Unknown").
2.  **ConnectivityMatrix**: The 90x90 functional connectivity graph for a subject.
    -   `matrix_id`: String (derived from subject_id).
    -   `matrix_data`: 2D Array (90x90).
    -   `source`: Path to raw NIfTI.
3.  **FeatureVector**: The extracted metrics for a subject.
    -   `feature_id`: String.
    -   `metrics`: Dict (global_eff, local_eff, modularity, centrality_prefrontal, etc.).
    -   `label`: Target variable for classification.
4.  **ModelResult**: Output of the classification task.
    -   `run_id`: Timestamp/Hash.
    -   `accuracy`: Float.
    -   `auc`: Float.
    -   `p_value_permutation`: Float.
    -   `coefficients`: Dict (feature importance).

## 2. Data Flow & Formats

### 2.1 Input
-   **Raw**: NIfTI (`.nii.gz`), JSON sidecars.
-   **Format**: 4D NIfTI (x, y, z, time).

### 2.2 Intermediate
-   **Time Series**: 2D NumPy array (90 ROIs x Timepoints).
-   **Correlation Matrix**: 2D NumPy array (90x90), symmetric.
-   **Format**: `.npy` (binary) or `.csv` (human readable).

### 2.3 Output
-   **Feature Table**: Pandas DataFrame saved as `.parquet` (N subjects x 20 features).
-   **Metrics**: JSON report for each subject.
-   **Final Report**: JSON/CSV containing model performance and statistical tests.

## 3. Constraints & Validation

-   **Matrix Dimensions**: Must be exactly 90x90.
-   **Value Range**: Correlation values must be in [, 1].
-   **No NaN**: Any matrix with NaNs is discarded.
-   **Memory**: Feature vectors must fit in <1MB total for 60 subjects.
