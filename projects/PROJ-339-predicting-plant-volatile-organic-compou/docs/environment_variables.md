# Environment Variable Configuration Guide

This document describes the environment variables used by the llmXive pipeline
for managing data paths, random seeds, and other critical runtime parameters.

## Setup

1. Copy `.env.example` to `.env` in the project root:
 ```bash
 cp.env.example.env
 ```

2. Edit `.env` to customize your configuration.

3. The pipeline automatically loads `.env` when importing `utils.env_config`.

## Configuration Variables

### Data Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_ROOT` | `./data` | Root directory for all project data |
| `QUERY_LOG_PATH` | `{DATA_ROOT}/raw/query_log.json` | Path to NCBI/Metabolomics query log |
| `SYNTHETIC_DATA_PATH` | `{DATA_ROOT}/raw/synthetic_arabidopsis_v1.csv` | Path to synthetic dataset |
| `MERGED_DATASET_PATH` | `{DATA_ROOT}/processed/merged_dataset.csv` | Path to merged genomic/VOC data |
| `MODEL_METRICS_PATH` | `{DATA_ROOT}/results/model_metrics.json` | Path to model performance metrics |
| `MODEL_ARTIFACT_PATH` | `{DATA_ROOT}/models/random_forest.pkl` | Path to trained model artifact |
| `INTERPRETATION_REPORT_PATH` | `{DATA_ROOT}/results/interpretation_report.json` | Path to feature importance report |
| `FEATURE_IMPORTANCE_PVALUES_PATH` | `{DATA_ROOT}/results/feature_importance_pvalues.json` | Path to corrected p-values |
| `SHAP_PLOT_PATH` | `{DATA_ROOT}/results/shap_summary.png` | Path to SHAP visualization |
| `VALIDATION_REPORT_PATH` | `{DATA_ROOT}/results/data_validation_report.json` | Path to data validation report |
| `STABILITY_METRICS_PATH` | `{DATA_ROOT}/results/stability_metrics.json` | Path to feature stability metrics |
| `OVERLAP_REPORT_PATH` | `{DATA_ROOT}/results/overlap_report.json` | Path to gene family overlap report |
| `PERF_METRICS_PATH` | `{DATA_ROOT}/results/perf_metrics.json` | Path to performance metrics |

### Reproducibility

| Variable | Default | Description |
|----------|---------|-------------|
| `RANDOM_SEED` | `42` | Integer seed for reproducible random number generation |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |

### API Keys (Optional)

If querying external databases directly, you may set:

| Variable | Description |
|----------|-------------|
| `NCBI_API_KEY` | NCBI E-utilities API key |
| `METABOLOMICS_WORKBENCH_TOKEN` | Metabolomics Workbench authentication token |

## Programmatic Access

Use the `EnvConfig` class to access configuration in your code:

```python
from utils.env_config import get_config

config = get_config()

# Access paths
data_root = config.data_root
merged_path = config.merged_dataset_path

# Access seed
seed = config.seed

# Validate directories
config.validate()

# Export as dictionary
config_dict = config.to_dict()

# Export as JSON
config_json = config.to_json()
```

## Validation

The `validate()` method ensures all required directories exist and are writable:

```python
from utils.env_config import get_config, EnvConfigError

try:
 config = get_config()
 config.validate()
except EnvConfigError as e:
 print(f"Configuration error: {e}")
 # Handle error (e.g., create missing directories, fix permissions)
```

## Testing Configuration

For testing, you can reset the configuration singleton:

```python
from utils.env_config import get_config, reset_config
import os

# Set test-specific environment variables
os.environ["RANDOM_SEED"] = "999"

# Reset singleton to pick up new values
reset_config()
config = get_config()

assert config.seed == 999
```

## Best Practices

1. **Never commit `.env`**: It contains sensitive paths and potentially API keys.
2. **Use `DATA_ROOT`**: Always reference data relative to `DATA_ROOT` for portability.
3. **Set `RANDOM_SEED`**: Ensure reproducibility across runs and environments.
4. **Validate early**: Call `config.validate()` at the start of long-running scripts.
5. **Log configuration**: Print `config.to_json()` at startup for debugging.