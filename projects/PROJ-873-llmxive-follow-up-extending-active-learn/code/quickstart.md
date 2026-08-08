# Quickstart Guide for llmXive Pipeline

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)

## Running the Pipeline

### Step 1: Prepare Injected Datasets

```bash
python code/data_loader.py prepare
```

This command prepares the injected datasets for `nfcorpus` and `scifact`, creating near-duplicate clusters for redundancy analysis.

### Step 2: Validate TREC-COVID Redundancy Clusters

```bash
python code/data_loader.py validate_trec_covid
```

This command validates the redundancy clusters on the `trec-covid` dataset and saves the results to `data/results/trec_covid_validation.json`.

### Step 3: Run the Full Pipeline

```bash
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 42
```

This command runs the full pipeline for the `baseline` variant with specified budgets and seeds.

For the `clustering_aided` variant:

```bash
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 42
```

### Step 4: Generate Statistical Report

The statistical report is automatically generated after the pipeline completes. It is saved to `data/results/statistical_report.md`.

## Output Files

- `data/processed/injected_datasets.json`: Injected datasets with redundancy clusters.
- `data/processed/clusters.json`: MinHash-LSH clustering results.
- `data/results/consensus_sample.json`: Sampled pairs for LLM consensus validation.
- `data/results/flagged_pairs_count.json`: Count of flagged pairs.
- `data/results/trec_covid_validation.json`: Validation results for `trec-covid`.
- `data/results/statistical_report.md`: Final statistical report.

## Troubleshooting

- Ensure all required artifacts exist before running the pipeline.
- Check resource limits (6 hours runtime, 7GB memory) to avoid early termination.
- Verify that the `beir` library is installed and datasets are downloadable.