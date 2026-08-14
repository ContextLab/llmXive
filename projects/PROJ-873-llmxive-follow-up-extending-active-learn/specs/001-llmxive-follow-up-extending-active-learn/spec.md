# Specification: llmXive PRP Redundancy Analysis
**Project**: PROJ-873-llmxive-follow-up-extending-active-learn
**Status**: Draft
**Version**: 1.0.0

## Overview
This specification defines the requirements for the "Active Learners as Efficient PRP Rerankers" follow-up study, focusing on quantifying redundancy-induced efficiency loss and validating CPU-tractable pre-clustering recovery.

## Functional Requirements

### FR-001: Redundancy Injection
The system must be able to inject synthetic redundancy into a baseline dataset (BEIR) to simulate real-world near-duplicate scenarios.
- **Method**: Synonym replacement and sentence shuffling.
- **Target**: Create ≥ 20 clusters of 3–5 near-duplicate passages with cosine similarity > 0.95.

### FR-002: Similarity Thresholding
The system must identify near-duplicate pairs using a cosine similarity threshold of 0.95.

### FR-003: Active Learning Baseline
The system must run a baseline active learning ranker on the unique subset of the injected data.

### FR-004: Wasted Call Detection
The system must count "wasted" LLM calls defined as comparisons between pairs with similarity > 0.95.

### FR-005: Pre-Clustering Filter
The system must implement a MinHash-LSH clustering step to reduce the candidate pool before ranking.

### FR-006: Resource Constraints
To ensure reproducibility and adherence to Constitution Principle IV, the pipeline execution is strictly bounded:
- **Runtime Limit**: The pipeline must terminate if execution exceeds a **limit of 6 hours**.
- **Memory Limit**: The pipeline must terminate if memory usage exceeds a **limit of 7GB**.
- **Enforcement**: These limits are enforced via `code/utils.py` (watchdog) and `code/config.py` (configuration).
- **Action**: If limits are approached, the system must perform graceful degradation or abort with a clear error.

### FR-007: Statistical Significance
The system must perform Wilcoxon signed-rank tests with Bonferroni correction to validate efficiency gains across multiple seeds.

### FR-008: Data Integrity
The system must verify the existence and integrity of all intermediate artifacts (checksums) before proceeding to downstream tasks.

### FR-009: Real-World Validation
The system must compare synthetic redundancy distributions against real-world near-duplicates from the `trec-covid` dataset.

## Non-Functional Requirements

### NFR-001: CPU-Only Execution
The pipeline must run entirely on CPU. GPU-specific libraries (bitsandbytes, accelerate) are forbidden.

### NFR-002: Reproducibility
All random seeds must be configurable and logged. Results must be deterministic for a given seed.

### NFR-003: Artifact Traceability
Every output file must be traceable to its input artifacts via a manifest or state file.

## Data Model

### Input
- BEIR Datasets: `nfcorpus`, `scifact`, `trec-covid`
- Configuration: `code/config.py`

### Intermediate Artifacts
- `data/processed/injected_datasets.json`: Synthetic redundancy injected data.
- `data/processed/clusters.json`: MinHash clusters.
- `data/processed/comparison_log.jsonl`: Pairwise comparison logs.
- `data/processed/unique_subset.json`: Unique representative subset.

### Output Artifacts
- `data/results/flagged_pairs_count.json`: Count of wasted calls.
- `data/results/us1_baseline_ndcg.json`: Baseline NDCG@10.
- `data/results/us1_redundant_ndcg.json`: Redundant run NDCG@10.
- `data/results/wilcoxon_ndcg.json`: Statistical test results.
- `data/results/statistical_report.md`: Final report.

## Constitution Principles

### Principle IV: Resource Efficiency
The system must not consume excessive computational resources. Execution must be bounded by the limits defined in FR-006.

### Principle VII: Data Fidelity
The system must not fabricate data. All metrics must be derived from real measurements on real or explicitly labeled synthetic data.

## Implementation Notes
- Use `beir` library for dataset loading.
- Use `datasketch` for MinHash-LSH.
- Use `llama-cpp-python` for LLM inference (TinyLlama Q4_K_M) where required.
- All scripts must be runnable via `python code/<script>.py`.