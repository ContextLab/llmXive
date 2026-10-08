# llmXive: Code as Agent Harness Extension

**Project ID**: PROJ-953-llmxive-follow-up-extending-code-as-agen
**Version**: 0.1.0

## Overview

llmXive is an automated science pipeline designed to investigate the relationship between static code structural features and the necessity of dynamic execution for verifying software engineering tasks. This project extends the "Code as Agent Harness" to ingest real-world task datasets (SWE-bench, AgentBench), extract structural metrics via `tree-sitter`, and train predictive models to identify safe decision boundaries for skipping dynamic execution.

**Core Principles**:
- **Real Data Only**: All analysis is performed on genuine datasets; no synthetic data is used.
- **CPU-Only**: All models and data processing run on CPU to ensure reproducibility and accessibility.
- **Associational Framing**: Findings are explicitly framed as correlational, not causal.
- **Fail Loudly**: Data loaders raise exceptions on fetch failures rather than falling back to synthetic data.

## Project Structure

```
.
├── code/
│ ├── config/ # Configuration loading and validation
│ └── scripts/ # Pipeline execution scripts
│ ├── ingest.py # Dataset ingestion (SWE-bench, AgentBench)
│ ├── extract_features.py # Structural metric extraction
│ ├── train_model.py # Predictive model training & threshold analysis
│ └──... # (Other utility scripts)
├── data/
│ ├── raw/ # Ingested raw datasets (parquet)
│ ├── processed/ # Ground truth, features, and model reports
│ ├── graphs/ # Serialized dependency graphs
│ └── logs/ # Execution logs and sampling justifications
├── docs/
│ ├── README.md # This file
│ ├── quickstart.md # Step-by-step setup and execution guide
│ ├── usage_guide.md # Detailed pipeline usage and result interpretation
│ └── api_reference.md # API documentation for scripts
├── models/ # Trained model artifacts (.pkl)
├── tests/ # Unit, integration, and contract tests
├── contracts/ # JSON/YAML schemas for data validation
├── specs/ # Design documents and requirements
└── requirements.txt # Python dependencies
```

## Prerequisites

- **Python**: 3.11 or higher
- **OS**: Linux/macOS (recommended for Docker compatibility)
- **Memory**: Minimum 6GB RAM for streaming datasets
- **Disk**: ~15GB free space for datasets and artifacts

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-follow-up-extending-code-as-agen
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify installation**:
 ```bash
 python -c "import datasets; import tree_sitter; import sklearn; print('All dependencies installed successfully.')"
 ```

## CLI Usage Guide

The pipeline consists of three main stages, executed sequentially. Ensure you have completed the installation and configuration steps before running these commands.

### 1. Ingestion (`ingest.py`)

Downloads and parses task datasets from HuggingFace, generating raw parquet files and initial logs.

**Command**:
```bash
python code/scripts/ingest.py
```

**Arguments**:
- `--max-tasks`: Maximum number of tasks to ingest (default: 500). Used for sampling large datasets.
- `--datasets`: Comma-separated list of datasets to ingest (e.g., `swe_bench_lite,agent_bench`).
- `--output-dir`: Directory to store raw data (default: `data/raw`).

**Outputs**:
- `data/raw/swe_bench_subset.parquet`
- `data/raw/agent_bench_subset.parquet`
- `data/logs/ingest_sample_log.json` (logs sample size and limitations)

**Note**: This script will fail loudly if it cannot connect to HuggingFace or if the dataset fetch fails. No synthetic data is generated.

### 2. Feature Extraction (`extract_features.py`)

Loads the ground truth data (generated after baseline execution) and calculates structural metrics using `tree-sitter`.

**Command**:
```bash
python code/scripts/extract_features.py
```

**Arguments**:
- `--input-csv`: Path to `data/processed/ground_truth.csv`.
- `--output-csv`: Path to save features (default: `data/processed/features.csv`).
- `--graphs-dir`: Directory to save serialized dependency graphs (default: `data/graphs`).

**Outputs**:
- `data/processed/features.csv`: Contains `task_id`, `code_diff`, and structural metrics.
- `data/graphs/{task_id}.json`: Serialized dependency graphs for traceability.
- `data/logs/graph_mapping_audit.json`: Integrity verification of graph-to-code mapping.

**Note**: Tasks marked "Unparseable" in the ground truth are automatically filtered out.

### 3. Model Training (`train_model.py`)

Trains predictive models (Logistic Regression, Random Forest) and performs sensitivity analysis to identify safe thresholds for skipping dynamic execution.

**Command**:
```bash
python code/scripts/train_model.py
```

**Arguments**:
- `--input-csv`: Path to `data/processed/features.csv`.
- `--output-dir`: Directory to save models and reports (default: `models` and `data/processed`).
- `--thresholds`: Comma-separated list of thresholds to evaluate (default: `0.01,0.05,0.1`).
- `--seed`: Random seed for reproducibility (default: 42).

**Outputs**:
- `models/logistic_regression.pkl`, `models/random_forest.pkl`: Trained model artifacts.
- `models/decision_boundary.pkl`: Identified thresholds and weights.
- `data/processed/threshold_sweep.json`: FNR analysis for each threshold.
- `data/processed/model_report.json`: Final report including correlation coefficients and safety flags.

**Note**: The model is CPU-only. If the False Negative Rate (FNR) exceeds 0.1%, the model is flagged as "unsafe" in the report.

## Configuration

The pipeline uses environment variables for configuration. Create a `.env` file in the project root or set variables in your shell:

- `HF_DATASETS_CACHE`: Directory for HuggingFace dataset cache.
- `PROJECT_ROOT`: Absolute path to the project root (default: current directory).
- `MAX_WORKERS`: Number of parallel workers for data processing (default: 4).

## Running the Full Pipeline

For a complete end-to-end execution (including baseline dynamic execution), refer to the [Quickstart Guide](quickstart.md).

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- SWE-bench and AgentBench teams for providing open-source datasets.
- Tree-sitter for code parsing capabilities.
- scikit-learn for machine learning tools.