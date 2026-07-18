# Design Document: llmXive Active Learner Reranker

## Overview
This project implements an active learning pipeline that uses MinHash-LSH pre-clustering to filter redundant retrieval results before passing them to an active ranker. The goal is to reduce "wasted" LLM calls while maintaining or improving NDCG@10 performance.

## Architecture

### Core Components

1. **Data Loading (`code/data_loader.py`)**
 - Fetches BEIR datasets (nfcorpus, scifact)
 - Implements synthetic redundancy injection via synonym replacement and sentence shuffling
 - Validates synthetic data against real-world near-duplicates from trec-covid

2. **Clustering (`code/clustering.py`)**
 - MinHash-LSH implementation for near-duplicate detection
 - Jaccard similarity thresholding (> 0.95)
 - Candidate pool filtering with minimum 30% reduction requirement

3. **Metrics (`code/metrics.py`)**
 - Cosine similarity proxy for wasted call detection (> 0.95 threshold)
 - NDCG@10 calculation against BEIR ground truth
 - Statistical significance testing (Wilcoxon signed-rank with Bonferroni correction)
 - Jaccard-Cosine correlation validation

4. **Ranking (`code/ranker.py`)**
 - Baseline active ranker without clustering
 - Clustering-aided variant with pre-filtering
 - LLM consensus validation for proxy accuracy

5. **Pipeline Orchestration (`code/run_pipeline.py`)**
 - Multi-seed execution loop
 - Threshold parameter sweeping
 - Resource monitoring (6h runtime, 7GB memory limits)

### Data Flow

```
BEIR Dataset → Redundancy Injection → MinHash-LSH Clustering
 ↓
 Baseline Run ← Unique Subset → Clustering-Aided Run
 ↓
 NDCG@10 Comparison + Statistical Significance Testing
```

## Configuration

### Resource Limits (FR-006)
- Maximum runtime: 6 hours
- Maximum memory: 7GB
- Enforced via `config.py` and `utils.py` watchdog

### Thresholds
- Cosine similarity proxy threshold: 0.95
- MinHash Jaccard threshold: 0.95 (configurable via sweep)
- Minimum pool reduction: 30%

## Experimental Protocol

### User Story 1: Baseline Efficiency Loss
- Inject synthetic redundancy (3-5 near-duplicates per cluster)
- Run baseline active ranker on full redundant list
- Measure wasted call ratio and NDCG@10 drop

### User Story 2: Clustering Recovery
- Apply MinHash-LSH pre-clustering
- Run active ranker on filtered pool
- Verify NDCG@10 recovery and wasted call reduction

### User Story 3: Statistical Validation
- Multi-seed execution (default: 5 seeds)
- Wilcoxon signed-rank tests on NDCG@10 and wasted call ratios
- Bonferroni correction for multiple hypothesis testing

## Results Artifacts

- `data/results/threshold_sweep.json`: Optimal threshold and sensitivity data
- `data/results/statistical_report.md`: Bonferroni-corrected p-values
- `data/injected/`: Synthetic redundancy datasets
- `logs/`: Pairwise comparison logs and resource usage stats

## Dependencies

See `requirements.txt` for complete list:
- beir
- sentence-transformers
- datasketch
- scikit-learn
- scipy
- pandas
- numpy
- nltk
- pytest
- pyyaml
