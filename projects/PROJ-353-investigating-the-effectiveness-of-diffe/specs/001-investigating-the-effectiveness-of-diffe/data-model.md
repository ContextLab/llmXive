# Data Model: Investigating the Effectiveness of Loss Functions on Small-World Graphs

## Entity Definitions

### SyntheticGraph
Represents a single generated Watts-Strogatz graph with annotated community labels.

| Field | Type | Description |
|-------|------|-------------|
| `graph_id` | string | Unique identifier (e.g., "graph_001"). |
| `rewiring_probability_beta` | float | The $\beta$ parameter used for generation (0.0 to 1.0). |
| `node_count` | int | Total number of nodes (fixed at a constant value). |
| `k_neighbors` | int | Initial number of neighbors per node (fixed at a constant value). |
| `clustering_coefficient` | float | Global clustering coefficient of the graph. |
| `avg_path_length` | float | Average shortest path length. |
| `community_labels` | list[int] | Community ID for each node (0-indexed). |
| `adjacency_matrix` | list[list[int]] | Sparse or dense adjacency matrix (stored as list of lists or edge list). |
| `seed` | int | Random seed used for generation. |

### TrainingRun
Represents a single training execution of a GCN on a specific graph with a specific loss function.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique identifier (e.g., "run_graph_001_loss_ce"). |
| `graph_id` | string | Reference to `SyntheticGraph.graph_id`. |
| `loss_type` | string | "cross_entropy" or "info_nce". |
| `convergence_epoch` | int or null | Epoch number where accuracy $\ge$ 0.90. `null` if censored. |
| `is_censored` | boolean | `true` if `convergence_epoch` is `null` (did not converge). |
| `final_accuracy` | float | Accuracy at the last epoch (or at convergence). |
| `accuracy_epoch_100` | float | Accuracy at epoch 100. |
| `accuracy_epoch_500` | float | Accuracy at epoch 500. |
| `total_epochs` | int | Total epochs run (usually `MAX_EPOCHS` or convergence epoch). |
| `loss_curve` | list[float] | Average loss per epoch (optional, for debugging). |
| `training_seed` | int | Random seed for the training run. |

### AnalysisResult
The final output of the statistical analysis.

| Field | Type | Description |
|-------|------|-------------|
| `tobit_interaction_p_value` | float | P-value for the interaction term in the Tobit model. |
| `cox_interaction_p_value` | float | P-value for the interaction term in the Cox model. |
| `cox_ph_valid` | boolean | `true` if Schoenfeld test passed (PH assumption holds). |
| `is_significant` | boolean | `true` if (Tobit p < 0.05) OR (Cox p < 0.05 AND Cox is valid). |
| `tobit_coefficients` | dict | Full coefficient dictionary from Tobit model. |
| `cox_coefficients` | dict | Full coefficient dictionary from Cox model. |
| `fixed_epoch_results` | dict | P-values for interaction terms at fixed epochs (100, 500). |
| `generated_at` | string | ISO 8601 timestamp. |

## Relationships

- **SyntheticGraph** (1) --< **TrainingRun** (Many): One graph is trained with two loss functions.
- **TrainingRun** (Many) --< **AnalysisResult** (1): All runs are aggregated into one result.

## Constraints

- `rewiring_probability_beta` must be in $[0.0, 1.0]$.
- `convergence_epoch` must be $\le$ `MAX_EPOCHS` (1000) if not censored.
- `community_labels` must contain exactly `node_count` integers.