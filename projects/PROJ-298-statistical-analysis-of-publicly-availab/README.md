# Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Project ID**: PROJ-298

This project performs statistical analysis on publicly available Stack Overflow question tag data to identify technology growth/decline trajectories, seasonality, and co-occurrence clusters.

## Overview

The pipeline analyzes tag frequencies over time using:
- **Modified Mann-Kendall test** for trend detection
- **Theil-Sen slope estimation** for magnitude of change
- **STL/Hodrick-Prescott decomposition** for seasonality
- **Hierarchical clustering** based on tag co-occurrence

## Prerequisites

- Python 3.11+
- CPU-only environment (no GPU required)
- 64GB RAM recommended for full dataset processing
- Internet access for external data fetching (GitHub/NPM APIs)

## Project Structure

```
projects/PROJ-298-statistical-analysis-of-publicly-availab/
├── code/
│ ├── analysis/
│ │ ├── bootstrapping.py
│ │ ├── clustering.py
│ │ ├── correlation.py
│ │ ├── decomposition.py
│ │ ├── trends.py
│ │ └── generate_*.py
│ ├── data/
│ │ ├── download.py
│ │ ├── external.py
│ │ ├── generate_taxonomies.py
│ │ ├── preprocess.py
│ │ └── setup_data_structure.py
│ ├── utils/
│ │ ├── contract_validation.py
│ │ └── state_manager.py
│ ├── viz/
│ │ ├── plots.py
│ │ └── templates.py
│ └── requirements.txt
├── data/
│ ├── raw/
│ ├── processed/
│ ├── events/
│ │ └── reference_calendar.json
│ └── taxonomy/
│ └── survey_2023.json
├── notebooks/
│ ├── 02_trend_analysis.ipynb
│ ├── 03_decomposition.ipynb
│ └── 04_clustering.ipynb
├── tests/
│ ├── contract/
│ └── integration/
└── state/
 └── projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml
```

## Quick Start

### 1. Environment Setup

```bash
cd projects/PROJ-298-statistical-analysis-of-publicly-availab
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

### 2. Initialize Project Structure

```bash
# Create data directories and fetch taxonomies
python code/data/setup_data_structure.py
```

### 3. Download and Preprocess Data

```bash
# Fetch Stack Overflow PostsTags data
python code/data/download.py
python code/data/preprocess.py
```

### 4. Run Analysis Pipelines

#### Trend Analysis (User Story 1)
```bash
python code/analysis/trends.py
python code/analysis/bootstrapping.py
python code/analysis/correlation.py
python code/analysis/generate_trend_results.py
```

#### Decomposition (User Story 2)
```bash
python code/analysis/decomposition.py
python code/analysis/generate_decomposition_results.py
```

#### Clustering (User Story 3)
```bash
python code/analysis/clustering.py
python code/analysis/generate_cluster_results.py
```

### 5. Reproduce Notebooks

All notebooks are reproducible with the generated data:

```bash
# Install Jupyter if not already installed
pip install jupyter nbconvert

# Execute notebooks programmatically
jupyter nbconvert --to notebook --execute notebooks/02_trend_analysis.ipynb
jupyter nbconvert --to notebook --execute notebooks/03_decomposition.ipynb
jupyter nbconvert --to notebook --execute notebooks/04_clustering.ipynb
```

### 6. Validate Results

```bash
# Run contract tests
pytest tests/contract/

# Run integration tests
pytest tests/integration/
```

## Output Artifacts

All results are stored in `data/processed/`:

- `trend_results.json`: Trend classifications, slopes, p-values, and correlations
- `confidence_interval.json`: 95% CIs for Theil-Sen slopes
- `decomposition_results.json`: Seasonal components and statistical test results
- `cluster_results.json`: Co-occurrence clusters and alignment scores

State checksums are tracked in `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml`.

## Reproducibility

This project ensures reproducibility through:
- Deterministic random seeds where applicable
- SHA-256 checksums for all data artifacts
- Explicit dependency versions in `requirements.txt`
- Automated notebook execution via `nbconvert`

All notebooks include mandatory limitation disclosures per FR-011.

## License

This project uses publicly available data from Stack Overflow and follows their data license. Analysis code is provided for research purposes.
