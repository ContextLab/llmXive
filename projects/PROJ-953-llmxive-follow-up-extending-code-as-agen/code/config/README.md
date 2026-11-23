# Configuration Module

This module provides a centralized configuration system for the llmXive pipeline.

## Usage

```python
from code.config import get_config, Config

# Get the global configuration
config = get_config()

# Access configuration values
print(config.project_root)
print(config.data_root)
print(config.timeout_seconds)

# Get dataset paths
swe_path = config.get_dataset_path("swe_bench")
```

## Environment Variables

The following environment variables can be used to configure the pipeline:

- `PROJECT_ROOT`: Override the project root directory
- `DATA_ROOT`: Override the data root directory
- `RAW_DATA_DIR`: Override the raw data directory
- `PROCESSED_DATA_DIR`: Override the processed data directory
- `GRAPHS_DIR`: Override the graphs directory
- `MODELS_DIR`: Override the models directory
- `CONTRACTS_DIR`: Override the contracts directory
- `STATE_DIR`: Override the state directory
- `DATASET_SWE_BENCH_PATH`: Path to the SWE-bench dataset
- `DATASET_AGENT_BENCH_PATH`: Path to the AgentBench dataset
- `DATASETS_JSON`: JSON string with additional dataset mappings
- `EXECUTION_TIMEOUT_SECONDS`: Timeout for baseline execution (default: 300)
- `MAX_WORKERS`: Maximum number of parallel workers (default: 4)
- `ENVIRONMENT`: Environment name (default: "development")

## Directory Structure

The configuration automatically creates and validates the following directories:

- `data/raw/`: Raw downloaded datasets
- `data/processed/`: Processed data artifacts
- `data/graphs/`: Dependency graph JSON files
- `models/`: Trained models and thresholds
- `contracts/`: YAML schema files
- `state/`: Project state tracking