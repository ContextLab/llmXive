# Environment Configuration Management

## Overview

This project uses environment variables for configuration management, allowing flexible deployment across different environments (development, testing, production) without code changes.

## Configuration Loading

Configuration is loaded from a `.env` file in the project root, with fallback to sensible defaults defined in `code/config/env_config.py`.

### How it Works

1. On startup, `get_env_config()` is called
2. It looks for a `.env` file in the project root
3. If found, variables are loaded using `python-dotenv`
4. Any missing variables fall back to defaults
5. Critical values are validated (sampling rate, trial counts, log level)

## Configuration Keys

### Paths
- `PROJECT_ROOT`: Root directory of the project
- `DATA_DIR`: Directory for raw and processed data
- `CODE_DIR`: Directory containing source code
- `RESULTS_DIR`: Directory for analysis results
- `PROCESSED_DIR`: Directory for preprocessed data artifacts

### Logging
- `LOG_LEVEL`: One of DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_FILE`: Path to log file

### Data Processing
- `SAMPLING_RATE_THRESHOLD`: Minimum acceptable sampling rate (Hz)
- `TRIAL_ODDBALL_MIN`: Minimum oddball trials required
- `TRIAL_STANDARD_MIN`: Minimum standard trials required
- `TIME_WINDOW_START`: Start of analysis window (seconds)
- `TIME_WINDOW_END`: End of analysis window (seconds)

### Analysis
- `RANDOM_SEED`: Random seed for reproducibility
- `N_PERMUTATIONS`: Number of permutations for statistical tests

### ICA
- `ICA_MAX_ITER`: Maximum iterations for ICA
- `ICA_METHOD`: ICA algorithm (picard, fastica, infomax)

### Source Localization
- `HEAD_MODEL`: Head model template (icbm152)
- `SOURCE_SPACE_RES`: Source space resolution (mm)

## Usage

### Setting Up

1. Copy `.env.example` to `.env`:
 ```bash
 cp.env.example.env
 ```

2. Edit `.env` to customize values:
 ```bash
 LOG_LEVEL=DEBUG
 SAMPLING_RATE_THRESHOLD=1000
 ```

### Accessing Configuration

```python
from code.config import get_env_config

config = get_env_config()

# Get string value
log_level = config.get("LOG_LEVEL")

# Get integer value
seed = config.get_int("RANDOM_SEED")

# Get float value
time_start = config.get_float("TIME_WINDOW_START")

# Get boolean value
debug = config.get_bool("DEBUG_MODE")

# Get Path object
data_dir = config.get_path("DATA_DIR")

# Get as dictionary
all_config = config.to_dict()
```

### Programmatic Override

For testing or specific use cases:
```python
from code.config import reload_config

# Load from specific path
config = reload_config("/path/to/custom/.env")
```

## Validation

The configuration manager validates:
- Sampling rate threshold must be a positive integer
- Trial counts must be positive integers
- Log level must be a valid logging level

Invalid configurations raise `ConfigError` with descriptive messages.

## Best Practices

1. **Never commit `.env` files** with sensitive data to version control
2. **Use `.env.example`** as a template for required variables
3. **Validate early**: Call `get_env_config()` at module import or entry point
4. **Use typed getters**: Prefer `get_int()`, `get_float()` over raw `get()`
5. **Document changes**: Update this file when adding new configuration keys

## Error Handling

Configuration errors raise `code.config.ConfigError`. Catch these at the application entry point:

```python
from code.config import get_env_config, ConfigError

try:
 config = get_env_config()
except ConfigError as e:
 print(f"Configuration error: {e}")
 exit(1)
```
