# Project Architecture

## Directory Structure

```
PROJ-128-investigating-the-influence-of-network-t/
├── code/
│ ├── config.py # Global configuration (paths, seeds, hyperparameters)
│ ├── main.py # Entry point for the full pipeline
│ ├── analysis/
│ │ ├── correlation.py # Statistical correlation analysis (normality, FDR)
│ │ ├── robustness.py # Sensitivity analysis (window length, density)
│ │ └── generate_correlation_results.py
│ ├── preprocess/
│ │ ├── __init__.py
│ │ ├── loader.py # HCP data loading (dMRI/fMRI)
│ │ ├── structural.py # Graph metric calculation (NetworkX)
│ │ └── functional.py # Sliding window, LOO k-means, dynamic metrics
│ └── reports/
│ ├── generate_report.py # Final report generation
│ └── validate_report.py # Schema validation
├── data/
│ ├── raw/ # Downloaded HCP data
│ ├── processed/ # Metrics, correlations, sensitivity results
│ ├── figures/ # Generated plots (if any)
│ └── logs/ # Exclusion logs, resource usage
├── contracts/
│ ├── dataset.schema.yaml # Input data schema
│ └── output.schema.yaml # Output data schema
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/ # Documentation (this file)
├── requirements.txt
├── pyproject.toml # Linting/formatting config
└── README.md
```

## Module Responsibilities

### `code/config.py`
- Defines global paths, random seeds, and baseline parameters.
- Provides `get_config_dict()` for accessing configuration.
- Ensures directory structure exists via `ensure_directories()`.

### `code/main.py`
- Orchestrates the full pipeline:
 1. Loads configuration.
 2. Processes each subject (structural + functional).
 3. Aggregates metrics to CSV.
 4. Runs correlation analysis.
 5. Performs robustness checks.
 6. Generates final report.
- Handles subject exclusion logging.

### `code/preprocess/loader.py`
- Fetches real HCP data from OpenNeuro.
- Provides `load_hcp_fmri()`, `load_hcp_dmri()`, and `load_hcp_data()`.
- Fails loudly if data cannot be fetched (no synthetic fallback).

### `code/preprocess/structural.py`
- Calculates graph metrics: global efficiency, clustering, modularity.
- Uses `networkx` for graph analysis.
- Excludes subjects with sparsity > 90%.

### `code/preprocess/functional.py`
- Computes sliding-window correlation (30 TR window, 1 TR step).
- Implements **Leave-One-Out (LOO) k-means** (k=5) for dynamic states.
- Calculates dynamic metrics: dwell time, visited states.

### `code/analysis/correlation.py`
- Tests normality (Shapiro-Wilk).
- Calculates Pearson/Spearman correlations.
- Applies Benjamini-Hochberg FDR correction.

### `code/analysis/robustness.py`
- Re-runs analysis with alternative parameters (20 TR window, ±5% density).
- Calculates sensitivity metrics (absolute difference in r-values).

### `code/reports/generate_report.py`
- Aggregates all results into a final report.
- Ensures "associational" framing.
- Validates against `contracts/output.schema.yaml`.

## Data Flow

1. **Raw Data**: Downloaded from OpenNeuro (`data/raw/`).
2. **Preprocessing**:
 - Structural: dMRI → Connectivity Matrix → Graph Metrics.
 - Functional: fMRI → Sliding Window → LOO Clustering → Dynamic Metrics.
3. **Aggregation**: Metrics per subject → CSV files (`data/processed/`).
4. **Analysis**: Correlation → FDR correction → `correlation_results.csv`.
5. **Robustness**: Sensitivity checks → `sensitivity_results.json`.
6. **Reporting**: Final report → `final_report.json`.

## Testing Strategy

- **Unit Tests**: Individual functions (e.g., normality check, FDR correction).
- **Integration Tests**: Single-subject pipeline, end-to-end correlation analysis.
- **Validation**: Report schema validation (`validate_report.py`).

## Dependencies

See `requirements.txt` for the full list:
- `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `scipy`, `pyyaml`.

## Execution Constraints

- **CPU-Only**: No GPU calls; designed for limited compute environments.
- **Memory**: ~7 GB RAM required; ~14 GB disk space.
- **Real Data**: No synthetic data; pipeline fails if HCP data is unreachable.