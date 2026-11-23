# Design Document: Evaluating the Robustness of Common Statistical Tests to Non-Independence

## 1. Overview

This document outlines the design for a research pipeline that quantifies the inflation of Type I error rates and the reduction of statistical power in common statistical tests (t-test, ANOVA, Chi-squared) when the assumption of independence is violated.

The project uses public datasets from the UCI Machine Learning Repository and OpenML to ensure reproducibility and relevance to real-world data scenarios.

## 2. Methodology

### 2.1 Generate-then-Inject Paradigm
To ensure a true null hypothesis ($H_0$) is maintained during simulation, we employ a "Generate-then-Inject" approach:
1. **Generate**: Create synthetic data under $H_0$ (independence) with known parameters (e.g., equal means for t-test).
2. **Inject**: Apply dependency structures (AR(1), Block Bootstrap, Spatial Kernel Smoothing) to the synthetic data.
3. **Test**: Run the statistical test and record the p-value.
4. **Aggregate**: Repeat $N$ times (e.g., 10,000) to estimate the empirical Type I error rate.

### 2.2 Dependency Structures
- **Temporal (AR(1))**: Autocorrelation with strength $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$.
- **Hierarchical (Block Bootstrap)**: Clustering-based resampling to induce group-level dependency.
- **Spatial**: Kernel smoothing based on feature-space clustering proxies for datasets lacking explicit coordinates.

### 2.3 Metrics
- **Type I Error Rate**: Proportion of rejections at nominal $\alpha = 0.05$.
- **Power**: Proportion of rejections when a true effect ($\delta$) is injected.
- **Confidence Intervals**: Clopper-Pearson exact intervals for error rates.
- **Trend Verification**: Spearman rank correlation to confirm monotonic increase in error rates with dependency strength.

## 3. Data Sources

Datasets are fetched from verified, canonical URLs:
- **UCI Adult**: `
- **UCI Wine**: `
- **OpenML**: Specific dataset IDs defined in `data/manifests/datasets.yaml`.

Data integrity is verified via checksums stored in `data/manifests/checksums.json`.

## 4. Project Structure

```
PROJ-483-evaluating-the-robustness-of-common-stat/
├── code/
│ ├── config.py # Configuration loading and validation
│ ├── data_loader.py # Fetching and validating datasets
│ ├── dependency_injector.py # AR(1), Block, Spatial injection logic
│ ├── metrics.py # Error rate, power, CI calculations
│ ├── simulation_runner.py # Monte Carlo loop implementation
│ ├── visualizer.py # Plot generation
│ └── main.py # Orchestration and execution
├── data/
│ ├── manifests/ # Dataset URLs, checksums, proxy reports
│ └── raw/ # Downloaded raw CSVs
├── results/
│ ├── simulation_raw.csv # Individual p-values
│ ├── aggregated.csv # Aggregated error rates and power
│ └── logistic_models.pkl # Trained regression models
├── docs/
│ └── DESIGN.md # This file
├── tests/
│ └── unit/ # Unit tests for core logic
├── requirements.txt # Python dependencies
└── README.md # Project overview and usage
```

## 5. Execution Workflow

1. **Setup**: Initialize directories and load configuration (`code/config.py`).
2. **Data Loading**: Fetch and validate datasets (`code/data_loader.py`).
3. **Proxy Generation**: Generate spatial proxies if coordinates are missing (`code/dependency_injector.py`).
4. **Simulation**: Run Monte Carlo replications (`code/main.py` -> `code/simulation_runner.py`).
5. **Analysis**: Calculate metrics and train logistic models (`code/metrics.py`).
6. **Visualization**: Generate error rate curves and power plots (`code/visualizer.py`).

## 6. Reproducibility

- All random seeds are pinned in `code/config.yaml`.
- Checksums ensure data integrity.
- Vectorized operations (NumPy) ensure performance on CPU-only environments.
- Full code and data artifacts are version-controlled.

## 7. Limitations and Edge Cases

- **Small Sample Size**: Datasets with $N < 50$ are skipped and logged.
- **Proxy Quality**: If spatial proxy clustering quality is poor, the pipeline falls back to hierarchical dependency injection.
- **Normality Violations**: Edge cases where injected dependency violates normality assumptions are logged and handled gracefully.
