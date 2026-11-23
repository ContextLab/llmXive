# Environment Configuration Guide

## Overview

This project uses environment variables and a `.env` file for configuration management.
All sensitive data (API keys, passwords) and environment-specific settings should be
stored in the `.env` file and never committed to version control.

## Setup

1. **Copy the example file**:
 ```bash
 cp.env.example.env
 ```

2. **Edit `.env`** with your actual values:
 ```bash
 nano.env
 ```

3. **Required settings**:
 - `PROJECT_ROOT`: Absolute path to your project root
 - `RANDOM_SEED`: Integer seed for reproducibility (default: 42)

4. **Optional settings**:
 - `OPENNEURO_API_KEY`: For accessing OpenNeuro datasets
 - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: For S3 data storage
 - `FMRIPREP_CONTAINER`: Docker/Singularity container for fMRIPrep
 - `N_JOBS`: Number of parallel processing jobs (default: -1 for all cores)
 - `MOTION_THRESHOLD`: Framewise Displacement threshold (default: 0.5 mm)
 - `VIF_THRESHOLD`: Variance Inflation Factor threshold (default: 5.0)

## Directory Structure

The configuration automatically creates and manages these directories:

- `data/`: Raw and processed data files
- `figures/`: Generated plots and visualizations
- `logs/`: Application logs
- `contracts/`: Schema validation files

Subdirectories created:
- `data/preprocessing/`: fMRIPrep outputs
- `data/connectivity/`: Connectivity matrices
- `data/metrics/`: Graph metrics
- `data/merged/`: Merged datasets
- `figures/networks/`: Network diagrams
- `figures/plots/`: Statistical plots

## Programmatic Access

Use the configuration module in your code:

```python
from src.config.env_config import get_config, get_data_path, get_figures_path

# Get the configuration object
config = get_config()

# Access settings
print(f"Random seed: {config.random_seed}")
print(f"Motion threshold: {config.motion_threshold}")

# Get absolute paths
data_file = get_data_path("sub-01/fMRI.nii.gz")
figure_file = get_figures_path("networks/graph.png")

# Ensure directories exist
config.ensure_directories()
```

## Testing

For testing, you can override configuration:

```python
import os
from src.config.env_config import reset_config, get_config

# Set environment variables
os.environ['RANDOM_SEED'] = '999'
os.environ['MOTION_THRESHOLD'] = '0.3'

# Reset and reload configuration
reset_config()
config = get_config()

assert config.random_seed == 999
assert config.motion_threshold == 0.3
```

## Security Best Practices

1. **Never commit `.env`** to version control (it's in `.gitignore`)
2. Use `.env.example` to document required variables
3. Rotate API keys periodically
4. Use environment-specific `.env` files for development, staging, and production
5. Store secrets in a secure vault for production deployments
