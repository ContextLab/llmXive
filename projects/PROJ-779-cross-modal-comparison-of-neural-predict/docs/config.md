# Configuration Management

This document describes the configuration management system for the llmXive pipeline.

## Overview

The pipeline uses a combination of environment variables and a `.env` file for configuration. This allows for:
- Easy local development via `.env`
- Secure CI/CD configuration via environment variables
- Default values for optional settings

## Files

- `.env`: Local environment configuration (git-ignored). Copy from `.env.example`.
- `.env.example`: Template for required configuration keys.
- `code/config_loader.py`: Module responsible for loading and managing configuration.

## Usage

### Loading Configuration

The configuration is loaded automatically when `code/config_loader` is imported:

```python
from code.config_loader import load, get_config_value

# Load configuration (returns dict)
config = load()

# Get a specific value
log_level = get_config_value("LOG_LEVEL", default="INFO")
```

### Configuration Keys

| Key | Description | Default |
|-----|-------------|---------|
| `OPENNEURO_API_KEY` | API key for OpenNeuro access (if required) | `""` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DATA_ROOT` | Root directory for data | `data` |
| `CODE_ROOT` | Root directory for code | `code` |
| `RESULTS_ROOT` | Root directory for results | `data/results` |
| `PROCESSED_ROOT` | Root directory for processed data | `data/processed` |
| `FIGURES_ROOT` | Root directory for figures | `figures` |
| `RANDOM_SEED` | Random seed for reproducibility | `42` |
| `MAX_WORKERS` | Maximum parallel workers | `1` |

## Verification

To verify configuration loading:

```bash
python -c "from code.config_loader import load; load()"
```

This should execute without errors and log any warnings about missing files.