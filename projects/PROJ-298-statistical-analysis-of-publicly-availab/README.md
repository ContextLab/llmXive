# Statistical Analysis of Publicly Available Stack Overflow Question Tags

This project performs a comprehensive statistical analysis of technology trends using Stack Overflow tag data. It quantifies growth/decline trajectories, visualizes time series decomposition, and clusters technologies via co-occurrence analysis.

## Project Structure

```
projects/PROJ-298-statistical-analysis-of-publicly-availab/
├── code/
│ ├── analysis/ # Statistical analysis modules
│ ├── data/ # Data download and preprocessing
│ ├── utils/ # Utility functions
│ ├── viz/ # Visualization modules
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed analysis data
│ ├── taxonomy/ # Taxonomy and reference data
│ └── events/ # Reference calendar of events
├── notebooks/ # Jupyter notebooks for analysis
├── tests/ # Unit and integration tests
└── state/ # Project state and checksums
```

## Prerequisites

- Python 3.11+
- pip package manager
- Access to Stack Overflow data dump or HuggingFace datasets

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

See `quickstart.md` for step-by-step instructions to reproduce the entire analysis pipeline.

## Analysis Pipeline

The project implements three main user stories:

### User Story 1: Quantify Technology Growth and Decline
- Downloads and preprocesses Stack Overflow tag data
- Applies Modified Mann-Kendall test with pre-whitening
- Calculates Theil-Sen slopes and confidence intervals
- Validates against GitHub stars and NPM downloads
- Outputs: `data/processed/trend_results.json`

### User Story 2: Time Series Decomposition
- Performs ADF stationarity tests
- Applies STL or Hodrick-Prescott decomposition
- Tests residual independence (Ljung-Box)
- Aligns with industry events (Rayleigh test)
- Outputs: `data/processed/decomposition_results.json`

### User Story 3: Technology Clustering
- Computes Jaccard similarity matrix for tag co-occurrence
- Performs hierarchical clustering
- Validates clusters via permutation tests
- Aligns with Stack Overflow Survey taxonomy
- Outputs: `data/processed/cluster_results.json`

## Reproducibility

All notebooks in the `notebooks/` directory are fully reproducible:
- `02_trend_analysis.ipynb` - Trend analysis and visualization
- `03_decomposition.ipynb` - Time series decomposition
- `04_clustering.ipynb` - Clustering and co-occurrence analysis

To reproduce:
1. Ensure all data files exist in `data/processed/`
2. Run each notebook sequentially or execute via:
 ```bash
 jupyter nbconvert --execute notebooks/*.ipynb
 ```

## Data Sources

- **Stack Overflow PostsTags**: Downloaded from official data dump or HuggingFace
- **GitHub Stars**: Fetched via GitHub Search API
- **NPM Downloads**: Fetched via NPM Search API
- **Stack Overflow Developer Survey**: Used for taxonomy validation

## Validation

- Contract tests verify output schemas
- Integration tests validate pipeline end-to-end
- SHA-256 checksums track data integrity
- Limitation disclosures included in all visualizations

## License

This project is for research purposes only.
