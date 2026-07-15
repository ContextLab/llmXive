# Configuration Guide for llmXive Project

This document explains how to configure environment variables for dataset paths and random seed management.

## Environment Variables

The project uses the following environment variables to control behavior:

### 1. Random Seed (`LLMXIVE_RANDOM_SEED`)
- **Purpose**: Ensures reproducibility of experiments by fixing random seeds for Python, NumPy, and PyTorch.
- **Default**: `42`
- **Example**: `export LLMXIVE_RANDOM_SEED=12345`

### 2. ImageNet Path (`LLMXIVE_IMAGENET_PATH`)
- **Purpose**: Specifies the directory where ImageNet validation data is stored or cached.
- **Default**: `data/imagenet_trace`
- **Note**: When using streaming from HuggingFace, this should point to a local cache directory.
- **Example**: `export LLMXIVE_IMAGENET_PATH=/mnt/datasets/imagenet`

### 3. Routing Cache Path (`LLMXIVE_ROUTING_CACHE_PATH`)
- **Purpose**: Directory for storing intermediate routing weight matrices and clustering results.
- **Default**: `data/routing_cache`
- **Example**: `export LLMXIVE_ROUTING_CACHE_PATH=/tmp/llmxive_cache`

### 4. Results Path (`LLMXIVE_RESULTS_PATH`)
- **Purpose**: Directory for storing benchmark results, statistical analysis, and final reports.
- **Default**: `data/results`
- **Example**: `export LLMXIVE_RESULTS_PATH=/outputs/llmxive_results`

## Setting Up Configuration

### Option 1: Using `.env` File
1. Copy `.env.example` to `.env`:
 ```bash
 cp code/.env.example code/.env
 ```
2. Edit `code/.env` with your desired values.
3. Load the environment variables:
 ```bash
 export $(grep -v '^#' code/.env | xargs)
 ```

### Option 2: Exporting in Shell
```bash
export LLMXIVE_RANDOM_SEED=42
export LLMXIVE_IMAGENET_PATH=data/imagenet_trace
export LLMXIVE_ROUTING_CACHE_PATH=data/routing_cache
export LLMXIVE_RESULTS_PATH=data/results
```

### Option 3: Programmatic Configuration
The `src/config.py` module provides helper functions:
```python
from src.config import set_seed, get_config_summary, ensure_directories_exist

# Set seed programmatically
set_seed(42)

# Get configuration summary
config = get_config_summary()
print(config)

# Ensure directories exist
ensure_directories_exist()
```

## Verification
Run the test suite to verify configuration is working:
```bash
pytest tests/unit/test_config.py -v
```

## Troubleshooting
- If paths are incorrect, check that environment variables are exported in the same shell session running the scripts.
- If random seeds are not reproducible, ensure `LLMXIVE_RANDOM_SEED` is set before importing any modules that use randomness.
- Use `get_config_summary()` to debug current configuration state.
