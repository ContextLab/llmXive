# Data Model: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## 1. Entity Definitions

### 1.1 Subject
Represents a single participant in the HCP cohort.
*   **Fields**:
    *   `subject_id`: Unique string identifier (e.g., "100101").
    *   `structural_matrix`: 200x200 numpy array (or list of lists) representing connectivity weights.
    *   `fMRI_timeseries`: 200xT numpy array (T = number of time points).
    *   `exclusion_reason`: String or null (e.g., "sparsity >90%", "k-means non-convergence").

### 1.2 StructuralMetric
Derived graph properties for a single subject.
*   **Fields**:
    *   `subject_id`: Foreign key to Subject.
    *   `global_efficiency`: Float.
    *   `average_clustering`: Float.
    *   `modularity`: Float.
    *   `threshold_density`: Float (e.g., 0.15).

### 1.3 DynamicMetric
Derived state properties for a single subject, calculated using **Leave-One-Out (LOO)** clustering.
*   **Fields**:
    *   `subject_id`: Foreign key to Subject.
    *   `window_length_tr`: Integer (30 or 20).
    *   `number_of_visited_states`: Integer.
    *   `mean_dwell_time_state_1`: Float.
    *   `mean_dwell_time_state_2`: Float.
    *   `mean_dwell_time_state_3`: Float.
    *   `mean_dwell_time_state_4`: Float.
    *   `mean_dwell_time_state_5`: Float.
    *   `state_switching_rate`: Float (optional derived metric).
    *   `loo_derived`: Boolean (Always `true`, indicating metrics were derived from N-1 subjects).

### 1.4 CorrelationResult
Statistical association between a structural and dynamic metric.
*   **Fields**:
    *   `structural_metric_name`: String (e.g., "global_efficiency").
    *   `dynamic_metric_name`: String (e.g., "mean_dwell_time_state_1").
    *   `correlation_coefficient`: Float (r).
    *   `p_value`: Float.
    *   `fdr_corrected_p_value`: Float.
    *   `is_significant`: Boolean (FDR corrected p < 0.05).
    *   `method`: String ("Pearson" or "Spearman").
    *   `window_length_tr`: Integer (30 or 20).
    *   `causal_claim`: Boolean (Always `false`).

## 2. Data Flow

1.  **Input**: Raw HCP NIfTI files (Verified Sources).
2.  **Preprocessing**:
    *   Filter for valid subjects.
    *   Compute Structural Metrics (NetworkX, fixed 15% threshold).
    *   Compute Dynamic Metrics (Sliding Window + **LOO K-Means**).
3.  **Aggregation**: Merge Structural and Dynamic metrics into a single `metrics.csv`.
4.  **Analysis**:
    *   Test normality.
    *   Compute correlations.
    *   Apply FDR.
5.  **Output**: `correlation_results.csv`, `robustness_report.json`, `final_report.md`.

## 3. Constraints & Validation

*   **Sparsity**: If structural matrix sparsity > 90%, exclude subject.
*   **Convergence**: If k-means fails to converge, exclude subject.
*   **Normality**: Use Shapiro-Wilk; switch to Spearman if p < 0.05.
*   **Associational**: All outputs must include a metadata flag `causal_claim: false`.
*   **LOO Independence**: All dynamic metrics must be derived using the LOO protocol to ensure statistical independence.
* **Threshold Robustness**: Structural metrics must be calculated at [deferred], [deferred], and [deferred] density to validate robustness.