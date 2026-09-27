# Data Model Specification

This document defines the data entities, attributes, and schemas used in the `llmXive` project investigating the effectiveness of different loss functions on small-world graphs.

The model is based on the requirements derived from `specs/001-investigating-loss-functions-small-world/`, specifically FR-001 (Graph Generation), FR-005 (Training Convergence), and SC-003 (Statistical Analysis).

## Entity Definitions

### 1. SyntheticGraph

Represents a generated Watts-Strogatz graph with annotated community labels.
Corresponds to FR-001.

| Attribute | Type | Description |
|:--- |:--- |:--- |
| `graph_id` | string | Unique identifier for the graph instance (UUID). |
| `beta` | float | Rewiring probability parameter $\beta \in [0.0, 1.0]$. |
| `k` | int | Average degree (number of neighbors in the initial ring lattice). |
| `n` | int | Total number of nodes (fixed at 110 per Spec FR-001). |
| `seed` | int | Random seed used for generation to ensure reproducibility. |
| `clustering_coeff` | float | Measured global clustering coefficient of the generated graph. |
| `avg_path_length` | float | Measured average shortest path length. |
| `edge_list` | list of list of int | List of edges represented as `[source_node, target_node]`. |
| `labels` | list of int | Community labels for each node, derived from the initial lattice before rewiring. |
| `is_connected` | boolean | Flag indicating if the graph is fully connected. |

### 2. TrainingRun

Represents a single training execution of a GCN model on a specific graph with a specific loss function.
Corresponds to FR-005.

| Attribute | Type | Description |
|:--- |:--- |:--- |
| `run_id` | string | Unique identifier for the training run. |
| `graph_id` | string | Foreign key reference to `SyntheticGraph.graph_id`. |
| `loss_type` | string | Type of loss used: `"cross_entropy"` or `"info_nce"`. |
| `model_arch` | string | Architecture used (e.g., `"GCN2Layer"`). |
| `epochs_trained` | int | Total number of epochs the model was trained. |
| `steps_to_convergence` | int | Number of epochs until accuracy $\ge$ `CONVERGENCE_THRESHOLD` (0.90). |
| `convergence_status` | string | Status: `"converged"` or `"censored"` (if max epochs reached without convergence). |
| `trajectory` | list of object | Per-epoch metrics. Each object contains `{epoch: int, loss: float, accuracy: float}`. |
| `final_accuracy` | float | Accuracy at the final epoch. |
| `seed` | int | Random seed used for this specific training run. |

### 3. AnalysisResult

Represents the outcome of the statistical analysis (Tobit Regression and Cox PH) performed on the collection of `TrainingRun` entities.
Corresponds to SC-003.

| Attribute | Type | Description |
|:--- |:--- |:--- |
| `analysis_id` | string | Unique identifier for the analysis run. |
| `tobit_p_value` | float | P-value for the interaction term in Tobit Regression. |
| `tobit_coefficient` | float | Coefficient of the interaction term (Loss Type $\times$ Beta). |
| `cox_p_value` | float | P-value for the interaction term in Cox Proportional Hazards. |
| `cox_hazard_ratio` | float | Hazard Ratio for the interaction term. |
| `is_significant` | boolean | `true` if the Bonferroni-corrected p-value < 0.05. |
| `correction_method` | string | Method used for multiple comparison correction (e.g., `"bonferroni"`). |
| `sample_size` | int | Number of runs included in the analysis. |

## JSON Schema Examples (Draft 7)

### SyntheticGraph Schema Example

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "SyntheticGraph",
 "type": "object",
 "required": ["graph_id", "beta", "n", "seed", "clustering_coeff", "edge_list", "labels"],
 "properties": {
 "graph_id": { "type": "string", "format": "uuid" },
 "beta": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "k": { "type": "integer", "minimum": 2 },
 "n": { "type": "integer", "const": 110 },
 "seed": { "type": "integer" },
 "clustering_coeff": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "avg_path_length": { "type": "number" },
 "edge_list": {
 "type": "array",
 "items": {
 "type": "array",
 "minItems": 2,
 "maxItems": 2,
 "items": { "type": "integer" }
 }
 },
 "labels": {
 "type": "array",
 "items": { "type": "integer" }
 },
 "is_connected": { "type": "boolean" }
 }
}
```

### TrainingRun Schema Example

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "TrainingRun",
 "type": "object",
 "required": ["run_id", "graph_id", "loss_type", "epochs_trained", "trajectory", "convergence_status"],
 "properties": {
 "run_id": { "type": "string", "format": "uuid" },
 "graph_id": { "type": "string", "format": "uuid" },
 "loss_type": { "type": "string", "enum": ["cross_entropy", "info_nce"] },
 "model_arch": { "type": "string" },
 "epochs_trained": { "type": "integer", "minimum": 1 },
 "steps_to_convergence": { "type": ["integer", "null"] },
 "convergence_status": { "type": "string", "enum": ["converged", "censored"] },
 "trajectory": {
 "type": "array",
 "items": {
 "type": "object",
 "required": ["epoch", "loss", "accuracy"],
 "properties": {
 "epoch": { "type": "integer" },
 "loss": { "type": "number" },
 "accuracy": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
 }
 }
 },
 "final_accuracy": { "type": "number" },
 "seed": { "type": "integer" }
 }
}
```

### AnalysisResult Schema Example

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "AnalysisResult",
 "type": "object",
 "required": ["analysis_id", "tobit_p_value", "cox_p_value", "is_significant", "sample_size"],
 "properties": {
 "analysis_id": { "type": "string", "format": "uuid" },
 "tobit_p_value": { "type": "number" },
 "tobit_coefficient": { "type": "number" },
 "cox_p_value": { "type": "number" },
 "cox_hazard_ratio": { "type": "number" },
 "is_significant": { "type": "boolean" },
 "correction_method": { "type": "string" },
 "sample_size": { "type": "integer", "minimum": 1 }
 }
}
```