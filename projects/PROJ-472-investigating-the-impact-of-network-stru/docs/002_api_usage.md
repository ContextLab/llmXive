# API Usage Guide

This document describes how to use the core modules of the `llmXive` pipeline.

## Configuration

All paths and hyperparameters are managed via `code/config.py`.

```python
from config import get_data_root, ensure_directories

# Get the root data directory
data_root = get_data_root()

# Ensure required directories exist
ensure_directories()
```

## Data Pipeline

### 1. Preprocessing (dMRI)
Converts raw tractography to adjacency matrices.

```python
from data.preprocess_dMRI import run_pipeline

# Run for a specific subject
run_pipeline(subject_id="sub-001", parcellation="HCP-MMP1.0")
```

### 2. Simulation (Synthetic EEG)
Generates neural time-series from structural graphs.

```python
from data.simulate_EEG import run_pipeline

# Run simulation (uses parameters from config.SIMULATION_PARAMS)
run_pipeline(subject_id="sub-001")
```
*Note: This task (T025) documents that `simulate_EEG.py` now logs parameters to `data/processed/simulation_metadata.json`.*

### 3. Data Storage
Unified interface for saving and loading processed data.

```python
from data.store import store_cleaned_eeg, load_connectome_matrix

# Store a time-series
store_cleaned_eeg(participant_id="sub-001", data=array, sample_rate=250)

# Load a connectome
matrix = load_connectome_matrix(participant_id="sub-001")
```

## Analysis

### 1. Network Metrics
Computes degree, clustering, and rich-club coefficients.

```python
from analysis.metrics import run_metrics_pipeline

# Computes all metrics and saves to data/processed/metrics.csv
run_metrics_pipeline()
```

### 2. Avalanche Detection
Detects spatiotemporal avalanches from EEG signals.

```python
from analysis.avalanches import run_avalanche_pipeline

# Detects avalanches using 75th percentile threshold
run_avalanche_pipeline()
```

### 3. Statistical Analysis
Performs correlation and robustness testing.

```python
from analysis.stats import run_correlation_analysis

# Runs Spearman correlation + permutation test
run_correlation_analysis()
```

### 4. Reporting
Generates the final results report.

```python
from analysis.report import main

# Generates `data/results/correlation_report.csv` or `null_result_report.md`
main()
```

## Error Handling

The pipeline uses a custom exception hierarchy defined in `utils/logger.py`.

- `ResearchError`: Base class.
- `DataLoadError`: Raised when real data fetch fails (e.g., OpenNeuro unavailable).
- `SimulationError`: Raised during Wilson-Cowan integration failure.
- `AnalysisError`: Raised during metric computation or fitting.

```python
from utils.logger import DataLoadError

try:
 from data.download import fetch_data
 fetch_data("ds004230")
except DataLoadError as e:
 print(f"Data acquisition failed: {e}")
 # Triggers fallback logic or pipeline halt
```

## Execution Order

1. **Setup**: `config.py`, `data_setup.py`.
2. **Data**: `download.py` -> `preprocess_dMRI.py` -> `simulate_EEG.py` (or `preprocess_EEG.py`).
3. **Store**: `store.py`.
4. **Analysis**: `metrics.py` -> `avalanches.py` -> `fitting.py` -> `stats.py`.
5. **Report**: `report.py`.

Run the full pipeline via `code/main.py`:
```bash
python code/main.py
```
