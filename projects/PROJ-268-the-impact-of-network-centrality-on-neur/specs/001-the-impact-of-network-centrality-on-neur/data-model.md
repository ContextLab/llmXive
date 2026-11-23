# Data Model: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

## 1. Overview

This document defines the data structures used throughout the pipeline. The model is designed to be lightweight, reproducible, and compatible with the GitHub Actions runner constraints.

## 2. Core Entities

### 2.1 Subject
Represents a single participant in the study.
- **Attributes**:
  - `subject_id`: Unique identifier (string).
  - `raw_data_path`: Path to raw NIfTI files (if available).
  - `sc_matrix_path`: Path to the Structural Connectivity Matrix (400x400).
  - `fc_matrix_path`: Path to the Functional Connectivity Matrix (400x400).
  - `status`: "valid", "excluded", "corrupted".
  - `exclusion_reason`: Reason for exclusion (e.g., "FD > 0.5mm").

### 2.2 ConnectivityMatrix
Represents the 400x400 adjacency matrix.
- **Attributes**:
  - `matrix`: 2D NumPy array (float32).
  - `type`: "structural" or "functional".
  - `atlas`: "Schaefer400".
  - `threshold`: (Optional) Density threshold used for structural matrix.

### 2.3 NodeMetrics
Represents the computed metrics for each of the 400 nodes.
- **Attributes**:
  - `node_id`: Integer (0-399).
  - `region_name`: Name of the ROI (from Schaefer atlas).
  - `degree_centrality`: Float.
  - `betweenness_centrality`: Float.
  - `eigenvector_centrality`: Float.
  - `functional_synchrony`: Float (mean absolute correlation).

### 2.4 AnalysisResult
Represents the output of the statistical analysis.
- **Attributes**:
  - `metric_type`: "degree", "betweenness", "eigenvector".
  - `rho`: Spearman correlation coefficient.
  - `p_value_uncorrected`: Raw p-value.
  - `p_value_permutation`: Permutation-corrected p-value.
  - `effect_size_ci`: 95% Confidence Interval (Fisher's z).
  - `n_permutations`: Number of permutations (1000).
  - `threshold_density`: The density threshold used for the structural matrix.

### 2.5 ProcessingSummary
Represents the logging of the pipeline execution and success metrics.
- **Attributes**:
  - `target_subjects`: Integer (10).
  - `processed_subjects`: Integer.
  - `skipped_subjects`: Integer.
  - `proportion`: Float (processed/target).
  - `status`: "success", "partial", "failed".
  - `reason`: String (if failed/partial).

## 3. Data Flow

1.  **Raw Data** (NIfTI) → **Preprocessing** → **ConnectivityMatrix** (SC, FC).
2.  **ConnectivityMatrix** → **Metric Computation** → **NodeMetrics**.
3.  **NodeMetrics** → **Statistical Analysis** → **AnalysisResult**.
4.  **AnalysisResult** → **Visualization** → **Report**.
5.  **Pipeline Execution** → **ProcessingSummary**.

## 4. File Format Specifications

### 4.1 Connectivity Matrices
- **Format**: NumPy `.npy` or HDF5 `.h5`.
- **Shape**: (400, 400).
- **Data Type**: Float32.

### 4.2 Node Metrics
- **Format**: CSV.
- **Columns**: `node_id`, `region_name`, `degree_centrality`, `betweenness_centrality`, `eigenvector_centrality`, `functional_synchrony`.

### 4.3 Analysis Results
- **Format**: JSON.
- **Structure**: Array of objects, each representing a metric type and threshold density.

### 4.4 Processing Summary
- **Format**: JSON.
- **Structure**: Object containing `target_subjects`, `processed_subjects`, `skipped_subjects`, `proportion`, `status`, `reason`.

## 5. Constraints & Validation

- **Dimension Mismatch**: If SC and FC matrices do not have the same dimensions (400x400), the pipeline halts.
- **Missing Values**: Matrices must not contain NaN values.
- **Symmetry**: Functional matrices must be symmetric. Structural matrices may be asymmetric (streamline count) but are treated as symmetric for centrality calculations.
- **Range**: Centrality metrics must be non-negative. Synchrony must be between 0 and 1.
