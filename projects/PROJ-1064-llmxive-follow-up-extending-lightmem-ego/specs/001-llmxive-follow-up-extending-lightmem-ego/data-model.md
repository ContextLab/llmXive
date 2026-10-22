# Data Model

## Processed Memory Nodes (Parquet)

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | string | Unique identifier for the memory node. |
| `timestamp` | datetime (ISO‑8601) | Event occurrence time. |
| `event_label` | string | Categorical label of the event (used for rarity counting). |
| `embedding` | bytes (np.float32, shape = (768,)) | Vector representation of the audiovisual segment. |
| `is_rare` | boolean | `True` if the event label occurs ≤ 5 times in the corpus (FR‑012). |
| `is_semantically_distinct` | boolean | `True` if the event's within-cluster cohesion (via semantic clustering) exceeds the corpus median, indicating semantic significance beyond mere frequency (Phase 0.4). |

*Stored as `data/processed/memory_nodes.parquet`.*

## FAISS HNSW Index

**File**: `data/processed/faiss_hnsw_ego4d.index`  
**Source**: Built deterministically from Ego4D video‑MAE embeddings (seed = 42).  
**Parameters**: M=16, ef_construction=200, ef_search=50.  
**Modality**: Egocentric video embeddings (high-dimensional, float32).  
**Purpose**: Enables efficient k-NN search for both Fixed Hierarchy and Semantic Decay retrievers.

## Evaluation Report (JSON)

The report must validate against `contracts/evaluation_report.schema.yaml`. Key top‑level keys:

| Key | Type | Meaning |
|-----|------|----------|
| `optimal_alpha` | float | α selected by joint grid‑search (Phase 3). |
| `optimal_beta` | float | β selected by joint grid‑search (Phase 3). |
| `optimal_lambda` | float | λ selected by joint grid‑search (Phase 3). |
| `validation_accuracy` | float | Top-k accuracy on the validation set using (α*, β*, λ*). |
| `long_term` | object | Metrics for queries > 14 days. |
| `short_term` | object | Metrics for queries within a few days. |
| `overall` | object | Aggregate metrics across all queries. |
| `latency` | object | `max_ms`, `mean_ms`, `p95_ms`. |
| `cpu_cycles` | object | `baseline_avg`, `semantic_decay_avg`, `ratio`. |
| `mcnemar_test` | object | `statistic`, `p_value`, `significant` (bool). |
| `flags` | list[string] | Any warnings (e.g., insufficient rare events, short‑term degradation, power limitations). |

All numeric fields may be `[deferred]` during planning; they will be filled at runtime.

---