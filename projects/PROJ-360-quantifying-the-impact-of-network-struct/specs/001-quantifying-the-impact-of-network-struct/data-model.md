# Data Model: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

## 1. Entities

### MaterialRecord
Represents a single crystalline material.
*   `material_id` (string): Unique identifier from Materials Project.
*   `cif_path` (string): Relative path to the raw CIF file.
*   `thermal_conductivity_tensor` (list of 3 floats): $[k_x, k_y, k_z]$.
*   `scalar_k` (float): Arithmetic mean of the tensor.
*   `unit_cell_volume` (float): Volume in Å³.
*   `atom_count` (integer): Total number of atoms.
*   `mean_atomic_mass` (float): Average atomic mass of elements.
*   `skip_reason` (string or null): Reason for skipping (e.g., "No bonds", "Missing data").

### NetworkGraph
Represents the atomic network derived from a material.
*   `material_id` (string): Foreign key to MaterialRecord.
*   `node_count` (integer): Number of atoms.
*   `edge_count` (integer): Number of bonds.
*   `average_degree` (float): Mean degree of nodes.
*   `average_path_length` (float or null): Mean shortest path on LCC. (Imputed if disconnected, else null).
*   `clustering_coefficient` (float): Global clustering coefficient.
*   `is_connected` (boolean): True if the graph is fully connected.

### CorrelationResult
Result of statistical analysis.
*   `metric_name` (string): Name of the network metric.
*   `correlation_coefficient` (float): Pearson or Spearman r.
*   `p_value` (float): Raw p-value.
*   `bonferroni_adjusted_p` (float): Adjusted p-value.
*   `significance_flag` (boolean): True if adjusted p < 0.05.
*   `vif_value` (float or null): VIF if used in regression.

## 2. Data Flow

1.  **Raw Input**: CIF files from Materials Project.
2.  **Intermediate**: `networks/` (pickle files of `NetworkGraph` objects).
3.  **Aggregated**: `data/processed/metrics.csv` (flattened `NetworkGraph` attributes + `scalar_k` + physical descriptors).
4.  **Final Output**: `results/correlations.json`, `results/model_performance.json`, `results/final_report.md`.

## 3. Constraints

*   **Immutability**: Raw CIFs in `data/raw/cif/` are never modified.
*   **Determinism**: All random seeds (for CV splits) are fixed in code.
*   **Completeness**: All materials in the final `metrics.csv` must have a valid `material_id`.
*   **Missing Data Handling**: `average_path_length` is imputed with median of connected components if disconnected and $n_{connected} > 5$; otherwise marked as null.