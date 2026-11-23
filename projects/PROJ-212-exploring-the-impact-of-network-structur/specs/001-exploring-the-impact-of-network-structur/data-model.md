# Data Model: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## Entity Definitions

### 1. NetworkGraph
Represents a single network dataset loaded from the raw source.
-   `id` (str): Unique identifier derived from filename (e.g., "snap_graph_001").
-   `source_url` (str): The verified URL from which this file was downloaded.
-   `format` (str): "mtx", "csv", or "edge_list".
-   `node_count` (int): Total number of nodes $N$.
-   `edge_count` (int): Total number of edges $M$.
-   `is_connected` (bool): True if the graph is a single connected component.
-   `largest_component_ratio` (float): Ratio of nodes in the largest component to total nodes.
-   `reduced` (bool): True if the graph was reduced via BFS to N=200.

### 2. TopologicalMetrics
Computed static features for a `NetworkGraph`.
-   `mean_degree` (float): Average degree of the network.
-   `degree_variance` (float): Variance of the degree distribution.
-   `clustering_coefficient` (float): Global clustering coefficient $C$.
-   `average_path_length` (float): Average shortest path length. Set to `null` if disconnected.
-   `is_disconnected` (bool): True if `largest_component_ratio` < 0.9.

### 3. SimulationResult
Outcome of the Kuramoto simulation for a `NetworkGraph`.
-   `network_id` (str): Reference to `NetworkGraph.id`.
-   `coupling_strength_threshold` (float): The minimum $K$ where $r(t) > 0.8$ for $t > 100$. Set to `null` if disconnected. Precision is < 0.001 (bisection search).
-   `integration_time` (float): Total time units simulated.
-   `step_size` (float): RK45 step size used.
-   `order_parameter_final` (float): Final value of $r(t)$.
-   `status` (str): "synchronized", "failed", "disconnected".
-   `warning` (str): Optional warning if N < 200 or other issues.

### 4. RegressionModel
Statistical fit results.
-   `model_type` (str): "linear" or "polynomial".
-   `predictors` (list[str]): List of features used (e.g., ["mean_degree", "clustering_coefficient"]).
-   `coefficients` (dict): Map of predictor -> coefficient.
-   `r_squared` (float): Coefficient of determination.
-   `p_values` (dict): Map of predictor -> p-value.
-   `vif_scores` (dict): Map of predictor -> VIF.
-   `cv_mean_r2` (float): Mean R² from cross-validation.
-   `cv_std_r2` (float): Standard deviation of R².
-   `is_stable` (bool): True if `cv_std_r2` < 0.1.
-   `warning_message` (str): Warning if dataset size is insufficient (N < 10).