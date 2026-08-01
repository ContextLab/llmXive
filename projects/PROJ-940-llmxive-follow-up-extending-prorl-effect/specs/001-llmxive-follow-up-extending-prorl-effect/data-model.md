# Data Model: llmXive Follow-up: Extending ProRL for Zero-Shot Proactive Recommendation

## 1. Overview
This document defines the data structures used for graph representation, path generation, and evaluation results. All data is stored in memory during execution and serialized to JSON/Parquet for persistence.

## 2. Core Entities

### 2.1 ItemNode
Represents a single item in the recommendation graph.
- **id**: `str` (Unique identifier, e.g., "item_123")
- **features**: `dict` (Key-value pairs of metadata, e.g., `{"genre": ["Action", "Sci-Fi"]}`)
- **feature_vector**: `list[float]` (Pre-computed one-hot or TF-IDF vector for similarity)

### 2.2 SimilarityEdge
Represents a connection between two items.
- **source_id**: `str`
- **target_id**: `str`
- **weight**: `float` (Cosine similarity score, range [0.0, 1.0])
- **is_valid**: `bool` (True if weight > 0.0, False if zero overlap)

### 2.3 RecommendationPath
A candidate recommendation sequence.
- **path_id**: `str` (Unique hash of the sequence)
- **seed_id**: `str`
- **nodes**: `list[str]` (Ordered list of item IDs)
- **raw_score**: `float` (Sum of edge weights)
- **rectified_score**: `float` (After SRC and PSA)
- **positions**: `list[int]` (0-indexed positions)
- **alpha**: `float` (The alpha value used for PSA, e.g., 0.1 or 0.0 for control)
- **method**: `str` ("beam", "greedy", "prorl", "prorl-null")

### 2.4 EvaluationMetric
Results of a single evaluation run.
- **seed_id**: `str`
- **method**: `str` ("beam", "prorl", "prorl-null")
- **precision_at_k**: `float`
- **recall_at_k**: `float`
- **diversity**: `float`
- **coverage**: `float`
- **ground_truth_next**: `str`
- **k_value**: `int` (The K used for Precision@K, e.g., 10)

## 3. Data Flow

1. **Input**: Raw CSV (MovieLens) -> **Processed**: `ItemNode` list, `SimilarityEdge` list.
2. **Processing**: Seed -> **Output**: `RecommendationPath` list (Beam Search).
3. **Scoring**: Apply SRC/PSA -> **Output**: `RecommendationPath` list (Rectified).
4. **Evaluation**: `RecommendationPath` + Ground Truth -> **Output**: `EvaluationMetric` record.
5. **Aggregation**: `EvaluationMetric` list -> **Output**: Statistical summary (p-values, means).

## 4. Storage Strategy
- **Graph**: Serialized as `data/processed/graph.pkl` (NetworkX object) or `data/processed/graph.parquet` (edge list).
- **Paths**: `results/raw_paths.json`, `results/rectified_paths.json`.
- **Metrics**: `results/metrics_summary.json`.
- **Logs**: `logs/pipeline.log`.