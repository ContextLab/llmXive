# llmXive Quickstart Guide

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Data Preparation
1. Prepare injected datasets:
 ```bash
 python code/data_loader.py prepare
 ```
 This generates `data/processed/injected_datasets.json`.

2. Run clustering pipeline:
 ```bash
 python code/clustering.py --threshold 0.95
 ```
 This generates `data/processed/clusters.json`.

3. Run sampling pipeline:
 ```bash
 python code/sampling.py
 ```
 This generates `data/results/consensus_sample.json`.

4. Run ranker and metrics:
 ```bash
 python code/ranker.py --variant baseline --budget 100
 ```
 This generates `data/processed/comparison_log.json`, `data/processed/unique_subset.json`, `data/results/correction_factor.json`, and `data/results/us1_efficiency_ratio.json`.

## Pipeline Execution
Run the full pipeline with specific variants and budgets:

```bash
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 42 43 44
```

Or for clustering-aided:
```bash
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 42 43 44
```

## Cross-Dataset Validation
```bash
python code/data_loader.py validate_trec_covid
```

## Statistical Report
The statistical report is generated automatically at the end of the pipeline run if prerequisites are met.
Output: `data/results/statistical_report.md`

## Troubleshooting
- If `DataFlowViolationError` occurs, ensure `prepare` and `clustering` steps have been run successfully.
- If `FileNotFoundError` occurs for `injected_datasets.json`, run `python code/data_loader.py prepare` first.
