# llmXive: Code as Agent Harness Extension

An automated science pipeline for evaluating code complexity and predicting the necessity of dynamic execution for software engineering tasks. This project ingests datasets from SWE-bench and AgentBench, extracts structural features using `tree-sitter`, and trains CPU-only predictive models to identify safe thresholds for skipping dynamic execution.

## Overview

The llmXive pipeline follows a strict three-phase process:
1. **Ingestion & Ground Truth**: Download real datasets and establish ground truth via full-environment re-execution.
2. **Feature Extraction**: Parse code artifacts into dependency graphs and calculate structural metrics (cyclomatic complexity, semantic score, etc.).
3. **Predictive Modeling**: Train models to predict execution outcomes based on structural features, identifying thresholds where dynamic execution can be safely skipped.

## Prerequisites

- Python 3.11+
- pip (package manager)
- Access to HuggingFace Hub (for dataset download)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```text
.
├── code/ # Source code
│ ├── config/ # Configuration loaders
│ └── scripts/ # Pipeline execution scripts
├── data/ # Data artifacts
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Intermediate and final CSV/JSON files
│ └── graphs/ # Serialized dependency graphs
├── docs/ # Documentation
├── tests/ # Unit and integration tests
├── models/ # Trained model artifacts
└── requirements.txt # Python dependencies
```

## CLI Usage Guide

The pipeline is executed via Python scripts located in `code/scripts/`.

### 1. Ingest Data
Downloads SWE-bench and AgentBench subsets and generates the initial ground truth CSV.
```bash
python code/scripts/ingest.py
```
**Output**: `data/processed/ground_truth.csv`, `data/raw/swe_bench_subset.parquet`, `data/raw/agentbench_subset.parquet`

### 2. Extract Features
Parses code diffs, builds dependency graphs, and calculates structural metrics.
```bash
python code/scripts/extract_features.py
```
**Output**: `data/graphs/{task_id}.json`, intermediate metrics in `data/processed/`

### 3. Finalize Features
Merges ground truth with calculated metrics into a single feature set.
```bash
python code/scripts/generate_features.py
```
**Output**: `data/processed/features.csv`

### 4. Train Model
Trains Logistic Regression and Random Forest models, performs sensitivity analysis, and identifies decision thresholds.
```bash
python code/scripts/train_model.py
```
**Output**: `models/logistic_regression.pkl`, `models/random_forest.pkl`, `data/processed/threshold_sweep.json`, `data/processed/model_report.json`

### 5. Validate Artifacts
Verifies the integrity and checksums of all generated artifacts.
```bash
python code/scripts/checksum_artifacts.py
```

## Important Constraints

- **CPU Only**: All models and data processing must run on CPU. The pipeline explicitly checks for and fails if GPU/CUDA is detected.
- **Real Data Only**: Synthetic data generation is strictly prohibited. The pipeline will fail loudly if it cannot fetch real data from HuggingFace.
- **Timeout Handling**: Tasks exceeding the configured timeout (default 600s) are explicitly marked as "Timeout/Fail", not skipped.

## License

(Add license information here)
