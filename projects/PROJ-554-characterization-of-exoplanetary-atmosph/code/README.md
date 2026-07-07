# Code Module Documentation

This directory contains the core Python implementation for the exoplanetary atmosphere characterization pipeline.

## Module Overview

- **`config.py`**: Handles environment variables, random seeds, and path configuration.
- **`utils.py`**: Provides logging setup, custom exceptions, retry logic, and censored data helpers.
- **`data_models.py`**: Defines dataclasses for `ExoplanetSpectrum` and `RetrievalResult`.
- **`api_config.py`**: Defines query parameters for the NASA Exoplanet Archive.
- **`download.py`**: Orchestrates data fetching, metadata parsing, and sample size validation.
- **`retrieval.py`**: Wraps `petitRADTRANS` for CPU-optimized retrieval and handles convergence failures.
- **`analysis.py`**: Implements censored Kendall's tau, Tobit regression, and detection limit calculations.
- **`plots.py`**: Generates visualization artifacts for SNR and resolution analysis.
- **`validation.py`**: Contains tests for upper limit flags and data quality.

## Execution Flow

1. **Initialization**: `config.py` loads settings; `utils.py` configures logging.
2. **Ingestion**: `download.py` fetches data to `data/raw/` and `data/processed/metadata.csv`.
3. **Processing**: `retrieval.py` processes spectra to `data/processed/retrieval_results.csv`.
4. **Analysis**: `analysis.py` computes statistics and saves to `data/processed/analysis_results.json`.
5. **Visualization**: `plots.py` creates figures in `results/plots/`.

## Dependencies

See `requirements.txt` for the full list. Key libraries:
- `petitRADTRANS`: Atmospheric retrieval.
- `scikit-survival`: Censored statistical analysis.
- `lifelines`: Tobit regression.
- `pandas`, `numpy`, `scipy`: Data manipulation.
