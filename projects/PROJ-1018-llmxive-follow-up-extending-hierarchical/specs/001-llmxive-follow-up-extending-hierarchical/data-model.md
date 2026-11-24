# Data Model: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

## 1. Core Entities

| Entity | Description | Produced By | Consumed By |
|--------|-------------|-------------|-------------|
| **RelevanceProfile** | Aggregated retrieval scores for a single document chunk. | `src/aggregation.py` | `src/clustering.py` |
| **StaticIndex** | K centroids (in PCA space) + mapping `chunk_id → cluster_id`. | `src/clustering.py` | `src/inference.py` |
| **EvaluationReport** | Quantitative results: log‑perplexity, QA accuracy, latency, memory, statistical test. | `src/evaluation.py` (and `src/report_sweep.py` for sweeps) | Paper generation, CI checks |
| **SplitDefinition** | JSON list of document IDs for validation and test splits, plus checksum. | `src/data_loader.py` | All downstream scripts |

## 2. Schema Definitions (YAML)

### 2.1 RelevanceProfile (JSON, conforms to `contracts/relevance_profile.schema.yaml`)
```json
{
  "document_id": "string",
  "chunk_id": "integer",
  "start_token": "integer",
  "end_token": "integer",
  "relevance_scores": ["number"],
  "aggregated_profile": ["number"],
  "pca_components": ["number"],   // optional, after PCA step
  "checksum": "string"
}
```

### 2.2 StaticIndex (JSON, conforms to `contracts/static_index.schema.yaml`)
```json
{
  "k": "integer",
  "centroids": [["number"]],
  "chunk_to_cluster_map": {"string": "integer"},
  "validation_checksum": "string",
  "created_at": "string",   // ISO‑8601 timestamp
  "seed": "integer",
  "pca_components": "integer",
  "distance_metric": "string"
}
```

### 2.3 EvaluationReport (JSON, conforms to `contracts/evaluation_report.schema.yaml`)
```json
{
  "experiment_id": "string",
  "k_value": "integer",
  "metrics": {
    "dynamic": {"log_perplexity": "number", "qa_accuracy": "number", "latency_ms": "number"},
    "static": {"log_perplexity": "number", "qa_accuracy": "number", "latency_ms": "number"}
  },
  "statistical_test": {"method": "string", "p_value": "number", "significance": "boolean", "confidence_interval": ["number"]},
  "latency_reduction_factor": "number",
  "memory_footprint_bytes": "integer"
}
```

### 2.4 SplitDefinition (JSON, conforms to `contracts/split_definition.schema.yaml`)
```json
{
  "validation_ids": ["string"],
  "test_ids": ["string"],
  "checksum": "string"
}
```

## 3. Data Flow Diagram
1. **Streaming PG‑19** → `src/data_loader.py` → `SplitDefinition` (validation & test).  
2. **Validation Docs** → `src/extraction.py` → raw `.pt` tensors (temporary).  
3. Raw tensors → `src/aggregation.py` → collection of `RelevanceProfile` objects.  
4. `RelevanceProfile` → `src/clustering.py` (PCA → K‑Means) → `StaticIndex`.  
5. **Test Docs** + `StaticIndex` → `src/inference.py` (static mode) → logits (in‑memory).  
6. Logits + Long‑QA data → `src/evaluation.py` → `EvaluationReport`.  
7. `src/sensitivity.py` repeats steps 4‑6 for each K; `src/report_sweep.py` aggregates into `sweep_report.json`.

All intermediate artifacts are checksum‑verified, stored under `data/`, and conform to the schemas above. The `filtered_pgXX.json` file produced in Phase 0 conforms to the `SplitDefinition` schema, guaranteeing downstream scripts a well‑defined input structure.

---
