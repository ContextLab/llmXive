# Quickstart Guide - llmXive Active Learning Pipeline

## Prerequisites

- Python 3.11+
- pip installed
- 7GB RAM available
- No GPU required (CPU-only)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify environment
bash code/validate_env.sh
```

## Running the Pipeline

### Step 1: Prepare Injected Datasets (T012)

This generates synthetic redundancy in the datasets:

```bash
python code/data_loader.py prepare
```

This creates:
- `data/processed/injected_datasets.json`

### Step 2: Validate TREC-COVID (T017)

Check for real-world redundancy:

```bash
python code/data_loader.py validate_trec_covid
```

This creates:
- `data/results/trec_covid_validation.json`

### Step 3: Calculate Sample Size (T013b)

```bash
python code/calculate_sample_size.py
```

This creates:
- `data/results/sample_config.json`

### Step 4: Run Sampling Pipeline (T013c)

```bash
python code/run_sampling.py
```

This creates:
- `data/results/consensus_sample.json`

### Step 5: Run Main Pipeline

Run the baseline variant:

```bash
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 42
```

Run the clustering-aided variant:

```bash
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 42
```

This creates:
- `data/results/pipeline_results_baseline.json`
- `data/results/pipeline_results_clustering_aided.json`

## Output Artifacts

| File | Description |
|------|-------------|
| `data/processed/injected_datasets.json` | Injected redundancy clusters |
| `data/processed/clusters.json` | MinHash-LSH clusters |
| `data/results/flagged_pairs_count.json` | Count of wasted calls |
| `data/results/sample_config.json` | Sampling configuration |
| `data/results/consensus_sample.json` | Selected sample indices |
| `data/results/trec_covid_validation.json` | TREC-COVID validation results |
| `data/results/pipeline_results_*.json` | Pipeline execution results |

## Troubleshooting

### Missing Artifacts

If you see `PipelineDependencyError`, ensure you've run the preparation steps in order:

1. `python code/data_loader.py prepare`
2. `python code/clustering.py` (to generate clusters.json)

### Network Issues

If BEIR download fails, check your internet connection. The pipeline will fail loudly (no synthetic fallback).

### Resource Limits

The pipeline enforces 6-hour runtime and 7GB memory limits. If exceeded, it will terminate gracefully.