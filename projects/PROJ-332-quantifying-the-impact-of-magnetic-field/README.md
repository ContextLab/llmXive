# Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Project Overview

This project analyzes DIII-D tokamak discharge data to quantify the relationship between magnetic field topology (specifically island width and resonant surface density) and plasma energy confinement time (tau_e). The analysis aims to validate the hypothesis that increased magnetic island width correlates with degraded confinement.

## Architecture

The project follows a modular pipeline architecture:

```
PROJ-332-quantifying-the-impact-of-magnetic-field/
├── code/
│ ├── data/ # Data retrieval, preprocessing, validation
│ ├── analysis/ # Metrics calculation, correlation, power analysis
│ ├── utils/ # Logging, timeouts, memory monitoring
│ ├── viz/ # Visualization utilities
│ └── main.py # Entry point
├── data/
│ ├── raw/ # Raw data from MDSplus
│ ├── intermediate/ # Intermediate processed data
│ └── processed/ # Final unified datasets
├── outputs/ # Final reports, plots, summaries
├── tests/ # Unit and integration tests
├── contracts/ # Schema definitions
└──.github/
 └── workflows/ # CI/CD pipelines
```

### Key Components

1. **Data Retrieval (`code/data/retrieval.py`)**: Connects to MDSplus archive, fetches EFIT, island, tau_e, and h98y2 data with retry logic.
2. **Preprocessing (`code/data/preprocessing.py`)**: Parses time-series data, calculates confinement mode, and creates unified datasets.
3. **Metrics (`code/analysis/metrics.py`)**: Calculates resonant surface density, derives island width from EFIT if needed, and validates ranges.
4. **Correlation (`code/analysis/correlation.py`)**: Performs Spearman rank correlation with bootstrap resampling, stratification, and multicollinearity checks.
5. **Reporting (`code/analysis/report_generator.py`)**: Generates final JSON reports and diagnostic plots.

## Workflow

1. **Setup**: Initialize directories and dependencies.
2. **Retrieval**: Fetch DIII-D discharge data from MDSplus.
3. **Preprocessing**: Parse and validate data, calculate confinement mode.
4. **Metrics**: Compute topological metrics (island width, resonant surface density).
5. **Analysis**: Perform power analysis, multicollinearity check, and correlation.
6. **Reporting**: Generate summary reports and visualizations.

## Dependencies

- Python 3.11+
- scipy, numpy, matplotlib, pandas, pytest, requests, pyyaml

## License

[License information]
