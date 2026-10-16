# Data Model: 001-static-dynamic-gap-analysis

## Overview
The pipeline works with four core data artifacts, each validated against a JSON/YAML schema stored under `specs/<identifier>-static-dynamic-gap-analysis/contracts/`. The schemas enable contract‑based testing (`tests/contract/test_contracts.py`) and guarantee reproducibility.

## Schemas

### 1. `static_graph.schema.yaml`
Describes the JSON representation of a Control‑Flow Graph (CFG) or Call Graph (CG) generated for a single patch.

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "StaticGraph"
type: "object"
required:
  - patch_id
  - graph_type
  - nodes
  - edges
properties:
  patch_id:
    type: "string"
    description: "Unique identifier matching the source patch."
  graph_type:
    type: "string"
    enum: ["cfg", "cg"]
    description: "Either 'cfg' for control‑flow or 'cg' for call graph."
  nodes:
    type: "array"
    description: "List of graph nodes."
    items:
      type: "object"
      required: ["id", "label", "attributes"]
      properties:
        id:
          type: "string"
        label:
          type: "string"
        attributes:
          type: "object"
          properties:
            external:
              type: "boolean"
              description: "True if the node represents an external (non‑local) call."
  edges:
    type: "array"
    description: "List of directed edges."
    items:
      type: "object"
      required: ["source", "target"]
      properties:
        source:
          type: "string"
        target:
          type: "string"
        attributes:
          type: "object"
          additionalProperties: true
```

### 2. `feature_vector.schema.yaml`
Defines a single row in `features/static_features.csv`. Updated to include two additional covariates (`patch_size`, `lines_changed`) that capture edit magnitude.

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "FeatureVector"
type: "object"
required:
  - patch_id
  - language
  - node_count
  - edge_count
  - mean_degree
  - max_degree
  - avg_shortest_path
  - recursion_depth
  - external_call_count
  - patch_size
  - lines_changed
  - label
properties:
  patch_id:
    type: "string"
  language:
    type: "string"
    enum: ["python", "cpp"]
  node_count:
    type: "integer"
    minimum: 0
  edge_count:
    type: "integer"
    minimum: 0
  mean_degree:
    type: "number"
  max_degree:
    type: "integer"
    minimum: 0
  avg_shortest_path:
    type: "number"
    minimum: 0
  recursion_depth:
    type: "integer"
    minimum: 0
  external_call_count:
    type: "integer"
    minimum: 0
  patch_size:
    type: "integer"
    minimum: 0
    description: "Size of the raw patch file in bytes."
  lines_changed:
    type: "integer"
    minimum: 0
    description: "Total number of added plus deleted lines in the diff."
  label:
    type: "string"
    enum: ["pass", "fail"]
```

## Data Flow Diagram (textual)

```
Raw Datasets (parquet / jsonl)
   │
   └─► ingest.py ──► patches.csv (patch_id, language, source_code, label)
            │
            ├─► graph_extractor.py ──► static_graph JSON files (CFG/CG)
            │
            └─► feature_engineer.py ──► static_features.csv (FeatureVector)
                     │
                     ├─► model_trainer.py ──► models/*.pkl + evaluation reports
                     │
                     └─► error_miner.py ──► error_cases.csv + taxonomy distribution
```

All intermediate files are version‑hashed and stored under `interim/`, `features/`, `models/`, and `reports/` respectively.
