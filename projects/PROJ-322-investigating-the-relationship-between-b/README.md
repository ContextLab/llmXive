# Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury

## Overview
This project implements an automated science pipeline to analyze longitudinal resting-state fMRI data from mTBI patients. It investigates how changes in brain network topology (efficiency, modularity) correlate with cognitive recovery over time.

## Key Features
- **Automated Data Acquisition**: Downloads and preprocesses OpenNeuro datasets.
- **Graph Theory Analysis**: Computes Global/Local Efficiency and Modularity.
- **Statistical Modeling**: Linear Mixed-Effects models for longitudinal data.
- **Robustness Validation**: Permutation testing and sensitivity analysis.
- **Resource Constraints**: Enforces 6GB RAM and 6-hour runtime limits.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
### Quick Start
1. Ensure `data/raw/` is empty or contains valid OpenNeuro downloads.
2. Run the full pipeline:
 ```bash
 python code/data_ingestion.py
 python code/preprocessing.py
 python code/graph_metrics.py
 python code/statistical_model.py
 python code/robustness.py
 python code/sensitivity_analysis.py
 python code/analysis_report.py
 ```
3. Results will be saved in `data/results/`.

### Methodology Validation Mode
If real data is unavailable, set the environment variable `SYNTHETIC_MODE=true` to generate synthetic data for testing the pipeline logic.

## Project Structure
- `code/`: Python modules for data processing, analysis, and reporting.
- `data/`: Raw, processed, and result data files.
- `tests/`: Unit and integration tests.
- `docs/`: Architecture and process documentation.
- `specs/`: Feature specifications and requirements.

## Requirements
- Python 3.11+
- `nilearn`, `networkx`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `pyyaml`, `huggingface_hub`

## Compliance
- **Memory Limit**: ≤6GB (enforced by `memory_monitor.py`).
- **Runtime Limit**: ≤6 hours (enforced by `time_monitor.py`).
- **Data Integrity**: Uses real OpenNeuro data or flagged synthetic data only.

## License
[Project License]

## Contributing
See `docs/PROCESS.md` for the research methodology and execution order.