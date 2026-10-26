# Data Model

## Processed Memory Nodes (Parquet)

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | string | Unique identifier for the memory node. |
| `timestamp` | string (ISO‑8601) | Event occurrence time. |
| `event_label` | string | Categorical label of the event (used for rarity counting). |
| `embedding` | bytes (np.float32, shape = (768,)) | Vector representation of the audiovisual segment. |
| `is_rare` | boolean | `True` if the event label occurs ≤ 5 times in the corpus (FR‑012). |

*Stored as `data/processed/memory_nodes.parquet`.*

## FAISS HNSW Index

- **File**: `data/processed/faiss_hnsw.index`  
- **Source**: Built deterministically from the embeddings in `memory_nodes.parquet` (seed = 42).  
- **Parameters**: `M=16`, `ef_construction=200`, `ef_search=50`.  
- **Purpose**: Provides fast k‑NN search for both the Fixed Hierarchy and Semantic Decay retrievers.

## Evaluation Report (JSON)

The report must validate against `contracts/evaluation_report.schema.yaml`. Top‑level keys:

| Key | Type | Meaning |
|-----|------|---------|
| `optimal_lambda` | number | Decay rate λ selected by deterministic grid search (Phase 3). |
| `validation_accuracy` | number | Top‑rank accuracy on the 50‑query validation set using the optimal λ. |
| `long_term` | object | `{ "accuracy_top1": number, "num_queries": integer }` (SC‑001). |
| `short_term` | object | `{ "accuracy_top1": number, "num_queries": integer }` (SC‑004). |
| `overall` | object | `{ "accuracy_top1": number }`. |
| `latency` | object | `{ "max_ms": number, "mean_ms": number, "p95_ms": number }` (SC‑003). |
| `cpu_cycles` | object | `{ "baseline_avg": number, "semantic_decay_avg": number, "ratio": number }` (SC‑009). |
| `mcnemar_test` | object | `{ "statistic": number, "p_value": number, "significant": boolean }` (SC‑002). |
| `flags` | array of strings | Any warnings (e.g., insufficient rare events, short‑term degradation). |

All numeric fields may be `[deferred]` in the plan; they will be populated at runtime.

---
