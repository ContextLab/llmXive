# Data Model: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

## Overview

This document defines the data structures used throughout the pipeline, from raw BEIR ingestion to final statistical outputs. All data is stored in `data/` with strict versioning.

## Entities

### 1. Document
Represents a single passage in the retrieval candidate list.
- **id**: `str` (Unique identifier, e.g., `scifact_123`)
- **text**: `str` (The full text of the passage)
- **source**: `str` (e.g., `scifact`, `synthetic_cluster_1`)
- **is_synthetic**: `bool` (True if generated via synonym/shuffling)
- **parent_document_id**: `str` (Optional. ID of the original document if this is a synthetic variant; null otherwise. Used to track lineage.)
- **cluster_id**: `str` (Optional. Cluster ID assigned by MinHash-LSH; null if not clustered yet. Used for flat schema representation.)

### 2. ComparisonPair
Represents a pairwise comparison made by the active ranker.
- **id**: `str` (UUID)
- **doc_a_id**: `str`
- **doc_b_id**: `str`
- **ranker_decision**: `str` ("a_wins", "b_wins", "tie")
- **cosine_similarity**: `float` (0.0 to 1.0)
- **is_wasted**: `bool` (True if `cosine_similarity` > 0.95. This is the operational classification.)
- **llm_consensus_label**: `str` (Optional. Ground truth label from stratified sampling: "wasted" if tie/low-conf, "informative" otherwise.)

### 3. Cluster
Represents a group of near-duplicate documents identified by MinHash-LSH.
- **cluster_id**: `str` (e.g., `cluster_1`)
- **member_ids**: `List[str]`
- **representative_id**: `str` (The document chosen to represent the cluster, selected by highest similarity to centroid.)
- **representative_selection_strategy**: `str` (e.g., "centroid_similarity", "relevance_score")
- **minhash_jaccard_score**: `float` (Internal consistency score)

### 4. RunMetric
Aggregated metrics for a single execution run.
- **run_id**: `str` (UUID)
- **seed**: `int`
- **variant**: `str` ("baseline", "clustering_aided", "unique_baseline")
- **n_calls**: `int`
- **n_wasted**: `int`
- **wasted_ratio**: `float`
- **ndcg_at_10**: `float`
- **runtime_seconds**: `float`
- **peak_memory_mb**: `float`

### 5. StatisticalTestResult
Results of hypothesis testing.
- **test_id**: `str`
- **test_type**: `str` ("wilcoxon_ndcg", "wilcoxon_wasted")
- **variant_a**: `str`
- **variant_b**: `str`
- **p_value**: `float`
- **statistic**: `float`
- **is_significant**: `bool` (p < 0.05)

### 6. CorrelationResult
Results of the correlation analysis between MinHash and Cosine similarity.
- **analysis_id**: `str`
- **sample_size**: `int`
- **correlation_coefficient**: `float` (Pearson or Spearman)
- **p_value**: `float`
- **description**: `str` (Summary of the correlation strength)

## Data Flow

1. **Ingestion**: `data/raw/beir_scifact.parquet` -> `Document` objects.
2. **Synthesis**: `Document` objects -> `Document` (with synthetic variants, `parent_document_id` set) -> `data/processed/redundant_scifact.parquet`.
3. **Clustering**: `redundant_scifact.parquet` -> `Cluster` objects (via MinHash-LSH).
4. **Ranking**: `Cluster` or `Redundant` list -> `ComparisonPair` objects (via Active Ranker).
5. **Aggregation**: `ComparisonPair` objects -> `RunMetric` objects.
6. **Analysis**: `RunMetric` objects (across seeds) -> `StatisticalTestResult`.
7. **Correlation**: Labeled subset of `ComparisonPair` objects -> `CorrelationResult`.

## Storage Format

- **Raw Data**: Parquet (BEIR native format).
- **Processed Data**: Parquet (for fast I/O).
- **Intermediate/Logs**: JSONL (for streaming analysis).
- **Final Results**: CSV (for statistical analysis and plotting).
- **Correlation Analysis**: JSON (`data/results/correlation_analysis.json`).