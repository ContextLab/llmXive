# API Usage Guide

## Overview
This document provides usage examples for the core modules in the `code/` directory.

## Configuration

### `code/config.py`
Central configuration for paths, seeds, and hyperparameters.

```python
from config import get_data_root, ensure_directories

data_root = get_data_root()
ensure_directories() # Creates data/raw, data/processed, data/results
```

**Key Parameters**:
- `SIMULATION_PARAMS`: Wilson-Cowan equation parameters
- `SEED`: Random seed for reproducibility
- `DATA_PATHS`: Directory structure configuration

## Data Pipeline

### Downloading Data
```python
from data.download import fetch_dMRI_data

# Fetches ds004230, falls back to ds004503/HCP-Lifespan
subject_ids = fetch_dMRI_data(output_dir="data/raw/dMRI")
```

### Preprocessing dMRI
```python
from data.preprocess_dMRI import run_preprocessing_for_subject

# Converts.tck to adjacency matrix
matrix_path = run_preprocessing_for_subject(
 subject_id="sub-01",
 tractography_path="data/raw/dMRI/sub-01.trk",
 parcellation_path="data/raw/parcellation/HCP-MMP1.0.nii.gz"
)
```

### Simulating EEG (Primary Path)
```python
from data.simulate_EEG import simulate_eeg_for_subject

# Generates synthetic EEG from structural connectome
eeg_data = simulate_eeg_for_subject(
 participant_id="sub-01",
 connectome_matrix=matrix,
 seed=42
)
# Outputs: data/processed/eeg/sub-01_eeg.npy
```

## Analysis

### Computing Network Metrics
```python
from analysis.metrics import run_metrics_pipeline

# Computes degree, clustering, rich-club coefficients
metrics = run_metrics_pipeline(
 connectome_dir="data/processed/connectomes",
 output_path="data/results/network_metrics.csv"
)
```

### Detecting Avalanches
```python
from analysis.avalanches import run_avalanche_pipeline

# Detects avalanches from EEG time series
avalanches = run_avalanche_pipeline(
 eeg_dir="data/processed/eeg",
 threshold_percentile=75,
 output_path="data/results/avalanche_records.jsonl"
)
```

### Power-Law Fitting
```python
from analysis.fitting import run_fitting_pipeline

# Fits power-law models to avalanche size distributions
results = run_fitting_pipeline(
 avalanche_file="data/results/avalanche_records.jsonl",
 output_path="data/results/powerlaw_fits.csv"
)
```

### Statistical Association
```python
from analysis.stats import run_correlation_analysis

# Computes Spearman correlations between structure and dynamics
analysis = run_correlation_analysis(
 metrics_file="data/results/network_metrics.csv",
 fitting_file="data/results/powerlaw_fits.csv",
 output_path="data/results/correlation_report.csv"
)
```

## Error Handling

All modules use custom exceptions defined in `utils/logger.py`:
- `DataLoadError`: Raised when data fetch fails
- `SimulationError`: Raised during Wilson-Cowan integration
- `AnalysisError`: Raised during metric computation or fitting

```python
from utils.logger import DataLoadError, handle_exceptions

@handle_exceptions
def safe_data_load():
 # Will catch and log DataLoadError
 pass
```

## Reproducibility

### Logging
All pipelines log to `logs/pipeline.log` with structured JSON format.
Key fields: `timestamp`, `level`, `module`, `message`, `traceback`.

### Metadata
Simulation parameters are saved to `data/processed/simulation_metadata.json`:
```json
{
 "participant_id": "sub-01",
 "seed": 42,
 "wilson_cowan_params": {
 "connection_strength": 1.5,
 "time_constant": 10.0
 },
 "timestamp": "2024-01-01T00:00:00Z"
}
```

### Checksums
Data integrity verified via `utils/data_setup.py`:
```python
from utils.data_setup import verify_file_integrity

is_valid = verify_file_integrity(
 file_path="data/processed/connectomes/sub-01.npy",
 expected_checksum="abc123..."
)
```
