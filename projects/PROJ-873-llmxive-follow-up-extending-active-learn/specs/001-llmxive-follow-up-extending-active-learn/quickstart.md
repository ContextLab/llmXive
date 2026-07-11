# Quickstart: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine with sufficient RAM)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-873-llmxive-follow-up-extending-active-learn
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### 1. Prepare Data
Download and prepare the BEIR datasets with synthetic redundancy:
```bash
python code/data_loader.py --prepare
```
*This will download `scifact`, `nfcorpus`, and `trec-covid`, inject synthetic redundancy, and save to `data/processed/`.*

### 2. Run Baseline (High Redundancy)
Execute the baseline active ranker on the redundant list for all required budgets:
```bash
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5
```

### 3. Run Clustering-Aided Variant
Execute the MinHash-LSH filtered ranker for all required budgets:
```bash
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5
```

### 4. Run Unique Baseline (Reference)
Execute on a unique pool of N=100 for comparison:
```bash
python code/run_pipeline.py --variant unique_baseline --budgets 20 50 100 --seeds 5
```

### 5. Statistical Analysis
Compute metrics and run significance tests:
```bash
python code/metrics.py --aggregate
```
*This generates `data/results/statistical_summary.csv`, `data/results/ndcg_recovery_plot.png`, and `data/results/correlation_analysis.json`.*

## Verification

- **Check Resource Usage**: Monitor RAM and CPU during `run_pipeline.py`. It should stay under 7GB RAM and complete within 6 hours.
- **Check Outputs**: Verify `data/results/statistical_summary.csv` contains p-values < 0.05 for the clustering-aided variant if the hypothesis holds.
- **Check Correlation**: Verify `data/results/correlation_analysis.json` contains the Jaccard-Cosine correlation results.

## Troubleshooting

- **OOM Error**: Reduce `--budgets` or `--seeds` in `run_pipeline.py`.
- **Slow Embedding**: Ensure `sentence-transformers` is installed and using CPU (no CUDA errors).
- **MinHash Threshold**: Adjust `--minhash-threshold` in `run_pipeline.py` if clustering is too aggressive.