# Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Project ID**: PROJ-298
**Status**: Production Ready

## Overview

This project performs statistical analysis on publicly available Stack Overflow question tag data to identify technology growth/decline trajectories, seasonality patterns, and technology clusters.

## Features

- **Trend Analysis (US1)**: Modified Mann-Kendall tests with Theil-Sen slope estimation, Benjamini-Hochberg correction, and power analysis.
- **Decomposition (US2)**: STL/Hodrick-Prescott decomposition with ADF stationarity pre-testing and event alignment validation.
- **Clustering (US3)**: Co-occurrence analysis using Jaccard similarity, hierarchical clustering, and taxonomy alignment scoring.
- **External Validation**: Correlation with GitHub stars and NPM download metrics.

## Project Structure

```
projects/PROJ-298-statistical-analysis-of-publicly-availab/
├── code/
│ ├── analysis/ # Statistical analysis modules
│ ├── data/ # Data ingestion and preprocessing
│ ├── utils/ # Utility functions (hygiene, state management)
│ ├── viz/ # Visualization and template generation
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed time-series data
│ ├── events/ # Reference calendar for event alignment
│ └── taxonomy/ # Survey-based taxonomy mappings
├── notebooks/ # Reproducible Jupyter notebooks
├── tests/ # Unit, contract, and integration tests
├── state/ # Artifact state and checksums
├── README.md
└── quickstart.md
```

## Prerequisites

- Python 3.11+
- CPU-only execution environment (compatible with GitHub Actions runners)
- ~14 GB disk space for data artifacts
- ~7 GB RAM for streaming processing

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-298-statistical-analysis-of-publicly-availab
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

## Quick Start

See [quickstart.md](./quickstart.md) for the full execution pipeline.

### Running Individual Modules

**Data Download & Preprocessing**:
```bash
python code/data/download.py
python code/data/preprocess.py
```

**Trend Analysis**:
```bash
python code/analysis/trends.py
python code/analysis/bootstrapping.py
python code/analysis/generate_trend_results.py
```

**Decomposition**:
```bash
python code/analysis/decomposition.py
python code/analysis/generate_decomposition_results.py
```

**Clustering**:
```bash
python code/analysis/clustering.py
python code/analysis/generate_cluster_results.py
```

**External Correlation**:
```bash
python code/data/external.py
python code/analysis/correlation.py
```

### Running Notebooks

All analysis is reproducible via Jupyter notebooks:
```bash
jupyter notebook notebooks/02_trend_analysis.ipynb
jupyter notebook notebooks/03_decomposition.ipynb
jupyter notebook notebooks/04_clustering.ipynb
```

## Data Sources

- **Primary**: Stack Overflow Data Dump (PostsTags table) via HuggingFace datasets
- **External Validation**: GitHub Search API (stars) and NPM Search API (downloads)
- **Taxonomy**: Stack Overflow Developer Survey 2023

## Statistical Methods

- **Trend Detection**: Modified Mann-Kendall test with pre-whitening, Theil-Sen slope estimator
- **Multiple Testing**: Benjamini-Hochberg false discovery rate correction
- **Power Analysis**: Minimum Detectable Effect Size (MDES) calculation
- **Decomposition**: STL (Seasonal-Trend decomposition using Loess) or Hodrick-Prescott filter
- **Seasonality**: Augmented Dickey-Fuller (ADF) stationarity test, spectral analysis
- **Clustering**: Jaccard similarity, hierarchical clustering with permutation validation

## Output Artifacts

All outputs are stored in `data/processed/`:

- `trend_results.json`: Trend classifications, slopes, p-values, and external correlations
- `confidence_interval.json`: 95% bootstrap confidence intervals for slopes
- `decomposition_results.json`: Decomposition components, Ljung-Box and Rayleigh test results
- `cluster_results.json`: Jaccard matrix, cluster assignments, alignment scores

## Validation & Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Verify artifact contracts:
```bash
python code/verification/verify_limitations.py
```

## Reproducibility

- All scripts write SHA-256 checksums to `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml`
- Notebooks include mandatory limitation disclosures (FR-011)
- Streaming processing ensures compatibility with limited RAM environments

## Limitations

**Important**: All findings are associational and do not imply causality. External correlations are based on topic/keyword mapping and may not capture all relevant technologies.

## License

MIT License
