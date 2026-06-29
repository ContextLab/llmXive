# Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

**Project ID:** PROJ-284-investigating-the-relationship-between-b

## Overview

This project implements an automated pipeline to investigate the relationship between functional brain network dynamics (specifically Participation Coefficient and Within-Module Degree) and individual differences in sensorimotor performance (motor task scores) using data from the Human Connectome Project (HCP).

The pipeline handles data acquisition, preprocessing (including motion correction and normalization), network metric extraction, statistical correlation analysis with covariates, and the generation of publication-quality visualizations and reports.

## Features

- **Automated Data Acquisition:** Fetches HCP data (ICA-FIX or raw) via the HCP API with retry logic and credential management.
- **Preprocessing Pipeline:** Implements motion correction, slice-time correction, normalization to MNI space, and smoothing. Includes tSNR calculation and motion parameter validation.
- **Network Metric Extraction:** Computes functional connectivity matrices (400x400) using the Schaefer atlas and extracts graph metrics (Modularity, Global Efficiency, Participation Coefficient, Within-Module Degree).
- **Statistical Analysis:** Performs correlation analysis (Spearman/Pearson) with Framewise Displacement (FD) as a covariate, applies Benjamini-Hochberg FDR correction, and calculates detectable effect sizes for power analysis.
- **Visualization & Reporting:** Generates scatter plots, network diagrams, and comprehensive Markdown/PDF reports including limitation statements and associational relationship conclusions.
- **Memory Management:** Dynamic batch sizing and memory profiling to respect a 7GB RAM limit.

## Requirements

- Python 3.11+
- FSL (for `mcflirt`, `fslmaths`) - Optional, used for local preprocessing validation.
- AFNI (for `3dTshift`, `3dQwarp`) - Optional, used for local preprocessing validation.
- External dependencies listed in `requirements.txt`.

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Create a `.env` file in the project root or set environment variables for HCP credentials:
- `HCP_USERNAME`: Your HCP username.
- `HCP_PASSWORD`: Your HCP password.

Additional configuration options (e.g., `BATCH_SIZE`, `MEMORY_LIMIT`) are managed in `code/config.py`.

## Usage

### Quick Start

Run the full pipeline (data download, preprocessing, analysis, and reporting):

```bash
python code/main.py
```

*Note: This requires valid HCP credentials and sufficient disk space.*

### Running Specific Modules

- **Download Data:**
 ```bash
 python code/data/download.py
 ```
- **Preprocess Data:**
 ```bash
 python code/data/preprocess.py
 ```
- **Extract Metrics & Run Analysis:**
 ```bash
 python code/data/metrics.py
 python code/analysis/correlations.py
 ```
- **Generate Visualizations:**
 ```bash
 python code/viz/scatter.py
 python code/viz/network.py
 ```
- **Generate Report:**
 ```bash
 python code/report/generate.py
 ```

### Running Tests

```bash
pytest tests/
```

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis and power calculations
│ ├── data/ # Data acquisition and preprocessing
│ ├── viz/ # Visualization generation
│ ├── report/ # Report generation
│ ├── config.py # Configuration management
│ ├── models.py # Data models
│ └── main.py # Entry point
├── data/
│ ├── raw/ # Downloaded raw data
│ ├── processed/ # Preprocessed NIfTI files
│ └── analysis/ # Analysis outputs (CSVs, metrics)
├── docs/ # Documentation
├── logs/ # Pipeline logs
├── templates/ # Report templates
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md
```

## Output Files

- `data/analysis/pca_loadings.csv`: PCA loadings for network metrics.
- `data/analysis/factor_scores.csv`: PCA factor scores per subject.
- `data/analysis/full_metrics.csv`: Combined raw metrics and PCA factors.
- `data/analysis/correlation_results.csv`: Correlation statistics (r, p, q).
- `figures/`: Generated scatter plots and network diagrams.
- `docs/report.md`: Final generated report.

## Limitations

- **Motor Task Performance:** Used as a proxy for proprioceptive accuracy.
- **Associational Relationship:** Findings represent correlational evidence, not causation.
- **Data Availability:** Requires access to HCP data and valid credentials.
- **Preprocessing Tools:** Full local preprocessing requires FSL and AFNI installation.

## Contributing

Please refer to the implementation plan and task list (`tasks.md`) for ongoing development priorities.

## License

[Insert License Here]
