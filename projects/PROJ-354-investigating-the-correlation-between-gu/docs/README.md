# Gut Microbiome-Cognitive Correlation Study

## Project Overview

This project investigates the correlation between gut microbiome composition (16S rRNA sequencing data) and cognitive assessment scores using data from the UK Biobank. The study employs rigorous statistical methods including Isometric Log-Ratio (ILR) transformation for compositional data, Lasso/Ridge regularized regression for confounder control, and Benjamini-Hochberg correction for multiple testing.

## Key Features

- **Data Pipeline**: Streaming data loader for large UK Biobank datasets (>14GB) with memory optimization
- **Preprocessing**: Bayesian-multiplicative zero-replacement (alpha=1e-6) and ILR transformation
- **Statistical Analysis**: Regularized linear models with comprehensive confounder adjustment
- **Validation**: Power analysis, citation validation, and sensitivity analyses
- **Visualization**: Manhattan-style plots for taxon-cognitive associations

## User Stories

### User Story 1: Data Download and Preprocessing (P1)
- Download UK Biobank microbiome and cognitive data
- Filter cohort (exclude antibiotic users, handle missingness)
- Apply zero-replacement and ILR transformation
- Generate retention logs and age group categorizations

### User Story 2: Statistical Association Analysis (P2)
- Fit Lasso/Ridge regularized models with confounders
- Apply Benjamini-Hochberg correction
- Conduct over-control bias sensitivity analysis
- Validate power requirements

### User Story 3: Interaction Analysis and Visualization (P3)
- Fit age-interaction models
- Generate Manhattan-style plots
- Perform threshold sweep sensitivity analysis
- Compare model selection (Lasso vs Ridge)

## Project Structure

```
.
├── code/
│ ├── analysis.py # Statistical analysis implementation
│ ├── config.py # Configuration and path management
│ ├── download.py # Data download utilities
│ ├── preprocess.py # Preprocessing pipeline
│ ├── visualize.py # Visualization generation
│ ├── power_analysis.py # Power calculation utilities
│ ├── models/ # Data models (Participant, MicrobiomeProfile, etc.)
│ └── utils/ # Utility functions (streaming, hygiene, logging)
├── data/
│ ├── raw/ # Raw downloaded data (parquet files)
│ └── processed/ # Processed data (ILR coordinates, etc.)
├── results/
│ ├── associations/ # Association analysis results
│ ├── sensitivity/ # Sensitivity analysis reports
│ ├── plots/ # Generated visualizations
│ └── validation/ # Validation reports
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── quickstart.md # Quick start guide
└── README.md # This file
```

## Requirements

- Python 3.10+
- UK Biobank access credentials
- Minimum 7GB RAM, 14GB disk space

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Configure UK Biobank token (see `code/utils/credentials.py` or set `UK_BIOBANK_TOKEN` environment variable)

## Usage

See `quickstart.md` for detailed execution steps.

## Validation Gates

- **Power Gate**: T019 validates methodology with synthetic data (power >= 0.8 required)
- **Citation Gate**: T024a validates cognitive instrument citations
- **Data Integrity**: All data files are checksummed and PII-masked

## License

This project is for research purposes only. UK Biobank data usage is subject to their terms and conditions.
