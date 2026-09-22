# PROJ-444: Predicting Molecular Properties from Topological Data Analysis

## Overview
This project implements a pipeline to predict molecular properties (specifically LogP from the ESOL dataset) using Topological Data Analysis (TDA) features derived from molecular graphs.

## Structure
- `code/`: Source code for the pipeline (ingestion, TDA computation, modeling, diagnostics)
- `data/`:
 - `raw/`: Original dataset files
 - `processed/`: Feature matrices, splits, and intermediate results
- `data/logs/`: Execution logs
- `state/`: Pipeline state tracking
- `reports/`: Final metrics and analysis reports
- `tests/`: Unit and integration tests

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Quick Start
1. Set up the data directory structure: `python code/setup_data_structure.py`
2. Ingest data: `python code/01_data_ingestion.py`
3. Compute TDA features: `python code/02_tda_computation.py`
4. Train models: `python code/04_model_training.py`
5. Run diagnostics: `python code/06_diagnostics.py`

## License
MIT
