# API Usage Guide

This document provides detailed examples of how to use the core modules in the `llmXive` pipeline.

## 1. Configuration (`code/config.py`)

All configuration is centralized here.

```python
from config import get_data_root, SIMULATION_PARAMS

# Get the root data directory
data_root = get_data_root()

# Access simulation parameters
params = SIMULATION_PARAMS
tau = params['tau']
sigma = params['sigma']
```

## 2. Data Loading & Simulation (`code/data/`)

### Simulating EEG (Primary Path)

```python
from data.simulate_EEG import WilsonCowanSimulator, load_connectome, simulate_eeg_for_subject

# Load a connectome matrix for a subject
subject_id = "sub-001"
matrix = load_connectome(subject_id)

# Initialize the simulator
simulator = WilsonCowanSimulator(
 dt=0.1,
 T=1000,
 seed=42
)

# Run simulation
eeg_signal = simulate_eeg_for_subject(matrix, simulator)

# Save to store
from data.store import store_cleaned_eeg
store_cleaned_eeg(subject_id, eeg_signal, "data/processed/eeg/")
```

### Downloading Real Data (Probe Path)

```python
from data.download import download_dMRI_data

# Attempt to download from OpenNeuro
try:
 download_dMRI_data("ds004230")
except Exception as e:
 print(f"Data unavailable: {e}")
```

## 3. Analysis (`code/analysis/`)

### Computing Network Metrics

```python
from analysis.metrics import run_metrics_pipeline

# Run for all subjects in the processed directory
metrics_df = run_metrics_pipeline(
 input_dir="data/processed/connectomes/",
 output_path="data/results/metrics.csv"
)
```

### Detecting Avalanches

```python
from analysis.avalanches import run_avalanche_pipeline

# Detect avalanches in simulated or real EEG
results = run_avalanche_pipeline(
 eeg_dir="data/processed/eeg/",
 threshold_percentile=75.0
)
```

### Power-Law Fitting

```python
from analysis.fitting import run_fitting_pipeline

# Fit power-law models to avalanche sizes
fitting_results = run_fitting_pipeline(
 avalanche_data_dir="data/results/avalanches/",
 output_path="data/results/fitting_results.json"
)
```

### Statistical Association

```python
from analysis.stats import run_correlation_analysis

# Correlate structural metrics with avalanche exponents
report = run_correlation_analysis(
 metrics_file="data/results/metrics.csv",
 fitting_file="data/results/fitting_results.json",
 output_path="data/results/correlation_report.csv"
)
```

## 4. Error Handling

The pipeline uses custom exceptions defined in `code/utils/logger.py`.

- `DataLoadError`: Raised when real data cannot be fetched.
- `SimulationError`: Raised if the Wilson-Cowan simulation diverges.
- `AnalysisError`: Raised if metric calculation fails (e.g., disconnected graph).

```python
from utils.logger import DataLoadError

try:
 load_real_data()
except DataLoadError as e:
 # Trigger simulation path
 run_simulation_path()
```

## 5. Output Formats

- **CSV**: Used for metrics and correlation reports.
 - Columns: `subject_id`, `degree`, `clustering`, `rich_club`, `avalanche_exponent`, `p_value`.
- **JSON**: Used for fitting results and QC status.
- **NPY**: Used for large matrices (connectomes).
- **FIF/CVS**: Used for EEG time-series.
