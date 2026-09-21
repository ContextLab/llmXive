# Design Document: Network Centrality and Motor Memory Consolidation

## Overview
This project investigates the impact of network centrality metrics derived from functional connectivity on the consolidation of motor memories. The analysis leverages fMRI data preprocessed with fMRIPrep and behavioral metrics extracted from OpenNeuro datasets.

## Architecture
The pipeline follows a modular structure:
1. **Data Ingestion**: Downloads and validates raw data (OpenNeuro).
2. **Preprocessing**: Wraps fMRIPrep for memory-efficient processing.
3. **Behavioral Extraction**: Extracts motor scores and demographics.
4. **Centrality Analysis**: Computes graph metrics (degree, betweenness, eigenvector) using the AAL3 atlas.
5. **Regression Modeling**: Fits linear and GAM models with motion covariates.
6. **Validation**: Performs Freedman-Lane permutation tests and k-fold cross-validation.

## Data Flow
- **Input**: OpenNeuro dataset (dsXXXX)
- **Intermediate**: Preprocessed NIfTI, connectivity matrices, centrality metrics (CSV)
- **Output**: Regression summaries, validation metrics, reproducibility reports (JSON/CSV)

## Key Dependencies
- `nilearn`: Connectivity and atlas handling
- `networkx`: Graph centrality calculations
- `statsmodels`: Regression and GAM fitting
- `scikit-learn`: Cross-validation
- `openneuro-cli`: Data download

## Configuration
All parameters are managed via `code/utils/config.py`. Key thresholds:
- Retention rate: 80%
- VIF threshold: 5.0
- Power threshold (N): 85
- Permutation seeds: 42
- CV folds: 5

## Execution
Run the full pipeline via `python code/main.py` (or specific stage scripts in `code/data/`, `code/analysis/`).
