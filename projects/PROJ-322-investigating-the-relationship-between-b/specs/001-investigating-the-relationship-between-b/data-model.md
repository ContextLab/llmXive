# Data Model: Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury

## Entity Relationship Overview

The data model defines the flow from raw imaging data to statistical results.

1.  **Subject**: The atomic unit of analysis. Contains metadata (ID, Time Point, Cognitive Score).
2.  **ConnectivityMatrix**: Derived from raw fMRI. A square matrix (N x N) representing correlations between ROIs.
3.  **GraphMetrics**: Scalar values derived from the matrix (Global Efficiency, Local Efficiency, Modularity).
4.  **AnalysisResult**: Aggregated statistical output (Coefficients, P-values, Confidence Intervals).

## Data Flow Diagram (Logical)

```mermaid
graph TD
    A[Raw fMRI NIfTI] -->|Preprocessing (nilearn)| B[Time Series]
    B -->|AAL Parcellation| C[Connectivity Matrix]
    C -->|Sparsity Threshold| D[Thresholded Matrix]
    D -->|NetworkX| E[Graph Metrics]
    F[Clinical Scores] -->|Merge| E
    E -->|LMM / Permutation / PCA| G[Analysis Result]
```

## Schema Definitions

### 1. Subject Metadata
*   **Source**: Derived from dataset manifest or synthetic generation.
*   **Format**: CSV or JSON.
*   **Fields**:
    *   `subject_id`: String (Unique ID).
    *   `time_point`: Enum ("acute", "chronic").
    *   `cognitive_score`: Float (e.g., PCS score).
    *   `status`: Enum ("included", "excluded_missing_timepoint", "excluded_aal_fail").

### 2. Connectivity Matrix (Intermediate)
*   **Source**: `code/preprocessing.py`.
*   **Format**: `.npy` (NumPy array) or dense CSV.
*   **Fields**:
    *   `subject_id`: String.
    *   `time_point`: String.
    *   `matrix_data`: Array of floats (flattened upper triangle or full NxN).
    *   `roi_count`: Integer (Default 90 for AAL).

### 3. Graph Metrics (Final Input for Model)
*   **Source**: `code/graph_metrics.py`.
*   **Format**: CSV.
*   **Fields**:
    *   `subject_id`: String.
    *   `time_point`: String.
    *   `global_efficiency`: Float.
    *   `local_efficiency`: Float.
    *   `modularity_q`: Float.
    *   `sparsity_threshold`: Float (e.g., 0.15).
    *   `vif_global`: Float (Variance Inflation Factor for Global Efficiency).
    *   `vif_local`: Float (Variance Inflation Factor for Local Efficiency).
    *   `vif_modularity`: Float (Variance Inflation Factor for Modularity).
    *   `pc1_value`: Float (Principal Component 1 value, if VIF > 5).

### 4. Analysis Result
*   **Source**: `code/statistical_model.py`.
*   **Format**: JSON.
*   **Fields**:
    *   `model_type`: String ("LinearMixedLM").
    *   `fixed_effects`: Object (Map of predictor -> {beta, std_err, p_value, conf_int}).
    *   `random_effects`: Object (Variance components).
    *   `permutation_p_value`: Float.
    *   `convergence_status`: Boolean.
    *   `vif_flags`: Object (Map of predictor -> VIF value).
    *   `collinearity_mitigation`: String ("PCA", "Ridge", "None", "Descriptive").
    *   `limitations`: Array of Strings (e.g., "n < 20", "Missing PCS scores", "Synthetic Data").
    *   `independent_metric_status`: Enum ("validated", "missing", "skipped").
    *   `is_synthetic`: Boolean (True if data was generated for validation).

## Data Constraints & Validation

*   **Memory Limit**: No single matrix or batch of matrices shall exceed 6GB.
*   **Sparsity**: All matrices used for graph calculation must be thresholded to a low level of sparsity.
*   **Missing Data**: Subjects with only one time point are excluded from the longitudinal model but logged.
*   **Collinearity**: If VIF > 5 for any predictor, the result must flag "COLLINEARITY_DETECTED" and report descriptive statistics or PCA results only.
*   **Data Gap**: If cognitive scores are missing, the `is_synthetic` flag must be set to `true` and the `limitations` array must include "Missing cognitive scores; validation mode only".
