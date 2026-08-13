# Quickstart Guide

## Overview

This project implements a zero-shot drift detection system for AI agent logs,
following the AgentDoG methodology. The system builds taxonomy centroids,
computes drift scores, and validates results against human annotations.

## Prerequisites

- Python 3.11+
- pip
- Access to Hugging Face datasets

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black ruff
```

## Directory Structure

```
projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/
├── code/ # Source code
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data and outputs
│ └── test/ # Test fixtures
├── specs/ # Specification documents
├── docs/ # Documentation
└── tests/ # Test suite
```

## Running the Pipeline

### 1. Build Taxonomy Centroids

First, ensure the taxonomy data is available at `data/processed/taxonomy_agentdog.json`.
Then run:

```bash
python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json
```

This command:
- Loads the taxonomy from the configured path
- Builds centroid embeddings using `all-MiniLM-L6-v2`
- Saves centroids to `data/processed/taxonomy_centroids.json`

### 2. Run Drift Scoring

```bash
python -m code.drift_scoring \
 --input data/raw/atbench.parquet \
 --taxonomy data/processed/taxonomy_centroids.json \
 --output data/processed/drift_results.csv
```

### 3. Run Validation

```bash
python -m code.validation \
 --drift data/processed/drift_results.csv \
 --ground_truth data/raw/atbench.parquet \
 --annotations data/processed/gold_standard_proxy.csv \
 --output data/processed/validation_report.json
```

### 4. Run Full Pipeline

For end-to-end execution:

```bash
python code/main.py --validate
```

## Configuration

Edit `code/config.py` to modify:
- `RANDOM_SEED`: Random seed for reproducibility
- `MAX_RAM_GB`: Maximum RAM limit (default: 7 GB)
- `BATCH_SIZE`: Batch size for encoding (default: 64)

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=code --cov-report=html
```

## Data Sources

- **ATBench**: `AI45Research/ATBench` - Adversarial testing dataset
- **Taxonomy**: `AgentDoG/safety-taxonomy` - Safety taxonomy from AgentDoG paper
- **Agent Logs**: `mlfoundations/agent_logs` - Large-scale agent logs

## Output Files

- `data/processed/taxonomy_centroids.json`: Centroid embeddings for each category
- `data/processed/drift_results.csv`: Drift scores for each log
- `data/processed/validation_report.json`: Statistical validation results
- `data/processed/us01_final_stats.json`: US-01 validation statistics
