# API Reference

## Overview

This document provides a reference for the core modules and functions in the llmXive network topology project.

## Configuration

### `code/config.py`

```python
from config import ensure_directories, get_config_dict
```

**Functions:**
- `ensure_directories()` - Creates required data directories
- `get_config_dict()` - Returns all configuration parameters

**Key Configurations:**
- `WINDOW_LENGTH_BASELINE` - Baseline window length (30 TR)
- `WINDOW_LENGTH_VALIDATION` - Validation window lengths ([20, 25, 30, 35])
- `K_MEANS_K` - Number of K-Means clusters (5)
- `DENSITY_THRESHOLD_BASELINE` - Baseline density threshold (0.15)
- `TRACTOGRAPHY_CONFIDENCE_THRESHOLDS` - Confidence levels ([0.0, 0.2, 0.4, 0.6, 0.8])

## Preprocessing

### `code/preprocess/loader.py`

```python
from preprocess.loader import load_hcp_fmri, load_hcp_dmri, load_hcp_data
```

**Functions:**
- `load_hcp_fmri(subject_id)` - Loads fMRI data for a subject
- `load_hcp_dmri(subject_id)` - Loads dMRI data for a subject
- `load_hcp_data(subject_id)` - Loads both fMRI and dMRI data

### `code/preprocess/structural.py`

```python
from preprocess.structural import calculate_graph_metrics, run_structural_pipeline
```

**Functions:**
- `calculate_graph_metrics(adjacency_matrix, density_threshold)` - Computes graph metrics
- `run_structural_pipeline(subject_ids)` - Processes all subjects
- `run_sensitivity_analysis()` - Runs density sensitivity analysis

**Returns:**
- Global efficiency
- Average clustering coefficient
- Modularity

### `code/preprocess/functional.py`

```python
from preprocess.functional import compute_sliding_window_correlation, extract_dynamic_states_loo
```

**Functions:**
- `compute_sliding_window_correlation(fmri_data, window_length, step)` - Computes sliding windows
- `extract_dynamic_states_loo(all_subjects_data, subject_id, k)` - LOO K-Means centroid generation
- `assign_states_and_calculate_metrics(subject_data, centroids)` - Assigns states and calculates metrics

**Returns:**
- State assignments
- Mean dwell time
- Number of visited states

## Analysis

### `code/analysis/correlation.py`

```python
from analysis.correlation import check_normality, calculate_correlation, benjamini_hochberg_fdr
```

**Functions:**
- `check_normality(data)` - Performs Shapiro-Wilk test
- `calculate_correlation(structural_metrics, dynamic_metrics)` - Computes correlations
- `benjamini_hochberg_fdr(p_values)` - Applies FDR correction

**Returns:**
- Correlation coefficient (r)
- P-value
- FDR-corrected p-value

### `code/analysis/robustness.py`

```python
from analysis.robustness import run_sensitivity_analysis, calculate_sensitivity_metrics
```

**Functions:**
- `run_sensitivity_analysis()` - Runs all sensitivity analyses
- `calculate_sensitivity_metrics(baseline, variations)` - Computes sensitivity metrics

### `code/analysis/tractography_sensitivity.py`

```python
from analysis.tractography_sensitivity import run_tractography_sensitivity_analysis
```

**Functions:**
- `run_tractography_sensitivity_analysis()` - Varies tractography confidence thresholds

### `code/analysis/tractography_correlation_sensitivity.py`

```python
from analysis.tractography_correlation_sensitivity import run_correlation_for_threshold
```

**Functions:**
- `run_correlation_for_threshold(threshold)` - Runs correlation at specific threshold

## Reports

### `code/reports/generate_report.py`

```python
from reports.generate_report import generate_final_report
```

**Functions:**
- `generate_final_report()` - Generates comprehensive final report

**Output:**
- `data/processed/final_report.json`

### `code/reports/validate_report.py`

```python
from reports.validate_report import validate_report_file
```

**Functions:**
- `validate_report_file(report_path)` - Validates report against schema

### `code/reports/audit_associational_language.py`

```python
from reports.audit_associational_language import generate_audit_report
```

**Functions:**
- `generate_audit_report()` - Checks for causal language

## Utilities

### `code/utils/cpu_optimization.py`

```python
from utils.cpu_optimization import optimize_memory_usage, set_random_seed
```

**Functions:**
- `optimize_memory_usage()` - Optimizes memory for CPU-only execution
- `set_random_seed(seed)` - Sets random seed for reproducibility
- `validate_no_gpu_acceleration()` - Ensures no GPU usage

## Main Pipeline

### `code/main.py`

```python
from main import main
```

**Functions:**
- `main()` - Orchestrates the full pipeline

**Execution Order:**
1. Load data
2. Compute structural metrics
3. Extract dynamic states (LOO)
4. Perform correlation analysis
5. Run sensitivity analyses
6. Generate logs
