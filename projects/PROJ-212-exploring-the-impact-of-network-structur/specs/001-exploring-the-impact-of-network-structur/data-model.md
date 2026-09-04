# Data Model: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## 1. Entities and Relationships

### 1.1 NetworkGraph
Represents a single network instance.
*   **Attributes**:
    *   `network_id` (str): Unique identifier (e.g., filename or hash).
    *   `node_count` (int): Number of nodes (N).
    *   `edge_count` (int): Number of edges.
    *   `topology_metrics` (dict): Contains `degree_mean`, `degree_std`, `clustering_coeff`, `avg_path_length`.
    *   `is_connected` (bool): Flag for connectivity.
    *   `adjacency_matrix` (np.array): Optional, for simulation input.

### 1.2 SimulationResult
Represents the outcome of a Kuramoto run on a specific network.
*   **Attributes**:
    *   `network_id` (str): Foreign key to `NetworkGraph`.
    *   `coupling_strength` (float): The $K$ value tested.
    *   `order_parameter_series` (list[float]): Time series of $r(t)$.
    *   `synchronization_threshold` (float): The calculated $K_c$ (min $K$ for $r>0.8$).
    *   `convergence_time` (float): Time step where threshold was reached.
    *   `status` (str): "synchronized", "failed", "disconnected".

### 1.3 RegressionModel
Represents the statistical fit.
*   **Attributes**:
    *   `model_id` (str): Unique ID.
    *   `predictors` (list[str]): List of topological features used.
    *   `target` (str): "synchronization_threshold".
    *   `coefficients` (dict): Feature name -> coefficient value.
    *   `r_squared` (float): $R^2$ score.
    *   `p_values` (dict): Feature name -> p-value.
    *   `cv_score` (float): Mean cross-validation $R^2$.
    *   `cv_std` (float): Standard deviation of CV scores.
    *   `vif_scores` (dict): Feature name -> VIF value.

## 2. Data Flow

1.  **Input**: Raw Graph Files (`.mtx`, `.csv`, or Parquet edge lists).
2.  **Processing**:
    *   `loader.py` -> `NetworkGraph` objects.
    *   `topology.py` -> `topology_metrics` added to `NetworkGraph`.
    *   `simulation.py` -> `SimulationResult` objects generated for each network.
3.  **Aggregation**:
    *   All `SimulationResult` objects merged into a single `DataFrame` (`results.csv`).
    *   Features (`topology_metrics`) joined with `synchronization_threshold`.
4.  **Analysis**:
    *   `stats.py` -> `RegressionModel` objects generated.
5.  **Output**:
    *   `results/metrics.json` (Topological stats).
    *   `results/simulation_results.json` (Thresholds).
    *   `results/regression_summary.json` (Model stats).
    *   `results/heatmap.png` (Visualization).

## 3. Constraints and Validation
*   **Disconnected Graphs**: `avg_path_length` MUST be `null` or `inf` if `is_connected` is False.
*   **Threshold Logic**: `synchronization_threshold` MUST be `null` if the graph is disconnected (no global sync possible).
*   **Data Types**: All floating point values stored with 6 decimal precision.
