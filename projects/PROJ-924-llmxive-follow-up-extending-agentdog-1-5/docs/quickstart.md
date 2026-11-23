# Quick Start Guide

This guide walks you through the initial setup and execution of the llmXive AgentDoG drift detection pipeline.

## Prerequisites

- Python 3.9+
- pip
- Access to Hugging Face datasets

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure

The project creates the following directories:
- `code/`: Source code
- `data/raw/`: Raw dataset files
- `data/processed/`: Processed data files
- `tests/`: Test files
- `docs/`: Documentation
- `specs/`: Specification files

## Execution Pipeline

The main execution steps are:

1. **Fetch Validation Dataset (T012a-fetch)**:
 ```bash
 python code/data_loader.py --streaming --output data/raw/ATBench_raw.parquet
 ```

2. **Map Validation Dataset Labels (T012a-label)**:
 ```bash
 python code/data_loader.py --map-labels --input data/raw/ATBench_raw.parquet --output data/processed/ATBench_mapped.csv
 ```

3. **Fetch Agent Logs for Benchmarking (T012f)**:
 ```bash
 python code/data_loader.py --fetch-agent-logs --output data/raw/agent_logs.csv
 ```

4. **Define Taxonomy (T012d-gen)**:
 ```bash
 python code/taxonomy_builder.py --source agentdog_1_5_paper --output data/processed/taxonomy_centroids.json
 ```

5. **Run Drift Scoring (T021a-T021d)**:
 ```bash
 python code/drift_scoring.py --input data/raw/ATBench_raw.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_scores.csv
 ```

6. **Run Validation (T025a)**:
 ```bash
 python code/validation.py --drift data/processed/drift_scores.csv --ground_truth data/raw/ATBench_raw.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/us01_final_stats.json
 ```

## Running the Full Pipeline

To run the entire pipeline:
```bash
python code/main.py
```

## Validation

To validate only:
```bash
python code/main.py --validate-only
```

## Troubleshooting

- If you encounter memory issues, ensure you are using the `--streaming` flag for large datasets.
- If dataset fetch fails, check your network connection and Hugging Face access.
- For more detailed logs, add `--verbose` flag to any command.
