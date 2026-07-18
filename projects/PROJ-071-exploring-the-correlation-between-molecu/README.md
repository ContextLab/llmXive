# PROJ-071: Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

## Overview

This project investigates the correlation between molecular complexity metrics (TPSA, Rotatable Bond Count, MW, etc.) and degradation rates (half-lives) of FDA-approved drugs.

## Prerequisites

- Python 3.8+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-071-exploring-the-correlation-between-molecu
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Pipeline

The full pipeline can be executed by running:
```bash
python code/pipeline_runner.py
```

### Individual Scripts

- **Ingestion**: `python code/ingest.py`
- **Descriptors**: `python code/descriptors.py`
- **Standardization**: `python code/standardize.py`
- **Analysis**: `python code/analysis.py`
- **Visualization**: `python code/viz.py`
- **Report**: `python code/report.py`

## Data

- **Raw Data**: `data/raw/`
- **Processed Data**: `data/processed/`
- **Outputs**: `data/outputs/`

## Configuration

Configuration is managed via `config.yaml`. Adjust paths and settings as needed.

## Testing

Run tests with:
```bash
pytest tests/
```

## Reproducibility

All results are documented in `results_report.md` and `reproducibility_log.json`, including package versions, dataset URLs, and file hashes.

## License

[Insert License Information Here]
