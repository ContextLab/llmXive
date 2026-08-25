# PROJ-065: Assessing the Generalizability of Statistical Significance in Pre-Registered Studies

## Overview
This project implements an automated pipeline to assess the generalizability of statistical significance findings from pre-registered studies across disciplines. It leverages OSF (Open Science Framework) data, performs bootstrap resampling, and conducts meta-analysis to determine the stability of p-values under different model specifications.

## Directory Structure
- `code/`: Python source modules
 - `config.py`: Configuration constants and paths
 - `ingestion.py`: OSF API client and data ingestion
 - `bootstrap_engine.py`: Resampling and stability analysis
 - `meta_analysis.py`: Aggregation and visualization
 - `main.py`: Orchestration script
 - `setup_directories.py`: Directory initialization and checksumming
- `data/`:
 - `raw/`: Downloaded raw data from OSF
 - `processed/`: Cleaned and structured data
- `outputs/`:
 - `figures/`: Generated plots
 - `reports/`: Summary reports (PDF/CSV)
- `tests/`: Unit and integration tests
- `state/`: Artifact tracking and state management

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Initialize directories: `python code/setup_directories.py`
3. Run pipeline: `python code/main.py`

## Key Features
- **OSF Ingestion**: Fetches pre-registered study data with exponential backoff.
- **Bootstrap Resampling**: Stratified resampling to estimate sampling stability.
- **Specification Stability**: Tests robustness against 5 alternative model specs.
- **Meta-Analysis**: Aggregates results across studies with I² heterogeneity metrics.
- **Checksumming**: SHA-256 hashing for data integrity verification.

## License
MIT
