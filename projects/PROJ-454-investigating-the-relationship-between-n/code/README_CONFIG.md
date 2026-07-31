# Configuration Management Guide

## Overview

This project uses a centralized configuration system (`code/config.py`) to manage
all dataset URLs, thresholds, and environmental parameters. This ensures reproducibility
and makes it easy to adjust parameters without modifying code.

## Configuration Files

- `code/config.py`: Main configuration module with defaults and loader
- `code/.env.example`: Template for environment variables (copy to `.env`)
- `.env`: Actual environment file (git-ignored, create from `.env.example`)

## How to Configure

### 1. Copy the example file

```bash
cp code/.env.example code/.env
```

### 2. Edit `.env` with your values

Open `code/.env` and modify values as needed. For example:

```bash
# Change dataset IDs
OPENNEURO_DATASET_IDS=ds003104,ds000030

# Adjust SNR threshold
SNR_MIN_THRESHOLD_DB=5.0

# Modify resource limits
RAM_LIMIT_GB=7.0
```

### 3. Use in code

```python
from config import config, validate_config, load_config_from_env

# Validate configuration before running
validate_config()

# Get individual values
snr_threshold = config.get("SNR_MIN_THRESHOLD_DB")
dataset_ids = config.get_dataset_ids()

# Get grouped parameters
entropy_params = config.get_entropy_params()
eeg_params = config.get_eeg_params()
thresholds = config.get_thresholds()
```

## Configuration Priority

Values are loaded in this order (highest priority first):

1. **Environment variables** (e.g., `export SNR_MIN_THRESHOLD_DB=6.0`)
2. **`.env` file** (loaded automatically if present)
3. **Defaults in `CONFIG_DEFAULTS`** (in `config.py`)

## Key Configuration Groups

### Dataset Configuration
- `OPENNEURO_DATASET_IDS`: Comma-separated list of OpenNeuro dataset IDs
- `OPENNEURO_API_BASE_URL`: Base URL for OpenNeuro API

### Entropy Thresholds
- `ENTROPY_SAMPLE_M`: Embedding dimension for Sample Entropy
- `ENTROPY_SAMPLE_R_RATIO`: Tolerance for Sample Entropy (0.2 typical)
- `ENTROPY_APPROXIMATE_M`: Embedding dimension for Approximate Entropy
- `ENTROPY_APPROXIMATE_R_RATIO`: Tolerance for Approximate Entropy

### EEG Preprocessing
- `EEG_BANDPASS_LOW/HIGH`: Frequency range (1-45 Hz default)
- `EEG_NOTCH_FREQS`: Notch filter frequencies (50, 60 Hz)
- `EEG_MIN_VALID_DURATION`: Minimum seconds of valid EEG (60s)
- `EEG_MAX_CORRUPTED_PERCENT`: Max % corrupted segments (20%)

### Analysis Thresholds
- `SNR_MIN_THRESHOLD_DB`: Minimum SNR for inclusion (5 dB)
- `VIF_COLLINEARITY_THRESHOLD`: VIF threshold for multicollinearity (5.0)
- `FDR_ALPHA`: Significance level for FDR correction (0.05)
- `EFFECT_SIZE_MEDIUM`: Threshold for clinically meaningful effect (0.3)

### Resource Limits
- `RAM_LIMIT_GB`: Maximum RAM usage (7 GB)
- `DISK_LIMIT_GB`: Maximum disk usage (14 GB)

## Validation

Always validate configuration before running pipelines:

```python
from config import validate_config

try:
 validate_config()
 print("Configuration valid")
except ValueError as e:
 print(f"Configuration error: {e}")
 exit(1)
```

## Adding New Configuration Values

1. Add to `CONFIG_DEFAULTS` in `code/config.py`
2. Add to `code/.env.example`
3. Update this documentation
4. Add getter method if needed (e.g., `get_entropy_params()`)

## Environment Variables in CI/CD

For CI/CD environments, set variables directly:

```yaml
# Example GitHub Actions
env:
 OPENNEURO_DATASET_IDS: "ds003104"
 SNR_MIN_THRESHOLD_DB: "5.0"
 RAM_LIMIT_GB: "7.0"
```
