# Data Model: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

## Overview

This document defines the data structures used throughout the pipeline, ensuring consistency between the data loader, the injection module, the ranker, and the metrics calculator. All data is stored in JSON/JSONL format for portability and versioning.

## Entity Definitions

### 1. Document (Raw & Processed)
Represents a single passage from the BEIR corpus.
- **id**: `str` (Unique identifier from BEIR, e.g., "doc_123")
- **text**: `str` (Full text of the passage)
- **query_id**: `str` (Optional, if part of a specific query)
- **metadata**: `dict` (Optional, e.g., source, original length)
- **validation_score**: `float` (Optional, cosine similarity to original for injected docs)

### 2. Candidate List
A collection of documents associated with a specific query.
- **query_id**: `str`
- **documents**: `list[Document]`
- **redundancy_level**: `float` (0.0 to 1.0, percentage of near-duplicates)
- **injection_method**: `str` (e.g., "back_translation", "semantic_perturbation")

### 3. Comparison Pair
A tuple of two documents compared by the active ranker.
- **pair_id**: `str` (Unique hash of the pair)
- **doc_a_id**: `str`
- **doc_b_id**: `str`
- **similarity_score**: `float` (Cosine similarity)
- **is_wasted**: `bool` (True if `similarity_score > 0.95`)
- **validation_status**: `str` ("unvalidated", "validated_llm", "validated_proxy")
- **llm_consensus**: `str` (Optional, "agree", "disagree", "null")

### 4. Cluster
A group of near-duplicate documents identified by MinHash-LSH.
- **cluster_id**: `str`
- **member_ids**: `list[str]`
- **representative_id**: `str` (The document selected for ranking)
- **jaccard_min**: `float` (Minimum Jaccard similarity within cluster)

### 5. Metrics Snapshot
Aggregated results for a single run.
- **run_id**: `str` (Random seed)
- **dataset**: `str` (e.g., "scifact")
- **redundancy_level**: `float`
- **total_calls**: `int`
- **wasted_calls**: `int`
- **wasted_ratio**: `float`
- **ndcg_at_10**: `float`
- **execution_time_seconds**: `float`
- **peak_memory_mb**: `float`
- **validation_method**: `str` ("proxy_only", "llm_consensus", "hybrid")
- **proxy_accuracy**: `dict` (Optional, {"precision": float, "recall": float} if validated)
- **unvalidated_flag**: `bool` (True if proxy-only due to resource constraints)

### 6. Sample Config
Configuration for the LLM consensus sample.
- **sample_size**: `int`
- **skip_validation**: `bool` (True if no flagged pairs or resource constraints)
- **reason**: `str` (e.g., "zero_flagged_pairs", "ram_limit_exceeded")

## File Schemas

### `data/processed/comparison_log.jsonl`
Each line is a `Comparison Pair` object.
- **Format**: JSONL (one JSON object per line).
- **Purpose**: The single source of truth for all pairwise comparisons.

### `data/processed/injected_datasets.json`
A dictionary mapping dataset names to their injected candidate lists.
- **Format**: JSON.
- **Structure**: `{ "scifact": [Candidate List 1, ...], "nfcorpus": [...] }`

### `data/processed/resource_log.json`
Log of resource usage (RAM, time) for the entire pipeline.
- **Format**: JSON.
- **Structure**: `{ "max_ram_mb": float, "total_time_seconds": float, "timeout_triggered": bool }`

### `data/results/flagged_pairs_count.json`
Aggregated count of wasted pairs.
- **Format**: JSON.
- **Structure**: `{ "total_flagged": int, "total_pairs": int, "ratio": float, "validation_status": str, "unvalidated_flag": bool }`

### `data/results/sample_config.json`
Configuration for the consensus sample.
- **Format**: JSON.
- **Structure**: `{ "sample_size": int, "skip_validation": bool, "reason": str }`

### `data/results/consensus_sample.json`
List of pairs selected for LLM validation.
- **Format**: JSON.
- **Structure**: `{ "pairs": [Comparison Pair, ...] }` (Can be empty list if `skip_validation` is true).

### `data/results/final_report.json`
The final aggregated results across all seeds and datasets.
- **Format**: JSON.
- **Structure**: `{ "runs": [Metrics Snapshot, ...], "statistical_summary": { ... }, "threshold_sweep_results": [...] }`

## Data Flow

1. **Load**: `data/raw/` (BEIR) -> `data/processed/injected_datasets.json` (via `data_loader.py`).
2. **Cluster**: `injected_datasets.json` -> `data/processed/clusters.json` (via `minhash_pipeline.py`).
3. **Rank**: `clusters.json` -> `data/processed/comparison_log.jsonl` (via `ranker.py`).
4. **Evaluate**: `comparison_log.jsonl` + `data/raw/qrels` -> `data/results/flagged_pairs_count.json`, `data/results/final_report.json` (via `metrics.py`).
5. **Monitor**: `resource_log.json` written by `resource_monitor.py` at the end of the pipeline.