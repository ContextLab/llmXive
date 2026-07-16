# Design Document: Assessing Statistical Significance of Observed Correlations

## 1. Introduction

This document outlines the design for a statistical pipeline to assess the significance of observed correlations in multivariate public datasets. The primary goal is to distinguish true structural dependencies from spurious correlations that arise due to high dimensionality and finite sample sizes.

## 2. Objectives

- Ingest multivariate datasets from the UCI Machine Learning Repository.
- Compute observed correlation matrices (Pearson and Spearman).
- Construct correlation graphs based on a configurable threshold.
- Generate empirical null distributions via permutation testing.
- Calculate network statistics (Mean Absolute Correlation, Edge Density, etc.).
- Apply the Benjamini-Yekutieli (BY) procedure for multiple testing correction.
- Perform threshold sensitivity analysis.
- Generate visualizations and reports.

## 3. Architecture

The system is designed as a modular pipeline with the following components:

### 3.1. Data Ingestion Module (`code/loaders.py`)
- **Responsibility**: Fetch datasets from UCI, handle CSV ingestion, and apply data hygiene.
- **Key Functions**:
 - `fetch_uci_dataset()`: Downloads datasets from verified UCI URLs.
 - `apply_hygiene_pipeline()`: Drops missing values, detects constant variables, and filters for continuous variables.
 - `load_and_hygiene_dataset()`: Combines fetching and hygiene into a single step.

### 3.2. Statistical Engine (`code/stats_engine.py`)
- **Responsibility**: Core statistical computations, permutation testing, and graph construction.
- **Key Functions**:
 - `compute_correlation()`: Calculates Pearson and Spearman correlation matrices.
 - `construct_graph()`: Builds a network graph from the correlation matrix using a threshold.
 - `generate_null_distribution()`: Performs permutation testing to generate an empirical null distribution.
 - `calculate_stats()`: Computes network statistics (e.g., edge density, clustering coefficient).
 - `calculate_empirical_p_value()`: Calculates p-values from the null distribution.

### 3.3. Correction Module (`code/correction.py`)
- **Responsibility**: Apply multiple testing corrections.
- **Key Functions**:
 - `benjamini_yekutieli()`: Implements the BY procedure for FDR control under dependence.
 - `apply_correction_to_results()`: Applies correction to a list of p-values.

### 3.4. Visualization Module (`code/viz.py`)
- **Responsibility**: Generate visual outputs.
- **Key Functions**:
 - `plot_heatmap()`: Visualizes correlation matrices.
 - `plot_histogram()`: Visualizes null distributions with observed values overlaid.
 - `plot_primary_threshold_visualizations()`: Generates specific visualizations for the primary threshold.
 - `plot_sensitivity_sweep()`: Visualizes sensitivity analysis results.

### 3.5. Orchestration Module (`code/main.py`)
- **Responsibility**: Coordinate the pipeline, generate reports, and integrate visualizations.
- **Key Functions**:
 - `main()`: Entry point for the full pipeline.
 - `generate_sensitivity_report()`: Creates the sensitivity analysis report.
 - `integrate_visualizations()`: Combines visual outputs into the final report.

## 4. Data Flow

1. **Dataset Discovery**: The pipeline queries the UCI repository for valid multivariate datasets (>=20 continuous variables).
2. **Data Hygiene**: Datasets are cleaned (missing values dropped, constant variables excluded).
3. **Correlation Computation**: Pearson and Spearman correlation matrices are computed.
4. **Graph Construction**: A correlation graph is built using a configurable threshold (default |r| > 0.3).
5. **Permutation Testing**: 1,000 permutations are performed to generate an empirical null distribution for each dataset.
6. **Statistical Calculation**: Network statistics are calculated for the observed graph and each permuted graph.
7. **P-value Calculation**: Empirical p-values are calculated based on the null distribution.
8. **Correction**: The BY procedure is applied to correct for multiple testing.
9. **Sensitivity Analysis**: The pipeline sweeps across thresholds {0.1, 0.2, 0.3, 0.4, 0.5}.
10. **Reporting**: Results are summarized in CSV files and visualizations are generated.

## 5. Configuration

Configuration is managed via `code/config.py`:

- **Paths**: `data/raw`, `data/processed`, `output/results`, `output/plots`, `output/reports`.
- **Random Seed**: `42` (for reproducibility).
- **Permutation Count**: `1000` (configurable).
- **Correlation Thresholds**: `{0.1, 0.2, 0.3, 0.4, 0.5}`.
- **Correlation Method**: `pearson` (primary), `spearman` (exploratory).

## 6. Error Handling

- **Data Fetching**: If a UCI URL fails to download, the pipeline raises a `FileNotFoundError` or `ValueError` (no synthetic fallback).
- **Dataset Validation**: Datasets with <20 continuous variables are excluded.
- **Permutation Testing**: If the null model validation fails (p < 0.05 for synthetic data), the pipeline halts with an error.

## 7. Dependencies

- Python 3.11+
- `pandas`
- `numpy`
- `scipy`
- `networkx`
- `matplotlib`
- `seaborn`
- `requests`

## 8. Future Work

- Extend to support additional data sources beyond UCI.
- Implement parallel processing for large-scale permutation testing.
- Add interactive visualization capabilities (e.g., Plotly).
- Explore additional network statistics (e.g., modularity, centrality measures).