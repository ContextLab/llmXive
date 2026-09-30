# Data Model Specification
# Project: Investigating the Effectiveness of Contrastive Loss on Small-World Graphs
# Version: 1.0.0
# Schema Draft: JSON Schema Draft 7

## Overview
This document defines the data entities used throughout the research pipeline.
It serves as the source of truth for `contracts/*.schema.yaml` and data validation logic.

## 1. SyntheticGraph
Represents a single generated Watts-Strogatz graph with topology annotations.
Corresponds to User Story 1 (US1) and FR-001.

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `id` | string | Unique identifier for the graph instance. | UUID v4 or `graph_{beta}_{index}` |
| `beta` | float | Rewiring probability parameter ($\beta$). | $0.0 \le \beta \le 1.0$ |
| `seed` | integer | Random seed used for generation. | > 0 |
| `n_nodes` | integer | Number of nodes in the graph. | Fixed at 110 (FR-001) |
| `k` | integer | Each node is connected to $k$ nearest neighbors in the ring lattice. | Default: 6 |
| `clustering_coefficient` | float | Global clustering coefficient. | $0.0 \le C \le 1.0$ |
| `average_path_length` | float | Average shortest path length. | > 0 |
| `is_connected` | boolean | Whether the graph is a single connected component. | Must be `true` for valid runs |
| `edge_list` | array | List of edges represented as `[source, target]` pairs. | Integer indices |
| `labels` | array | Community labels derived from the initial lattice. | Integer class IDs |

### JSON Schema Draft 7 Example
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "$id": "synthetic_graph",
 "type": "object",
 "properties": {
 "id": { "type": "string", "pattern": "graph_[0-9.]+_[0-9]+" },
 "beta": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "seed": { "type": "integer", "minimum": 1 },
 "n_nodes": { "type": "integer", "const": 110 },
 "k": { "type": "integer", "default": 6 },
 "clustering_coefficient": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "average_path_length": { "type": "number", "minimum": 1.0 },
 "is_connected": { "type": "boolean", "const": true },
 "edge_list": {
 "type": "array",
 "items": {
 "type": "array",
 "items": { "type": "integer" },
 "minItems": 2,
 "maxItems": 2
 }
 },
 "labels": {
 "type": "array",
 "items": { "type": "integer" },
 "minItems": 110,
 "maxItems": 110
 }
 },
 "required": ["id", "beta", "seed", "n_nodes", "clustering_coefficient", "edge_list", "labels", "is_connected"]
}
```

## 2. TrainingRun
Represents the execution of a GCN model on a specific graph with a specific loss function.
Corresponds to User Story 2 (US2) and FR-005.

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `run_id` | string | Unique identifier for the training run. | `training_run_{graph_id}_{loss_type}` |
| `graph_id` | string | Reference to the `SyntheticGraph.id`. | Foreign Key |
| `loss_type` | string | Type of loss function used. | Enum: `["cross_entropy", "infonce"]` |
| `epochs_trained` | integer | Total number of epochs executed. | $\le$ `MAX_EPOCHS` (1000) |
| `steps_to_convergence` | integer | Epoch index where accuracy $\ge$ `CONVERGENCE_THRESHOLD`. | Null if censored |
| `convergence_status` | string | Status of the training run. | Enum: `["converged", "censored"]` |
| `final_accuracy` | float | Accuracy at the final epoch. | $0.0 \le A \le 1.0$ |
| `final_loss` | float | Loss at the final epoch. | $\ge 0.0$ |
| `trajectory` | array | Per-epoch metrics history. | List of objects |
| `hyperparameters` | object | Configuration used for this run. | LR, batch size, etc. |

### JSON Schema Draft 7 Example
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "$id": "training_run",
 "type": "object",
 "properties": {
 "run_id": { "type": "string" },
 "graph_id": { "type": "string" },
 "loss_type": { "type": "string", "enum": ["cross_entropy", "infonce"] },
 "epochs_trained": { "type": "integer", "minimum": 1 },
 "steps_to_convergence": { "type": ["integer", "null"] },
 "convergence_status": { "type": "string", "enum": ["converged", "censored"] },
 "final_accuracy": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "final_loss": { "type": "number", "minimum": 0.0 },
 "trajectory": {
 "type": "array",
 "items": {
 "type": "object",
 "properties": {
 "epoch": { "type": "integer" },
 "loss": { "type": "number" },
 "accuracy": { "type": "number" }
 },
 "required": ["epoch", "loss", "accuracy"]
 }
 },
 "hyperparameters": { "type": "object" }
 },
 "required": ["run_id", "graph_id", "loss_type", "epochs_trained", "convergence_status", "trajectory"]
}
```

## 3. AnalysisResult
Represents the statistical outcome of comparing loss functions across graph topologies.
Corresponds to User Story 3 (US3) and SC-003.

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `analysis_id` | string | Unique identifier for the analysis batch. | Timestamp or UUID |
| `tobit_model` | object | Results from Tobit Regression. | Contains coefficients, p-values |
| `cox_model` | object | Results from Cox Proportional Hazards. | Contains Hazard Ratios, p-values |
| `interaction_pvalue_tobit` | float | P-value for the $\beta \times$ Loss interaction term (Tobit). | $0.0 \le p \le 1.0$ |
| `interaction_pvalue_cox` | float | P-value for the $\beta \times$ Loss interaction term (Cox). | $0.0 \le p \le 1.0$ |
| `pvalue_corrected_tobit` | float | Bonferroni corrected p-value (Tobit). | Calculated as $p \times 2$ |
| `pvalue_corrected_cox` | float | Bonferroni corrected p-value (Cox). | Calculated as $p \times 2$ |
| `is_significant` | boolean | Whether the interaction is significant after correction. | True if $\min(p_{corr}) < 0.05$ |
| `sample_size` | integer | Number of training runs analyzed. | Expected: 220 (110 graphs $\times$ 2 losses) |

### JSON Schema Draft 7 Example
```json
{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "$id": "analysis_result",
 "type": "object",
 "properties": {
 "analysis_id": { "type": "string" },
 "sample_size": { "type": "integer", "minimum": 1 },
 "tobit_model": {
 "type": "object",
 "properties": {
 "coefficients": { "type": "object" },
 "p_values": { "type": "object" }
 }
 },
 "cox_model": {
 "type": "object",
 "properties": {
 "hazard_ratios": { "type": "object" },
 "p_values": { "type": "object" }
 }
 },
 "interaction_pvalue_tobit": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "interaction_pvalue_cox": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "pvalue_corrected_tobit": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "pvalue_corrected_cox": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
 "is_significant": { "type": "boolean" }
 },
 "required": ["analysis_id", "sample_size", "interaction_pvalue_tobit", "interaction_pvalue_cox", "pvalue_corrected_tobit", "pvalue_corrected_cox", "is_significant"]
}
```