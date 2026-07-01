# Data Model: Reproduce & Validate Arbor

## 1. Overview

This document defines the data structures for the Arbor reproduction project. The primary data artifacts are the **Hypothesis Tree** (`tree.json`), the **Benchmark Results** (`eval_results.json`), and the **Human-Readable Report** (`summary.md`).

## 2. Entity Definitions

### 2.1. Hypothesis Tree (`tree.json`)

The tree is a directed acyclic graph (DAG) where nodes represent state in the research process.

#### Node Types
1.  **Root**: The initial task definition.
2.  **Hypothesis**: A proposed code change or research direction.
3.  **Evidence**: The output (stdout, metrics, logs) of executing a hypothesis.
4.  **Artifact**: A generated file or model checkpoint.
5.  **Distillation**: A synthesized insight node combining multiple evidence nodes.

#### Relationships
- **Parent-Child**: A `Hypothesis` node is a child of a `Root` or `Distillation` node.
- **Evidence Link**: An `Evidence` node is a child of the `Hypothesis` it tested.
- **Artifact Link**: An `Artifact` node is a child of the `Evidence` that generated it.
- **Log Link**: Each `Evidence` node MUST contain a `log_file_path` pointing to a log file (`logs/<node_id>.log`) containing the execution output (FR-004).

### 2.2. Benchmark Results (`eval_results.json`)

Contains the final metrics, resource usage, and comparison data.

## 3. Schema Definitions

### 3.1. Tree Node Schema

```yaml
type: object
properties:
  id:
    type: string
    description: "Unique identifier for the node (UUID)."
  type:
    type: string
    enum: ["Root", "Hypothesis", "Evidence", "Artifact", "Distillation"]
    description: "The type of node."
  status:
    type: string
    enum: ["Pending", "Running", "Success", "Failed", "Timeout"]
    description: "Current execution status."
  content:
    type: object
    description: "Payload specific to the node type (e.g., hypothesis text, log output)."
  parent_id:
    type: string
    nullable: true
    description: "ID of the parent node. Null for Root."
  created_at:
    type: string
    format: date-time
    description: "ISO 8601 timestamp of creation."
  metrics:
    type: object
    nullable: true
    description: "Optional metrics (e.g., accuracy) if applicable."
  log_file_path:
    type: string
    nullable: true
    description: "Relative path to the log file for this node (e.g., 'logs/<id>.log'). Required for Evidence nodes to satisfy FR-004."
required:
  - id
  - type
  - status
  - created_at
```

### 3.2. Benchmark Result Schema

```yaml
type: object
properties:
  task_name:
    type: string
    description: "Name of the task (e.g., 'algotune_knn')."
  baseline_score:
    type: number
    description: "The score achieved by the baseline method (e.g., Random Search)."
  achieved_score:
    type: number
    description: "The score achieved by the Arbor system."
  improvement_percentage:
    type: number
    description: "Calculated improvement: ((achieved - baseline) / baseline) * 100."
  baseline_method:
    type: string
    description: "The method used for the baseline (e.g., 'Random Search', 'Standard KNN')."
  baseline_seed:
    type: integer
    description: "The random seed used for the baseline run to ensure reproducibility."
  execution_time_seconds:
    type: number
    description: "Total runtime of the benchmark."
  peak_memory_mb:
    type: number
    description: "Peak memory usage in MB (measured via memory_profiler)."
  hypothesis_count:
    type: integer
    description: "Number of hypotheses tested."
  tree_depth:
    type: integer
    description: "Maximum depth of the generated tree."
  status:
    type: string
    enum: ["Success", "Partial", "Failed"]
    description: "Overall execution status."
required:
  - task_name
  - baseline_score
  - achieved_score
  - execution_time_seconds
  - peak_memory_mb
  - baseline_method
  - baseline_seed
  - status
```

### 3.3. Report Template (`summary.md`)

The `summary.md` file must be generated from `eval_results.json` and contain:
- Task Name
- Baseline Method & Score
- Achieved Score
- Improvement Percentage
- Resource Usage (Peak Memory, Total Time)
- Tree Statistics (Depth, Node Count)
- Link to `tree.json` and `eval_results.json`