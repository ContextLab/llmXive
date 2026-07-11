# Assessing Orbital Period Dependence of the Exoplanet Radius Gap

A research pipeline to analyze the dependence of the exoplanet radius gap on orbital period using Kepler DR25 data. This project implements a rigorous statistical analysis comparing photoevaporation and core-powered mass loss theories.

## Project Overview

This pipeline performs the following steps:
1. **Data Ingestion**: Downloads Kepler DR25 Planet Table and Kepler Input Catalog (KIC) from MAST
2. **Preprocessing**: Filters planets by uncertainty criteria, merges catalogs, and resolves duplicates
3. **Gap Location Estimation**: Uses Gaussian Mixture Models (GMM) to identify the radius gap in period bins
4. **Slope Calculation**: Performs Errors-in-Variables (EIV) regression to determine the scaling relationship
5. **Theory Comparison**: Uses Monte Carlo simulation to compare measured slopes against theoretical predictions

## Prerequisites

- Python 3.8+
- pip and virtual environment tools
- Internet connection for data download

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### 2. Initialize Directory Structure

```bash
python code/setup_data_dirs.py
```

### 3. Run the Full Pipeline

```bash
python code/main.py
```

This will:
- Download Kepler DR25 and KIC data
- Preprocess and filter the data
- Perform GMM fitting for gap location estimation
- Run regression analysis
- Compare results with theoretical models
- Generate final results in `paper/results.md`

## Project Structure

```
.
├── code/
│ ├── ingest/ # Data download and preprocessing
│ │ ├── download_dr25.py
│ │ ├── download_kic.py
│ │ ├── merge_catalogs.py
│ │ └── preprocess.py
│ ├── analysis/ # Gap analysis and regression
│ │ ├── binning.py
│ │ ├── gmm_fitter.py
│ │ └── regression.py
│ ├── theory/ # Theoretical models
│ │ ├── scaling_laws.py
│ │ └── theory_comparison.py
│ ├── validation/ # Synthetic data validation
│ │ └── synthetic_recovery.py
│ ├── utils/ # Utility functions
│ ├── models/ # Data models
│ └── main.py # Pipeline orchestrator
├── data/
│ ├── raw/ # Downloaded raw data
│ └── processed/ # Processed data and results
├── tests/
│ ├── contract/ # Schema validation tests
│ └── unit/ # Unit tests
├── paper/
│ └── results.md # Final results report
├── README.md
└── quickstart.md
```

## Data Flow

1. **Raw Data**: `data/raw/dr25_raw.csv`, `data/raw/kic_raw.csv`, `data/raw/completeness_map.csv`
2. **Processed Data**: `data/processed/filtered_planets.csv`, `data/processed/deduped_planets.csv`
3. **Analysis Outputs**: `data/processed/binned_planets.csv`, `data/processed/gap_locations.csv`
4. **Final Results**: `data/processed/slope_results.json`, `paper/results.md`

## Execution Instructions

### Running Individual Steps

You can run individual pipeline steps for debugging or incremental development:

```bash
# Download data
python code/ingest/download_dr25.py
python code/ingest/download_kic.py

# Preprocess data
python code/ingest/preprocess.py

# Run analysis
python code/analysis/integrate_gap_analysis.py

# Run regression
python code/analysis/regression.py

# Compare with theory
python code/theory/theory_comparison.py
```

### Validation

```bash
# Run synthetic data validation
python code/validation/synthetic_recovery.py

# Run unit tests
pytest tests/unit/

# Run contract tests
pytest tests/contract/
```

## Configuration

Theoretical model parameters are defined in `code/theory/config.yaml`:
- Owen & Wu (photoevaporation): slope = -0.11 ± 0.02 [UNRESOLVED-CLAIM: c_f6c115a2 — status=not_enough_info]
- Ginzburg et al. (2018) (core-powered): slope = -0.15 ± 0.03 [UNRESOLVED-CLAIM: c_ebe21160 — status=not_enough_info]

## Performance Constraints

- Total pipeline execution must complete within 6 hours on CPU-only runners
- Memory usage is optimized for standard research computing environments
- All analysis uses CPU-only operations (no GPU dependencies)

## Dependencies

See `code/requirements.txt` for the complete list of dependencies:
- pandas, numpy, scipy, scikit-learn
- astropy, astroquery
- pyyaml, pytest, tqdm

## License

This project is for research purposes. Please refer to the original data sources (Kepler Mission, MAST) for their licensing terms.

## Contact

For questions about this implementation, please refer to the project documentation or open an issue in the repository.