# Environment Configuration Guide

This document describes the environment variable management system for the
llmXive automated science pipeline.

## Overview

The `code/utils/env_config.py` module provides centralized management of:
- Data directory paths (raw, processed, results, models)
- Random seed for reproducibility
- Parallel processing settings
- Verbose logging flag

## Setup

### 1. Create `.env` File

Copy `.env.example` to `.env` in the project root:

```bash
cp.env.example.env
```

### 2. Configure Environment Variables

Edit `.env` to set your paths and preferences:

```env
# Project Root (optional, defaults to parent of code/)
PROJECT_ROOT=/path/to/project

# Data Directories
DATA_ROOT=data
DATA_RAW=data/raw
DATA_PROCESSED=data/processed
DATA_RESULTS=data/results
DATA_MODELS=data/models

# Random Seed (critical for reproducibility)
RANDOM_SEED=42

# Parallel Processing
N_JOBS=-1 # -1 = use all CPU cores

# Verbose Output
VERBOSE=false
```

## Usage in Code

### Basic Usage

```python
from utils.env_config import get_config

config = get_config()

# Access paths
data_raw = config.data_raw
data_processed = config.data_processed
random_seed = config.random_seed

# Get specific path by key
models_dir = config.get_path('data_models')
```

### Using in Scripts

```python
from utils.env_config import get_config
import numpy as np
import pandas as pd

def main():
 config = get_config()

 # Set random seed for reproducibility
 np.random.seed(config.random_seed)
 pd.options.mode.chained_assignment = None # Suppress warnings

 # Use paths
 input_file = config.data_raw / 'input.csv'
 output_file = config.data_processed / 'output.csv'

 # Process data
 df = pd.read_csv(input_file)
 #... processing...
 df.to_csv(output_file)

if __name__ == '__main__':
 main()
```

## Configuration Object Methods

### `get_path(key: str) -> Path`

Get a path by key name:

```python
config.get_path('data_raw') # Path to raw data directory
config.get_path('data_processed') # Path to processed data directory
config.get_path('data_results') # Path to results directory
config.get_path('data_models') # Path to models directory
config.get_path('specs') # Path to specifications directory
```

### `to_dict() -> Dict[str, Any]`

Convert configuration to dictionary:

```python
config_dict = config.to_dict()
```

### `save_to_json(path: Path) -> None`

Save configuration to JSON file:

```python
config.save_to_json(Path('config_backup.json'))
```

### `from_json(path: Path) -> EnvConfig`

Load configuration from JSON file:

```python
config = EnvConfig.from_json(Path('config_backup.json'))
```

## Error Handling

The `EnvConfigError` exception is raised when:
- Required directories don't exist
- Invalid path keys are requested
- Environment variables have invalid values

```python
from utils.env_config import get_config, EnvConfigError

try:
 config = get_config()
 invalid_path = config.get_path('nonexistent')
except EnvConfigError as e:
 print(f"Configuration error: {e}")
```

## Testing Configuration

Run the test suite to verify configuration:

```bash
pytest tests/test_env_config.py -v
```

## Best Practices

1. **Always set RANDOM_SEED**: Ensure reproducibility across runs
2. **Use environment variables for paths**: Makes deployment easier
3. **Validate directories exist**: The config class does this automatically
4. **Don't commit.env**: Add it to.gitignore
5. **Use.env.example as template**: Document required variables

## Command-Line Usage

The config module can be run directly to inspect current configuration:

```bash
python -m utils.env_config
```

Output as JSON:

```bash
python -m utils.env_config --json
```

## Integration with Other Modules

All pipeline modules should use `get_config()` to access paths and settings:

```python
# In code/01_ingest.py
from utils.env_config import get_config

config = get_config()
raw_data_path = config.data_raw / 'input.csv'
```

This ensures consistent path handling across the entire pipeline.