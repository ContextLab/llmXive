# API Usage Guide

This document provides usage examples for the core modules in the llmXive pipeline.

## Configuration

All path and hyperparameter settings are managed in `code/config.py`.

```python
from config import get_data_root, ensure_directories

# Get the root data directory
data_root = get_data_root()

# Ensure standard directory structure exists
ensure_directories()
```

## Data Pipeline

### Downloading Data

Use `code/data/download.py` to fetch dMRI data from OpenNeuro.

```python
from data.download import download_openneuro_subset

# Download subjects 001 to 010
subjects = [f"sub-{i:03d}" for i in range(1, 11)]
download_openneuro_subset(subjects, dataset="ds003813")
```

### Preprocessing dMRI

Convert tractography to adjacency matrices.

```python
from data.preprocess_dMRI import run_preprocessing_pipeline

# Process all downloaded subjects
run_preprocessing_pipeline(
 input_dir="data/raw/ds003813",
 output_dir="data/processed/connectomes",
 parcellation="HCP-MMP1.0"
)
```

### Simulating EEG

Generate synthetic EEG using Wilson-Cowan dynamics.

```python
from data.simulate_EEG import simulate_eeg_for_subject

# Simulate for a specific subject
eeg_data = simulate_eeg_for_subject(
 subject_id="sub-001",
 connectome_path="data/processed/connectomes/sub-001.csv",
 seed=42
)
```

## Analysis Module

### Network Metrics

Compute structural metrics using `code/analysis/metrics.py`.

```python
from analysis.metrics import run_metrics_pipeline

results = run_metrics_pipeline(
 connectome_dir="data/processed/connectomes",
 output_file="data/results/network_metrics.csv"
)
```

### Avalanche Detection

Detect neural avalanches from EEG signals.

```python
from analysis.avalanches import run_avalanche_pipeline

# Run detection for all subjects
run_avalanche_pipeline(
 eeg_dir="data/processed/eeg",
 output_file="data/results/avalanche_events.csv"
)
```

### Power-Law Fitting

Fit power-law models to avalanche size distributions.

```python
from analysis.fitting import run_fitting_pipeline

fitting_results = run_fitting_pipeline(
 avalanche_file="data/results/avalanche_events.csv",
 output_file="data/results/powerlaw_fit.csv"
)
```

## Statistical Analysis

### Correlation Analysis

Test associations between structure and dynamics.

```python
from analysis.stats import run_correlation_analysis

stats_report = run_correlation_analysis(
 metrics_file="data/results/network_metrics.csv",
 fitting_file="data/results/powerlaw_fit.csv",
 output_file="data/results/correlation_report.csv",
 n_permutations=1000
)
```

### Sensitivity Analysis

Perform threshold sensitivity sweeps.

```python
from analysis.sensitivity import run_sensitivity_pipeline

sensitivity_report = run_sensitivity_pipeline(
 eeg_dir="data/processed/eeg",
 threshold_range=[1.5, 2.0, 2.5, 3.0],
 output_file="data/results/sensitivity_analysis.csv"
)
```

## Logging and Error Handling

The project uses a structured logger defined in `code/utils/logger.py`.

```python
from utils.logger import get_logger

logger = get_logger(__name__)

try:
 # Risky operation
 result = risky_function()
except Exception as e:
 logger.error("Operation failed", exc_info=True)
 raise
```

## Environment Configuration

Load environment variables using `code/utils/env_config.py`.

```python
from utils.env_config import setup_env_config

config = setup_env_config()
print(f"Data root: {config['data_root']}")
```
