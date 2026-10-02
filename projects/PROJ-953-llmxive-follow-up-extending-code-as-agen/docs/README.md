# llmXive: Code as Agent Harness Extension

A research pipeline for analyzing code complexity and predicting the necessity of dynamic execution for software engineering tasks. This project ingests datasets from SWE-bench and AgentBench, extracts structural features using tree-sitter, and trains predictive models to identify safe thresholds for skipping dynamic validation.

## Project Structure

```
.
├── code/
│ ├── config/
│ │ └── loader.py # Configuration management
│ └── scripts/
│ ├── ingest.py # Dataset ingestion (SWE-bench/AgentBench)
│ ├── baseline_runner.py # Dynamic execution baseline
│ ├── extract_features.py# Structural feature extraction
│ ├── train_model.py # Predictive model training
│ └──... # Other pipeline scripts
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Intermediate and final CSV/JSON artifacts
│ └── graphs/ # Serialized dependency graphs
├── tests/
│ ├── unit/ # Unit tests
│ └── contract/ # Contract tests
├── docs/
│ ├── README.md # This file
│ ├── quickstart.md # Setup and run instructions
│ ├── usage_guide.md # Detailed pipeline usage
│ └── api_reference.md # API documentation
├── models/ # Trained model artifacts
├── contracts/ # YAML schemas for validation
└── requirements.txt # Python dependencies
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-code-as-agen
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

## Quick Start

For a complete guide on setting up the environment, downloading data, and running the full pipeline, please refer to the [Quickstart Guide](quickstart.md).

### High-Level Workflow

1. **Ingest Data**: Download and parse tasks from SWE-bench and AgentBench.
2. **Run Baseline**: Execute tasks in a controlled environment to determine ground truth.
3. **Extract Features**: Analyze code structure to compute metrics like complexity and dependency depth.
4. **Train Model**: Train a classifier to predict execution outcomes based on structural features.
5. **Analyze Thresholds**: Determine safe decision boundaries for skipping dynamic execution.

## CLI Usage

The pipeline consists of several scripts located in `code/scripts/`. Each script is executable via the command line.

### 1. Ingest Data

Downloads datasets and generates the initial ground truth CSV.

```bash
python code/scripts/ingest.py
```

**Outputs**:
- `data/raw/swe_bench_subset.parquet`
- `data/raw/agentbench_subset.parquet`
- `data/processed/ground_truth.csv` (initial)

### 2. Run Baseline (Dynamic Execution)

Executes tasks in a virtual environment to verify pass/fail status.

```bash
python code/scripts/baseline_runner.py
```

**Outputs**:
- `data/processed/raw_outcomes.json`
- Updates `data/processed/ground_truth.csv` with `dynamic_execution_outcome`

### 3. Extract Features

Parses code and calculates structural metrics.

```bash
python code/scripts/extract_features.py
```

**Outputs**:
- `data/graphs/{task_id}.json` (Dependency graphs)
- `data/processed/features.csv` (Merged with ground truth)

### 4. Train Model

Trains predictive models and performs sensitivity analysis.

```bash
python code/scripts/train_model.py
```

**Outputs**:
- `models/logistic_regression.pkl`
- `models/random_forest.pkl`
- `data/processed/threshold_sweep.json`
- `data/processed/model_report.json`

## Configuration

Configuration is managed via `code/config/loader.py`. Ensure environment variables or a config file are set up as described in the [Usage Guide](usage_guide.md).

## License

This project is for research purposes. See the LICENSE file for details.
