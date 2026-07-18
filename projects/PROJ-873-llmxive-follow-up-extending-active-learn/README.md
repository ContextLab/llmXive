# llmXive: Active Learners as Efficient PRP Rerankers

**Project ID**: PROJ-873-llmxive-follow-up-extending-active-learn

## Overview
This project investigates the efficiency gains of using active learning and pre-clustering to reduce redundant pairwise comparisons in Passage Re-ranking (PRP). It quantifies the degradation in NDCG@10 caused by redundant retrieval lists and validates that MinHash-LSH pre-clustering can recover performance within strict CPU resource limits (6h runtime, 7GB RAM).

## Features
- **Redundancy Quantification**: Measures NDCG drop and "wasted" call ratios on synthetic and real-world near-duplicate datasets.
- **MinHash-LSH Clustering**: CPU-tractable pre-clustering to filter redundant candidates before ranking.
- **Statistical Validation**: Wilcoxon signed-rank tests with Bonferroni correction to confirm efficiency gains.
- **Resource Guardrails**: Enforces strict runtime and memory limits via watchdogs.

## Quick Start

### Prerequisites
- Python 3.11+
- CPU-only environment (CUDA not required)

### Installation
```bash
pip install -r requirements.txt
```

### Running the Pipeline
1. **Data Preparation**:
 The pipeline automatically downloads BEIR datasets (nfcorpus, scifact) on first run.
 Synthetic redundancy can be injected via `code/data_loader.py`.

2. **Execute Full Experiment**:
 ```bash
 python code/run_pipeline.py
 ```
 This runs baseline and clustering-aided variants across multiple seeds, performs threshold sweeps, and generates statistical reports.

3. **Validation**:
 ```bash
 python code/quickstart_validator.py
 ```
 Verifies reproducibility and resource constraints.

## Project Structure
```
.
├── code/
│ ├── data_loader.py # BEIR loading, synthetic redundancy injection
│ ├── metrics.py # NDCG, similarity proxy, statistical tests
│ ├── clustering.py # MinHash-LSH implementation
│ ├── ranker.py # Active ranker logic
│ ├── run_pipeline.py # Main execution loop
│ └──...
├── data/
│ ├── beir/ # Downloaded BEIR datasets
│ ├── injected/ # Synthetic redundancy datasets
│ └── results/ # Experiment outputs
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── docs/
```

## Key Metrics
- **NDCG@10**: Normalized Discounted Cumulative Gain at 10.
- **Wasted Call Ratio**: Percentage of comparisons flagged as near-duplicate (similarity > 0.95).
- **Runtime/Memory**: Enforced via 6h/7GB limits.

## License
MIT

## Contributing
Please refer to the contribution guidelines in `docs/CONTRIBUTING.md`.
