# Data Model: GraphCompass: Topological Predictors of Semantic Coherence in CPU-Constrained RAG

## Overview

This document defines the data structures, schemas, and flow for the GraphCompass project. All data artifacts are stored in `data/` and validated against the schemas in `contracts/`.

## Data Flow

1.  **Raw Data**: Downloaded from HuggingFace (`hotpot_qa`, `wikipedia`).
2.  **Preprocessed Data**: Tokenized, filtered, and split into `train`/`test`. Queries are filtered to ensure ground-truth answers exist in `test`.
3. **Fixed Vocabulary**: Pre-computed list of top [deferred] terms from the full Wikipedia dump (`data/processed/fixed_vocab.json`).
4.  **Graph Data**: `networkx` graphs serialized as Pickle or JSON for each document.
5.  **Feature Vectors**: Topological signatures (numpy arrays) and neural embeddings.
6.  **Results**: Retrieval metrics (Recall@k), correlation coefficients, and latency logs.

## Entity Definitions

### Document
A single unit of text (abstract or wiki page) with metadata.
- `id`: Unique identifier (string).
- `text`: Raw text content (string).
- `source`: Dataset source (string, e.g., "wikipedia_20231001_en").

### Graph
A lexical co-occurrence graph.
- `nodes`: List of term strings.
- `edges`: List of tuples (term1, term2).
- `attributes`: Dictionary of graph-level metrics (modularity, avg_path_length).

### TopologicalSignature
A numerical vector derived from a Graph.
- `modularity`: Float.
- `avg_path_length`: Float.
- `degree_centrality_mean`: Float.
- `degree_centrality_std`: Float.
- `betweenness_centrality_mean`: Float.
- `betweenness_centrality_std`: Float.

### RetrievalResult
Metrics for a single query.
- `query_id`: String.
- `recall_at_5_graph`: Float.
- `recall_at_10_graph`: Float.
- `recall_at_5_neural`: Float.
- `recall_at_10_neural`: Float.
- `latency_graph`: Float (seconds).
- `latency_neural`: Float (seconds).
- `mean_modularity_top10`: Float (Aggregated metric for correlation).
- `mean_centrality_top10`: Float (Aggregated metric for correlation).

### CorrelationAnalysis
Aggregated statistical results.
- `metric_name`: String (e.g., "modularity").
- `spearman_r`: Float.
- `p_value`: Float.
- `bonferroni_adjusted_p`: Float.

## Storage Locations

| Entity | Location | Format |
| :--- | :--- | :--- |
| Raw Datasets | `data/raw/` | Parquet/JSON (as provided) |
| Preprocessed Corpus | `data/processed/corpus.jsonl` | JSONL |
| Fixed Vocabulary | `data/processed/fixed_vocab.json` | JSON |
| Filtered Queries | `data/processed/filtered_queries.jsonl` | JSONL |
| Graphs | `data/processed/graphs/` | Pickle (`.pkl`) |
| Feature Vectors | `data/processed/features.csv` | CSV |
| Retrieval Results | `data/results/retrieval_metrics.json` | JSON |
| Statistical Analysis | `data/results/correlation_analysis.json` | JSON |

## Versioning

- All files in `data/` are checksummed (SHA-256) upon creation.
- Checksums are recorded in `state/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag.yaml`.