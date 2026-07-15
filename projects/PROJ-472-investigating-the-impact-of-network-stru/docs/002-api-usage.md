# API Usage Guide

This document provides examples of how to use the core modules in the `llmXive` pipeline. It assumes the project root is the current working directory.

## Prerequisites

Ensure the environment is set up and dependencies are installed:

```bash
pip install -r code/requirements.txt
```

## 1. Configuration

Access global configuration parameters (paths, seeds, hyperparameters).

```python
from config import get_data_root, ensure_directories

# Get the root data directory
data_root = get_data_root()
print(f"Data root: {data_root}")

# Ensure required directories exist
ensure_directories()
```

## 2. Data Pipeline

### Downloading Data

Fetch dMRI data for specific subjects.

```python
from data.download import run_pipeline

# Run for a subset of subjects
subjects = ["sub-001", "sub-002", "sub-003"]
run_pipeline(subjects=subjects)
```

### Preprocessing

Convert tractography to adjacency matrices.

```python
from data.preprocess_dMRI import run_pipeline

# Preprocess downloaded data
run_pipeline()
```

### Simulation

Generate synthetic EEG from structural connectomes.

```python
from data.simulate_EEG import main

# Run simulation for all processed subjects
main()
```

### Quality Control

Check data quality and graph connectivity.

```python
from data.quality_control import main

# Run QC checks
main()
```

### Storage

Persist processed data.

```python
from data.store import run_store_pipeline

# Store connectomes and EEG
run_store_pipeline()
```

## 3. Analysis

### Network Metrics

Compute structural network metrics.

```python
from analysis.metrics import main

# Compute degree, clustering, rich-club
main()
```

### Avalanche Detection

Detect neural avalanches from EEG.

```python
from analysis.avalanches import main

# Detect avalanches and save results
main()
```

### Power-Law Fitting

Fit power-law models to avalanche size distributions.

```python
from analysis.fitting import main

# Fit models and compare (power-law vs exponential)
main()
```

### Statistical Analysis

Perform correlation analysis and robustness checks.

```python
from analysis.stats import main

# Run Spearman correlation, permutation tests, VIF
main()
```

### Sensitivity Analysis

Sweep threshold multipliers.

```python
from analysis.sensitivity import main

# Run sensitivity sweep
main()
```

## 4. Reporting

### Export Metrics

Generate a CSV of all metrics.

```python
from analysis.export_metrics import main

# Export to data/results/metrics_export.csv
main()
```

### Generate Report

Create the final associational report.

```python
from analysis.report import main

# Generate data/results/correlation_report.csv
main()
```

## 5. Orchestration

Run the full pipeline via the main entry point.

```bash
python code/main.py --config config.yaml
```

Or programmatically:

```python
from main import main

main()
```

## Error Handling

All modules use the centralized logger.

```python
from utils.logger import get_logger, DataLoadError

logger = get_logger(__name__)

try:
 # Some operation
 pass
except DataLoadError as e:
 logger.error(f"Failed to load data: {e}")
 raise
```

## Data Models

Import data classes for type hinting or direct usage.

```python
from data.models import Participant, StructuralConnectome, AvalancheRecord

# Example usage
p = Participant(subject_id="sub-001", qc_passed=True)
```
