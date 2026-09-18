# Data Model: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## 1. Data Entities

### 1.1 Raw Sample (OxfordPets)
-   `sample_id`: Unique identifier (string).
-   `prompt`: Text prompt (string).
-   `image_url`: Path to image (string).

### 1.2 Synthetic Teacher/Student Record
-   `sample_id`: Reference to Raw Sample.
-   `teacher_scores`: Object containing 4 floats: `alignment`, `realism`, `aesthetics`, `plausibility`. (Generated).
-   `student_scalar`: Single float (student's scalar reward). (Generated).
-   `human_annotations`: Object containing 4 floats (or null). (Generated).
-   `training_dimension`: String (e.g., "alignment").
-   `target_dimension`: String (e.g., "realism").

### 1.3 Feature Record
Derived from Synthetic Record.
-   `sample_id`: Reference.
-   `teacher_variance`: Float.
-   `teacher_entropy`: Float.
-   `teacher_skewness`: Float.
-   `teacher_kurtosis`: Float.
-   `mean_teacher_score`: Float.
-   `theoretical_baseline_error`: Float (Analytical derivation).
-   `observed_mae`: Float (MAE between student and target dimension).
-   `residual_error`: Float (Observed MAE - Theoretical Baseline).
-   `is_valid`: Boolean.
-   `vif_filtered_features`: Array of strings (features retained after VIF check).

### 1.4 Global Entanglement Report
-   `global_covariance_matrix`: 4x4 array.
-   `global_dominant_eigenvalue`: Float.
-   `dataset_id`: String.
-   `timestamp`: ISO8601.

## 2. Data Flow

1.  **Ingest**: `code/ingest.py` reads raw parquet -> validates schema -> writes `data/processed/raw_samples.parquet`.
2.  **Simulate**: `code/simulate.py` generates teacher/student scores -> writes `data/processed/synthetic_records.parquet`.
3.  **Feature Eng**: `code/features.py` computes stats, VIF, and theoretical baseline -> writes `data/processed/features.parquet` and `data/processed/global_entanglement_report.json`.
4.  **Train**: `code/model.py` trains model on `residual_error` -> writes `data/processed/predictions.parquet` and `data/processed/metrics.json`.

## 3. Storage Format

-   **Raw**: Parquet (compressed).
-   **Processed**: Parquet (compressed) for tabular data; JSON for metrics and covariance matrices.
-   **Checksums**: SHA-256 recorded in `state/projects/...yaml`.