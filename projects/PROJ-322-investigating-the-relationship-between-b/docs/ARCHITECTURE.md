# Project Architecture

## Overview
This document describes the high-level architecture of the llmXive automated science pipeline for investigating the relationship between brain network reconfiguration and recovery from mild traumatic brain injury (mTBI).

## Directory Structure
```
.
├── code/ # Python source modules
│ ├── __init__.py
│ ├── analysis_report.py
│ ├── bootstrapping.py
│ ├── collinearity.py
│ ├── config.py
│ ├── data_ingestion.py
│ ├── entities.py
│ ├── graph_metrics.py
│ ├── logging_config.py
│ ├── memory_monitor.py
│ ├── preprocessing.py
│ ├── robustness.py
│ ├── sensitivity_analysis.py
│ ├── statistical_model.py
│ ├── synthetic_data.py
│ ├── time_monitor.py
│ ├── validation.py
│ └── validation_search.py
├── data/
│ ├── raw/ # Raw downloaded data (OpenNeuro)
│ ├── processed/ # Preprocessed fMRI data
│ └── results/ # Final analysis outputs
├── tests/
│ ├── unit/
│ └── integration/
├── docs/
└── specs/
```

## Core Components

### 1. Configuration & Infrastructure
- **`config.py`**: Central configuration management, including synthetic data mode toggles and resource limits.
- **`logging_config.py`**: Logging infrastructure with memory-aware hooks.
- **`memory_monitor.py`**: Runtime memory monitoring to enforce the 6GB RAM limit.
- **`time_monitor.py`**: Runtime monitoring to enforce the 6-hour execution limit.

### 2. Data Pipeline
- **`data_ingestion.py`**: Handles downloading datasets from OpenNeuro and generating manifests.
- **`preprocessing.py`**: Minimal preprocessing (confound regression, AAL parcellation) and connectivity matrix computation.
- **`synthetic_data.py`**: Generates synthetic data for methodology validation mode.

### 3. Analysis Modules
- **`entities.py`**: Core data classes (`Subject`, `ConnectivityMatrix`, `GraphMetrics`).
- **`graph_metrics.py`**: Calculates Global Efficiency, Local Efficiency, and Modularity.
- **`statistical_model.py`**: Fits Linear Mixed-Effects models for correlation analysis.
- **`collinearity.py`**: Handles multicollinearity via VIF and PCA fallbacks.
- **`robustness.py`**: Performs permutation testing for empirical p-values.
- **`sensitivity_analysis.py`**: Sweeps correlation thresholds to test robustness.
- **`validation.py`**: Validates results against independent clinical metrics.
- **`validation_search.py`**: Searches OpenNeuro metadata for external validation targets.

### 4. Reporting
- **`analysis_report.py`**: Aggregates metrics, logs, and compliance status into a final JSON report.
- **`bootstrapping.py`**: Implements bootstrapping for confidence intervals when sample sizes are small.

## Data Flow
1. **Ingestion**: `data_ingestion.py` downloads raw data → `data/raw/`.
2. **Preprocessing**: `preprocessing.py` cleans data → `data/processed/`.
3. **Metric Calculation**: `graph_metrics.py` computes network properties.
4. **Statistical Modeling**: `statistical_model.py` fits LME models.
5. **Validation**: `robustness.py` and `sensitivity_analysis.py` verify results.
6. **Reporting**: `analysis_report.py` generates `data/results/analysis_report.json`.

## Resource Constraints
- **Memory**: Hard limit of 6GB RAM enforced by `memory_monitor.py`.
- **Time**: Hard limit of 6 hours enforced by `time_monitor.py`.
- **Hardware**: CPU-only execution (no GPU dependencies).
