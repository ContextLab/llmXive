# Project Architecture: Network Topology Influence on Brain Activity

## Overview
This project investigates the relationship between structural brain network topology (derived from diffusion MRI) and spontaneous functional activity patterns (derived from fMRI). The pipeline follows a strict "associational" framing, avoiding causal claims.

## Directory Structure
```
PROJ-128/
├── code/ # Main implementation
│ ├── config.py # Configuration and paths
│ ├── main.py # Batch processing entry point
│ ├── preprocess/ # Data loading and feature extraction
│ │ ├── loader.py # HCP data fetching
│ │ ├── structural.py # Graph metric calculation
│ │ └── functional.py # Sliding window & LOO K-Means
│ ├── analysis/ # Statistical testing
│ │ ├── correlation.py # Normality tests, correlations, FDR
│ │ └── robustness.py # Sensitivity analysis
│ ├── reports/ # Report generation
│ │ ├── generate_report.py
│ │ ├── validate_report.py
│ │ └── audit_associational_language.py
│ └── utils/ # CPU optimization utilities
├── data/ # Data storage
│ ├── raw/ # Downloaded HCP data
│ ├── processed/ # Metrics CSVs and correlation results
│ └── logs/ # Exclusion logs
├── contracts/ # Schema definitions
│ ├── dataset.schema.yaml
│ └── output.schema.yaml
├── tests/ # Unit and integration tests
│ ├── unit/
│ └── integration/
├── docs/ # Documentation (this file)
├── requirements.txt # Dependencies
└── README.md # Project overview
```

## Core Components

### 1. Preprocessing Pipeline
- **Structural**: Calculates global efficiency, clustering coefficient, and modularity from dMRI-derived adjacency matrices.
- **Functional**: Implements sliding-window correlation (30 TR window, 1 TR step) and **Leave-One-Out (LOO) K-Means** (k=5) to derive dynamic states.
 - *Critical Constraint*: LOO ensures subject i's windows are assigned to centroids derived from all other subjects (j != i), preventing circular correlation.

### 2. Analysis Module
- **Correlation**: Performs Shapiro-Wilk normality tests. Selects Pearson (normal) or Spearman (non-normal) correlations. Applies Benjamini-Hochberg FDR correction (q=0.05).
- **Robustness**: Re-runs analysis with 20 TR windows and ±5% density thresholds to verify stability.

### 3. Reporting
- Generates a final report with explicit "associational" language.
- Includes sensitivity tables showing absolute differences between 30 TR and 20 TR correlation coefficients.
- Validates output against `contracts/output.schema.yaml`.

## Data Flow
1. **Fetch**: `code/preprocess/loader.py` downloads HCP data from OpenNeuro.
2. **Process**: `code/main.py` iterates subjects, computing structural and dynamic metrics.
3. **Aggregate**: Metrics are saved to `data/processed/structural_metrics.csv` and `dynamic_metrics.csv`.
4. **Correlate**: `code/analysis/correlation.py` computes structure-function relationships.
5. **Report**: `code/reports/generate_report.py` synthesizes findings.

## Dependencies
See `requirements.txt` for the full list. Key libraries:
- `nilearn`: Neuroimaging data handling
- `networkx`: Graph theory metrics
- `scikit-learn`: Clustering
- `scipy`/`statsmodels`: Statistical testing
- `pandas`/`numpy`: Data manipulation

## Execution
Run the full pipeline:
```bash
python code/main.py
```
Run validation:
```bash
python code/validate_quickstart.py
```
