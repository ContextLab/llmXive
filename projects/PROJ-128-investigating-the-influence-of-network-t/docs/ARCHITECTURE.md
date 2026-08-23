# Architecture Documentation

## System Overview

The pipeline processes HCP dMRI and fMRI data to compute structural and dynamic graph metrics, then correlates them to investigate the relationship between structural topology and spontaneous brain activity patterns.

## Module Responsibilities

### `code/config.py`
- Centralized configuration for paths, seeds, and hyperparameters
- Functions: `ensure_directories()`, `get_config_dict()`

### `code/preprocess/`
- **`loader.py`**: Downloads and loads HCP data from OpenNeuro
- **`structural.py`**: Computes graph metrics (efficiency, clustering, modularity) from dMRI
- **`functional.py`**: Computes sliding-window correlations, LOO k-means states, and dynamic metrics

### `code/analysis/`
- **`correlation.py`**: Normality testing, correlation calculation, FDR correction
- **`robustness.py`**: Sensitivity analysis for window length and density thresholds

### `code/reports/`
- **`generate_report.py`**: Aggregates results into final JSON report
- **`validate_report.py`**: Validates output against schema
- **`audit_associational_language.py`**: Checks for causal language violations

### `code/main.py`
- Orchestrates the full pipeline: data loading, metric computation, correlation, robustness, reporting

### `code/utils/cpu_optimization.py`
- Memory optimization, random seed setting, GPU validation

## Data Flow

1. **Input**: HCP dMRI/fMRI data (OpenNeuro)
2. **Structural Pipeline**: dMRI → Graph → Metrics (global efficiency, clustering, modularity)
3. **Functional Pipeline**: fMRI → Sliding windows → LOO k-means → Metrics (dwell time, visited states)
4. **Correlation**: Structural metrics ↔ Dynamic metrics → r, p, FDR
5. **Robustness**: Re-run with 20 TR window and ±5% density → sensitivity metrics
6. **Output**: `data/processed/*.csv`, `data/reports/final_report.json`

## Key Algorithms

### Leave-One-Out (LOO) K-Means
For each subject `i`:
1. Compute centroids from all subjects `j != i`
2. Assign subject `i`'s windows to these centroids
3. Calculate dwell times and state counts

This prevents circular correlation and satisfies the Constitution Principle VI.

### Benjamini-Hochberg FDR Correction
Applied to all correlation p-values (q=0.05) to control false discovery rate.

## Error Handling

- **Subject Exclusion**: Convergence failures or sparsity >90% logged to `data/logs/exclusion_log.json`
- **Data Fetch Failure**: Scripts fail loudly (no synthetic fallback)
- **Zero Significant Findings**: Report explicitly states this outcome

## Dependencies

See `requirements.txt`:
- nilearn, networkx, scikit-learn, pandas, numpy, scipy, statsmodels, pyyaml
