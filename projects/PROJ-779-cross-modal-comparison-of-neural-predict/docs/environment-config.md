# Environment Configuration Guide

## Overview

This project uses environment configuration management to control all runtime settings. Configuration is loaded from a `.env` file with secure defaults.

## Setup

1. Copy the example file:
 ```bash
 cp.env.example.env
 ```

2. Edit `.env` to customize settings for your environment.

3. The configuration is automatically loaded when the pipeline runs.

## Configuration Keys

### Data Paths
- `DATA_ROOT`: Root directory for all data (default: `data`)
- `RAW_DATA_DIR`: Directory for raw downloaded data
- `PROCESSED_DATA_DIR`: Directory for preprocessed data
- `RESULTS_DIR`: Directory for analysis results
- `FIGURES_DIR`: Directory for generated figures

### Dataset Identifiers
- `AUDITORY_DATASET_ID`: OpenNeuro dataset ID for auditory data (default: `ds000246`)
- `VISUAL_DATASET_ID`: Dataset ID for visual data (default: `openneuro/ds000117`)
- `VISUAL_DATASET_VERSION`: Version tag for visual dataset (default: `r.0`)

### Processing Parameters
- `SAMPLING_RATE_THRESHOLD`: Minimum sampling rate in Hz (default: `500`)
- `MIN_ODDBALL_TRIALS`: Minimum oddball trials required (default: `100`)
- `MIN_STANDARD_TRIALS`: Minimum standard trials required (default: `300`)
- `BANDPASS_LOW`: Low-frequency cutoff for bandpass filter (default: `1.0`)
- `BANDPASS_HIGH`: High-frequency cutoff for bandpass filter (default: `40.0`)

### Analysis Parameters
- `AUDITORY_WINDOW_START`: Start of auditory analysis window (default: `0.05`)
- `AUDITORY_WINDOW_END`: End of auditory analysis window (default: `0.20`)
- `VISUAL_WINDOW_START`: Start of visual analysis window (default: `0.10`)
- `VISUAL_WINDOW_END`: End of visual analysis window (default: `0.30`)
- `LATENCY_THRESHOLD_MS`: Maximum allowed latency difference (default: `50`)
- `DICE_THRESHOLD`: Minimum Dice coefficient for source overlap (default: `0.6`)
- `TOST_ALPHA`: Alpha level for equivalence testing (default: `0.05`)

### Execution Parameters
- `RANDOM_SEED`: Random seed for reproducibility (default: `42`)
- `N_JOBS`: Number of parallel jobs (default: `1`)
- `MAX_MEMORY_GB`: Maximum memory in GB (default: `7`)
- `TIMEOUT_HOURS`: Maximum runtime in hours (default: `6`)

### Logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE`: Path to log file

## Programmatic Access

```python
from code.config.env_config import get_env_config

# Get configuration
config = get_env_config()

# Access values with type safety
sampling_rate = config.get_int("SAMPLING_RATE_THRESHOLD")
data_root = config.get_path("DATA_ROOT")
log_level = config.get("LOG_LEVEL")

# Get all configuration
all_config = config.get_dict()
```

## Validation

The configuration is automatically validated on load. Invalid values will raise a `ConfigError`:

- Sampling rate threshold must be >= 100 Hz
- Trial counts must be >= 10
- Time windows must be ordered correctly
- Dice threshold must be between 0.0 and 1.0
- TOST alpha must be between 0.0 and 1.0

## Reloading Configuration

To reload configuration from a new `.env` file:

```python
from code.config.env_config import reload_config

config = reload_config(Path("/path/to/new/.env"))
```

## Environment-Specific Configuration

For different environments (development, testing, production), create separate `.env` files:

- `.env.dev` - Development settings
- `.env.test` - Testing settings
- `.env.prod` - Production settings

Then load the appropriate file:

```python
config = get_env_config(Path(".env.dev"))
```