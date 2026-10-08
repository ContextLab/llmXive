# Data Model

This document defines the core data entities for the `PROJ-353-investigating-the-effectiveness-of-diffe` project.
It includes Markdown tables describing the entities and JSON Schema Draft 7 examples for validation.

## Entities

### 1. SyntheticGraph

Represents a generated Watts-Strogatz graph with associated metadata.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `id` | string | Unique identifier for the graph instance. | UUID or sequential ID. |
| `beta` | number | Rewiring probability $\beta$. | Range: [0.0, 1.0]. |
| `seed` | integer | Random seed used for generation. | Positive integer. |
| `node_count` | integer | Total number of nodes in the graph. | Fixed at 110 (per FR-001). |
| `edge_list` | array of arrays | List of edges `[[u, v],...]`. | Undirected, no self-loops. |
| `labels` | array of integers | Community labels derived from initial lattice. | Values: 0 to K-1. |
| `clustering_coeff` | number | Global clustering coefficient (transitivity). | Range: [0.0, 1.0]. |
| `is_connected` | boolean | Connectivity status. | Must be `true` for valid graphs. |

**JSON Schema Example:**

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "SyntheticGraph",
 "type": "object",
 "required": ["id", "beta", "seed", "node_count", "edge_list", "labels", "clustering_coeff", "is_connected"],
 "properties": {
 "id": {
 "type": "string",
 "description": "Unique identifier for the graph instance."
 },
 "beta": {
 "type": "number",
 "minimum": 0.0,
 "maximum": 1.0,
 "description": "Rewiring probability beta."
 },
 "seed": {
 "type": "integer",
 "minimum": 0,
 "description": "Random seed used for generation."
 },
 "node_count": {
 "type": "integer",
 "description": "Total number of nodes in the graph."
 },
 "edge_list": {
 "type": "array",
 "items": {
 "type": "array",
 "items": { "type": "integer" },
 "minItems": 2,
 "maxItems": 2
 },
 "description": "List of edges [u, v]."
 },
 "labels": {
 "type": "array",
 "items": { "type": "integer" },
 "description": "Community labels derived from initial lattice."
 },
 "clustering_coeff": {
 "type": "number",
 "minimum": 0.0,
 "maximum": 1.0,
 "description": "Global clustering coefficient."
 },
 "is_connected": {
 "type": "boolean",
 "description": "Connectivity status."
 }
 }
}
```

---

### 2. TrainingRun

Represents a single training execution of a GCN model on a specific graph with a specific loss function.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `run_id` | string | Unique identifier for the training run. | UUID. |
| `graph_id` | string | Reference to the `SyntheticGraph.id`. | Foreign key. |
| `loss_type` | string | Type of loss function used. | Enum: `"ce"`, `"infonce"`. |
| `beta` | number | Rewiring probability of the source graph. | Propagated from graph. |
| `node_count` | integer | Number of nodes in the source graph. | Propagated from graph. |
| `convergence_status` | string | Status of convergence. | Enum: `"converged"`, `"censored"`. |
| `steps_to_convergence` | integer | Epochs until accuracy $\ge$ threshold. | Null if censored. |
| `final_accuracy` | number | Accuracy at the last epoch. | Range: [0.0, 1.0]. |
| `trajectory` | array | Per-epoch metrics history. | List of objects. |
| `trajectory[].epoch` | integer | Epoch index. | 1-based. |
| `trajectory[].loss` | number | Loss value at epoch. | Non-negative. |
| `trajectory[].accuracy` | number | Accuracy at epoch. | Range: [0.0, 1.0]. |

**JSON Schema Example:**

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "TrainingRun",
 "type": "object",
 "required": ["run_id", "graph_id", "loss_type", "beta", "node_count", "convergence_status", "final_accuracy", "trajectory"],
 "properties": {
 "run_id": {
 "type": "string",
 "description": "Unique identifier for the training run."
 },
 "graph_id": {
 "type": "string",
 "description": "Reference to the SyntheticGraph.id."
 },
 "loss_type": {
 "type": "string",
 "enum": ["ce", "infonce"],
 "description": "Type of loss function used."
 },
 "beta": {
 "type": "number",
 "description": "Rewiring probability of the source graph."
 },
 "node_count": {
 "type": "integer",
 "description": "Number of nodes in the source graph."
 },
 "convergence_status": {
 "type": "string",
 "enum": ["converged", "censored"],
 "description": "Status of convergence."
 },
 "steps_to_convergence": {
 "type": ["integer", "null"],
 "description": "Epochs until accuracy >= threshold. Null if censored."
 },
 "final_accuracy": {
 "type": "number",
 "minimum": 0.0,
 "maximum": 1.0,
 "description": "Accuracy at the last epoch."
 },
 "trajectory": {
 "type": "array",
 "items": {
 "type": "object",
 "required": ["epoch", "loss", "accuracy"],
 "properties": {
 "epoch": { "type": "integer" },
 "loss": { "type": "number" },
 "accuracy": { "type": "number" }
 }
 },
 "description": "Per-epoch metrics history."
 }
 }
}
```

---

### 3. AnalysisResult

Represents the aggregated statistical analysis results for the interaction between loss type and beta.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `tobit_interaction_p_value` | number | P-value for the interaction term in Tobit model. | Range: [0.0, 1.0]. |
| `cox_interaction_p_value` | number | P-value for the interaction term in Cox PH model. | Range: [0.0, 1.0]. |
| `bonferroni_corrected_p` | number | Minimum of corrected p-values. | Range: [0.0, 1.0]. |
| `is_significant` | boolean | Whether the interaction is significant after correction. | True if p < 0.05. |
| `methodology` | string | Summary of statistical methods used. | "Tobit + Cox PH". |

**JSON Schema Example:**

```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "AnalysisResult",
 "type": "object",
 "required": ["tobit_interaction_p_value", "cox_interaction_p_value", "bonferroni_corrected_p", "is_significant", "methodology"],
 "properties": {
 "tobit_interaction_p_value": {
 "type": "number",
 "minimum": 0.0,
 "maximum": 1.0,
 "description": "P-value for the interaction term in Tobit model."
 },
 "cox_interaction_p_value": {
 "type": "number",
 "minimum": 0.0,
 "maximum": 1.0,
 "description": "P-value for the interaction term in Cox PH model."
 },
 "bonferroni_corrected_p": {
 "type": "number",
 "minimum": 0.0,
 "maximum": 1.0,
 "description": "Minimum of corrected p-values."
 },
 "is_significant": {
 "type": "boolean",
 "description": "Whether the interaction is significant after correction."
 },
 "methodology": {
 "type": "string",
 "description": "Summary of statistical methods used."
 }
 }
}
```