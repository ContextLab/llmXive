# Quickstart Guide

This guide provides the steps to set up, run, and validate the llmXive project.

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)
- **Dependencies**: `networkx`, `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pyarrow`, `datasets`, `memory-profiler`, `pytest`, `ruff`, `black`

## Setup

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd PROJ-854-llmxive-follow-up-extending-sciatlas-a-l/code
 ```

2. **Create and activate virtual environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -e.
 ```

## Run

The pipeline can be executed step-by-step or fully.

### 1. Ingest Data (T012, T016)
Fetches OpenAlex data, builds the graph, assigns clusters, and saves `subgraph_with_clusters.parquet`.
```bash
python code/scripts/save_graph_pipeline.py --target-size 1000
```
*Or with a specific seed node:*
```bash
python code/scripts/save_graph_pipeline.py --target-size 1000 --seed-node-id "W23456789"
```

### 2. Run Embeddings & Novelty (T020, T021, T022)
Generates embeddings, performs K-Means clustering, and calculates novelty scores.
```bash
python code/scripts/run_novelty_calculation.py
```

### 3. Save Final Dataset (T024)
Merges graph data with novelty scores and saves `final_analysis_dataset.parquet`.
```bash
python code/scripts/save_final_dataset.py
```

### 4. Run Statistical Analysis (T026-T030)
Performs correlation, regression, and generates reports.
```bash
python code/scripts/save_statistical_metrics.py
```

### 5. Generate Report (T029)
Creates the final markdown report.
```bash
python code/scripts/generate_analysis_report.py
```

### Full Pipeline
To run the entire pipeline from ingestion to report:
```bash
python -m src.cli.main --step ingest --sample-size 1000
python -m src.cli.main --step embeddings
python -m src.cli.main --step analysis
python -m src.cli.main --step report
```
*Note: The CLI commands above are placeholders if the CLI module is not fully implemented. Use the script commands for guaranteed execution.*

## Validation

Run the validation script to check artifacts and hashes.
```bash
python code/scripts/run_validation.py
```

## Expected Outputs

- `data/processed/subgraph_with_clusters.parquet` (T016)
- `data/processed/final_analysis_dataset.parquet` (T024)
- `artifacts/results/analysis_report.md` (T029)
- `artifacts/results/statistical_metrics.json` (T030)
- `state/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l.yaml` (State file with hashes)
