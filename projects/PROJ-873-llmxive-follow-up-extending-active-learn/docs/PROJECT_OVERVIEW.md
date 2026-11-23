# llmXive: Active Learners as Efficient PRP Rerankers

## Project Overview

This project investigates the efficiency gains of using MinHash-LSH pre-clustering to filter redundant documents before applying an Active Learning-based reranker. The goal is to reduce the number of expensive LLM calls ("wasted calls") while maintaining or improving ranking quality (NDCG@10).

## Core Hypothesis

Redundant retrieval lists degrade active learning efficiency. By pre-clustering near-duplicates (Jaccard > 0.95) and selecting a single representative per cluster, we can:
1. Reduce the candidate pool size by ≥30%.
2. Maintain NDCG@10 within statistical significance of the full run.
3. Reduce "wasted" LLM calls (cosine similarity > 0.95) by a measurable margin.

## Architecture

The pipeline is divided into three main stages:

### 1. Data Ingestion & Redundancy Injection
- **Source**: BEIR datasets (`nfcorpus`, `scifact`, `trec-covid`).
- **Injection**: Synthetic redundancy is injected via synonym replacement and sentence shuffling to create controlled near-duplicate clusters.
- **Validation**: SHA-256 checksums ensure data integrity; cluster counts are verified against FR-002 (≥20 clusters of 3–5 items).

### 2. Pre-Clustering & Filtering
- **Algorithm**: MinHash-LSH (via `datasketch`) with adjustable Jaccard thresholds.
- **Filtering**: Candidates are filtered to keep one representative per cluster.
- **Threshold Sweep**: An automated sweep determines the optimal Jaccard threshold for the best trade-off between pool reduction and NDCG recovery.

### 3. Active Ranking & Evaluation
- **Ranker**: Baseline active ranker (without clustering) vs. Clustering-aided ranker.
- **Metrics**:
 - **NDCG@10**: Calculated against BEIR ground truth.
 - **Wasted Call Ratio**: Proxy-based (cosine > 0.95) with LLM consensus validation.
 - **Statistical Significance**: Wilcoxon signed-rank tests with Bonferroni correction.

## Key Modules

- `code/data_loader.py`: Handles BEIR downloads, synthetic redundancy injection, and real-world validation.
- `code/clustering.py`: Implements MinHash-LSH logic for near-duplicate detection.
- `code/ranker.py`: Orchestrates the ranking loop, applying pre-clustering filters.
- `code/metrics.py`: Calculates NDCG, wasted call ratios, and performs statistical tests.
- `code/run_pipeline.py`: The main entry point for running experiments across multiple seeds.

## Execution Flow

1. **Setup**: Initialize environment, check CPU-only constraints, and download datasets.
2. **Injection**: Generate redundant datasets and verify cluster counts.
3. **Baseline**: Run the active ranker on the full (redundant) and unique subsets.
4. **Clustering**: Run MinHash-LSH, filter candidates, and re-rank.
5. **Analysis**: Compare metrics, run statistical tests, and generate reports.

## Output Artifacts

All results are stored in `data/`:
- `data/injected/`: Synthetic redundant datasets.
- `data/results/`: NDCG scores, threshold sweep data, and statistical reports.
- `data/logs/`: Pairwise comparison logs and resource usage stats.

## Constraints

- **Runtime**: Max 6 hours per experiment (enforced by watchdog).
- **Memory**: Max 7GB RAM (enforced by watchdog).
- **Hardware**: CPU-only execution (CUDA disabled).
