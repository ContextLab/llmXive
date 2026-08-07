# Quickstart Guide for llmXive Follow-up

This guide explains how to run the full research pipeline for the "Active Learners as Efficient PRP Rerankers" extension.

## Prerequisites

1. Ensure you have Python 3.11+ installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Validate the environment:
 ```bash
 bash code/validate_env.sh
 ```

## Data Preparation

The pipeline requires BEIR datasets (`nfcorpus`, `scifact`, `trec-covid`) and injected redundancy datasets.

### Step 1: Prepare Injected Datasets

Run the data loader to fetch BEIR data and inject synthetic redundancy.
This generates `data/processed/injected_datasets.json`.

```bash
python code/data_loader.py prepare
```

### Step 2: Validate TREC-COVID (Optional)

If you specifically need to validate redundancy on TREC-COVID:

```bash
python code/data_loader.py validate_trec_covid
```

## Running the Pipeline

The main pipeline orchestrates the ranking experiments, sampling, and metric calculation.

### Basic Execution

Run the baseline variant with default settings:

```bash
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 42
```

### Clustering-Aided Variant

Run the clustering-aided variant:

```bash
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 42
```

### Cross-Dataset Generalization

To run the generalization check across `nfcorpus`, `scifact`, and `trec-covid`:

```bash
python code/run_pipeline.py --variant baseline --budgets 100 --seeds 42 --cross-dataset
```

## Artifact Generation

The pipeline produces the following key artifacts:

- `data/processed/injected_datasets.json`: Redundancy-injected datasets.
- `data/processed/clusters.json`: MinHash-LSH clusters.
- `data/processed/unique_subset.json`: Deduplicated candidate lists.
- `data/processed/comparison_log.json`: Pairwise comparison logs.
- `data/results/flagged_pairs_count.json`: Count of "wasted" calls.
- `data/results/consensus_sample.json`: Sampled pairs for LLM validation.
- `data/results/consensus_ground_truth.json`: LLM ground truth labels.
- `data/results/correction_factor.json`: Proxy accuracy correction factor.
- `data/results/us1_efficiency_ratio.json`: Final efficiency metrics.
- `data/results/statistical_report.md`: Final statistical analysis.

## Troubleshooting

### Missing Artifacts

If you see `FileNotFoundError` regarding `injected_datasets.json`, ensure you ran the `prepare` command in the Data Preparation section.

### Resource Limits

If the pipeline terminates due to time or memory limits, check `code/config.py` for `MAX_RUNTIME_HOURS` and `MAX_MEMORY_GB` settings.

## Validation

To verify the constitution compliance of the generated artifacts:

```bash
python code/audit/validate_constitution.py
```
