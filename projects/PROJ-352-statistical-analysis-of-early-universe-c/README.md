# Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

**Project ID:** PROJ-352
**Status:** Active Research Pipeline

## Overview

This project implements a reproducible, automated scientific pipeline to analyze Cosmic Microwave Background (CMB) temperature anisotropies from the Planck Legacy Archive. The primary objective is to constrain the energy scale of topological defects (e.g., cosmic strings) by computing Minkowski Functionals (Area, Perimeter, Genus) on masked CMB maps and comparing observed statistics against Gaussian Random Field (GRF) null hypotheses and defect-based alternative hypotheses.

The pipeline adheres to strict data integrity protocols: all input data is fetched directly from the Planck Legacy Archive, validated via checksums, and processed with documented edge-case handling (2-pixel buffer zones).

## Key Features

- **Data Acquisition:** Automated download and validation of Planck 2015/2018 SMICA CMB maps (Nside=128) with exponential backoff retry logic.
- **Preprocessing:** Application of Galactic masks and pixel buffer zones to minimize edge artifacts.
- **Topology Analysis:** Computation of Minkowski Functionals across multiple threshold levels.
- **Statistical Testing:** Likelihood Ratio Tests comparing observed data against Gaussian and Cosmic String simulations.
- **Reproducibility:** Deterministic random seeds, versioned dependencies, and full provenance tracking.

## Prerequisites

- **Python:** 3.9 or higher
- **System Dependencies:** `libcfitsio` (required for `healpy`), `gcc`, `gfortran`
- **Hardware:** Minimum 8GB RAM recommended for simulation phases; no GPU required.

## Installation

1. **Clone the repository:**
 ```bash
 git clone <repository-url>
 cd PROJ-352-statistical-analysis-of-early-universe-c
 ```

2. **Create a virtual environment:**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies:**
 Ensure `libcfitsio` is installed on your system (e.g., `sudo apt-get install libcfitsio-dev` on Ubuntu).
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

## Project Structure

```text
.
├── code/ # Core implementation modules
│ ├── __init__.py
│ ├── config.py # Configuration management
│ ├── download.py # Planck data acquisition
│ ├── mask.py # Mask application and buffering
│ ├── minkowski.py # Minkowski Functional computation
│ ├── simulate.py # Gaussian and String simulations
│ ├── statistics.py # Covariance estimation and LRT
│ └── setup_logging.py # Logging infrastructure
├── data/
│ ├── raw/ # Downloaded FITS files (auto-generated)
│ └── processed/ # Masked maps, stats, and reports
├── tests/ # Unit and integration tests
├── output/ # Final analysis results and plots
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage

### 1. Setup Environment
Run the initialization scripts to create directory structures and configure logging:
```bash
python code/setup_structure.py
python code/setup_logging.py
```

### 2. Download Data
Fetch the SMICA CMB map and Galactic mask from the Planck Legacy Archive:
```bash
python code/download.py
```
*Outputs:* `data/raw/COM_CMB_ILM-NR1-000_R2.01.fits`

### 3. Preprocess Map
Apply the Galactic mask and buffer zone:
```bash
python code/mask.py --input data/raw/COM_CMB_ILM-NR1-000_R2.01.fits
```
*Outputs:* `data/processed/masked_cmb_n128.fits`, `data/processed/coverage_report.json`

### 4. Compute Minkowski Functionals
Calculate Area, Perimeter, and Genus at specified thresholds:
```bash
python code/minkowski.py --input data/processed/masked_cmb_n128.fits
```
*Outputs:* `data/processed/minkowski_functionals_observed.json`

### 5. Statistical Analysis (Optional)
Run the full simulation and hypothesis testing pipeline:
```bash
python code/simulate.py --n-sims 1000
python code/statistics.py
```
*Outputs:* `output/results.json`

## Testing

Run the test suite to verify pipeline integrity:
```bash
pytest tests/ -v
```

## Configuration

Default paths and parameters are managed in `code/config.py`. To override:
```python
from code.config import update_config
update_config({"data_dir": "/path/to/custom/data"})
```

## Contributing

This is a research pipeline. Please ensure all new modules include:
- Docstrings describing inputs/outputs
- Unit tests in `tests/`
- Logging via `code/setup_logging.py`

## License

Research use only. See project specifications for data usage rights regarding Planck Legacy Archive data.

## References

- Planck Collaboration, "Planck 2018 results. IV. Diffuse component separation", A&A, 2020.
- Schmalzing, J., & Gorski, K. M. (1998). "Minkowski functionals used in the morphological analysis of cosmic microwave background anisotropy maps". MNRAS.
- Wiegand, A., & Hauser, M. (2018). "The genus of the CMB: A new look at the Planck data".