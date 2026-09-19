# Data Model: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

## 1. Entities & Relationships

### 1.1 RelevanceProfile
Represents the aggregated retrieval scores for a specific document chunk.
- **Source**: Output of `extraction.py` (FR-001).
- **Usage**: Input to `clustering.py` (FR-002).

### 1.2 StaticIndex
The static lookup table containing cluster centroids and chunk-to-cluster mappings.
- **Source**: Output of `clustering.py` (FR-002).
- **Usage**: Input to `inference.py` (FR-003).

### 1.3 EvaluationReport
Structured output containing all metrics and statistical results.
- **Source**: Output of `evaluation.py` (FR-004, FR-005, FR-006, FR-007, FR-008).
- **Usage**: Final artifact for the paper.

## 2. Schema Definitions

### 2.1 RelevanceProfile (JSON)
```json
{
  "document_id": "string",
  "chunk_id": "integer",
  "start_token": "integer",
  "end_token": "integer",
  "relevance_scores": "list[float]",
  "aggregated_profile": "list[float]",
  "pca_components": "list[float] (optional, if PCA applied)",
  "checksum": "string"
}
```

### 2.2 StaticIndex (JSON/YAML)
```json
{
  "k": "integer",
  "centroids": "list[list[float]]",
  "chunk_to_cluster_map": "dict[string, integer]",
  "validation_checksum": "string",
  "created_at": "string (ISO8601)",
  "seed": "integer",
  "pca_components": "integer (dimensionality used)",
  "distance_metric": "string (e.g., 'cosine')"
}
```

### 2.3 EvaluationReport (JSON)
```json
{
  "experiment_id": "string",
  "k_value": "integer",
  "metrics": {
    "dynamic": {
      "log_perplexity": "float",
      "qa_accuracy": "float",
      "latency_ms": "float"
    },
    "static": {
      "log_perplexity": "float",
      "qa_accuracy": "float",
      "latency_ms": "float"
    }
  },
  "statistical_test": {
    "method": "string (Wilcoxon signed-rank)",
    "p_value": "float",
    "significance": "boolean",
    "confidence_interval": "list[float]"
  },
  "latency_reduction_factor": "float",
  "memory_footprint_bytes": "integer"
}
```

## 3. Data Flow

1. **Ingest**: `PG-19` (Streamed) $\to$ `Tokenized Documents`.
2. **Split**: `Tokenized Documents` $\to$ `Validation Split` ([deferred]) + `Test Split` ([deferred]).
3. **Extract**: `Validation Split` + `HiLS Model` $\to$ `RelevanceProfiles`.
4. **Cluster**: `RelevanceProfiles` $\to$ `PCA` $\to$ `K-Means` $\to$ `StaticIndex`.
5. **Evaluate**: `StaticIndex` + `Test Split` + `HiLS Model` $\to$ `EvaluationReport`.

## 4. Constraints & Validations

- **RelevanceScores**: Must be non-negative, non-null.
- **ChunkIDs**: Must be unique per document.
- **Centroids**: Must match the dimension of `pca_components`.
- **Memory**: `RelevanceProfiles` must be processed in batches to stay under 7GB RAM.
- **Checksums**: All intermediate files must be checksummed (SHA-256) and recorded in `data/` metadata.
- **Independence**: Validation split (clustering) must not overlap with Test split (evaluation).