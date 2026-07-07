# Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

**Project ID**: PROJ-554
**Status**: Research Implementation Pipeline

## Overview

This project implements an automated scientific pipeline to characterize exoplanetary atmospheres, specifically focusing on the correlation between water vapor signatures and equilibrium temperature for Hot Jupiters and Super-Earths. The pipeline ingests transmission spectra from the NASA Exoplanet Archive, performs atmospheric retrieval using `petitRADTRANS`, and conducts statistical analysis on censored data to address detection limits and signal-to-noise constraints.

## Scientific Context

Recent reviews (simulated by Marie Curie and Rosalind Franklin personas) have emphasized the necessity of defining:
- **Spectral Resolution (R)**: To distinguish hydration features from noise.
- **Signal-to-Noise Ratio (SNR)**: To establish detection limits for water vapor lines.
- **Data Quantity**: To ensure statistical power (N ≥ 30) for correlation claims.

This pipeline addresses these constraints by:
1. Fetching raw spectra and metadata (including R and SNR) programmatically.
2. Deriving water mixing ratios with uncertainty estimates.
3. Treating low-SNR data as censored upper limits rather than false precision.
4. Computing Kendall's tau for censored data and fitting Tobit regression models.

## Architecture

The project follows a modular structure:

- **`code/`**: Core Python modules.
 - `download.py`: Data acquisition from NASA Exoplanet Archive.
 - `retrieval.py`: Atmospheric retrieval via `petitRADTRANS`.
 - `analysis.py`: Statistical correlation (Kendall's tau, Tobit regression).
 - `utils.py`: Logging, error handling, and censored data helpers.
 - `config.py`: Environment and configuration management.
- **`data/`**:
 - `raw/`: Downloaded spectrum files.
 - `processed/`: Metadata, retrieval results, and analysis outputs.
- **`results/`**: Generated plots and quality reports.
- **`tests/`**: Contract, integration, and unit tests.

## Prerequisites

- Python 3.9+
- `pip` for dependency management
- Access to the internet (for data fetching)

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. (Optional) Set environment variables for API keys if required by specific data sources:
 ```bash
 export NASA_API_KEY="your_key_here"
 ```

## Usage

The pipeline is executed sequentially via the `main` functions in each module, or via the top-level orchestration script.

### 1. Data Acquisition (User Story 1)
Downloads spectra and metadata, validates sample size, and logs SNR/Resolution.
```bash
python code/download.py
```
**Output**: `data/processed/metadata.csv`, `data/raw/` spectrum files.

### 2. Atmospheric Retrieval (User Story 2)
Runs `petitRADTRANS` to derive water abundances and handles censored data.
```bash
python code/retrieval.py
```
**Output**: `data/processed/retrieval_results.csv`.

### 3. Statistical Analysis (User Story 3)
Computes correlations, regression, and detection limits.
```bash
python code/analysis.py
```
**Output**: `data/processed/analysis_results.json`, `results/plots/`.

### 4. Visualization
Generates instrumental noise vs. signal plots.
```bash
python code/plots.py
```

## Data Integrity & Censorship

- **No Synthetic Data**: All data is fetched from the NASA Exoplanet Archive.
- **Censored Data Handling**: Spectra with low SNR are flagged as upper limits (censored) and analyzed using `scikit-survival` and `lifelines` (Tobit models).
- **Validation**: Contract tests ensure metadata schema compliance before analysis.

## Review Compliance

This implementation specifically addresses reviewer concerns regarding:
- **Detection Limits**: Explicit calculation of detection limits based on SNR and Resolution (Task T035).
- **Instrumental Noise**: Visualization of noise vs. signal distributions (Task T036).
- **Robustness**: Leave-one-out correlation checks to verify result stability (Task T037).

## License

Research code for the characterization of exoplanetary atmospheres.
