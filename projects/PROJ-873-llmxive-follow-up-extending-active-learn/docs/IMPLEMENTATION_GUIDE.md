# Implementation Guide

## Prerequisites

- Python 3.11+
- CPU-only environment (no CUDA)
- 7GB+ RAM available

## Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

Key libraries:
- `beir`: For dataset loading.
- `sentence-transformers`: For embedding and cosine similarity.
- `datasketch`: For MinHash-LSH clustering.
- `scikit-learn`, `scipy`: For statistical analysis.
- `pandas`, `numpy`: For data manipulation.

## Configuration

Edit `code/config.py` to adjust:
- `MAX_RUNTIME_HOURS`: Default 6.
- `MAX_MEMORY_GB`: Default 7.
- `JACCARD_THRESHOLD`: Default 0.95.

## Running the Pipeline

### 1. Data Preparation
```bash
python code/data_loader.py
```
This downloads BEIR datasets and injects synthetic redundancy.

### 2. Baseline Execution
```bash
python code/run_baseline_unique.py
```
Runs the active ranker on the unique subset to establish a baseline NDCG.

### 3. Full Experiment (Baseline + Clustering)
```bash
python code/run_pipeline.py
```
Executes the full workflow: baseline, clustering-aided, threshold sweep, and statistical tests.

### 4. Threshold Analysis
```bash
python code/analyze_threshold_sweep.py
```
Analyzes the results of the threshold sweep to find the optimal Jaccard threshold.

### 5. Report Generation
```bash
python code/generate_statistical_report.py
```
Generates a markdown report with Bonferroni-corrected p-values and efficiency metrics.

## Validation

### Resource Limits
The pipeline includes a watchdog (`code/utils.py`) that terminates execution if:
- Runtime > 6 hours.
- Memory > 7GB.

### Data Integrity
SHA-256 checksums are calculated for all downloaded datasets and stored in `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml`.

### Statistical Validity
All comparisons use Wilcoxon signed-rank tests with Bonferroni correction to control for multiple hypothesis testing.

## Troubleshooting

- **CUDA Errors**: Ensure `CUDA_VISIBLE_DEVICES=""` is set.
- **Memory Errors**: Reduce `MAX_MEMORY_GB` or process datasets in smaller chunks.
- **Timeout Errors**: Increase `MAX_RUNTIME_HOURS` if the dataset is very large.
