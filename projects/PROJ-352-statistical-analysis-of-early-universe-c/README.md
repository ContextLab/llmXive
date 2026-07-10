# Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

This project implements a comprehensive pipeline for analyzing Cosmic Microwave Background (CMB) temperature anisotropies from the Planck mission data. The analysis focuses on detecting potential signatures of topological defects (such as cosmic strings) through Minkowski Functionals and statistical hypothesis testing.

## Research Question

Can Minkowski functionals and statistical measures of CMB anisotropies constrain topological defect energy scales?

## Key Features

- **Data Acquisition**: Download and validate Planck 2015/2018 SMICA CMB maps
- **Preprocessing**: Apply Galactic masks with pixel buffer zones
- **Minkowski Functionals**: Compute area, perimeter, and genus functionals at multiple thresholds
- **Simulations**: Generate Gaussian random fields and cosmic string template realizations
- **Statistical Testing**: Perform likelihood ratio tests to compare observed data against null and alternative hypotheses

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-352-statistical-analysis-of-early-universe-c

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
.
├── code/ # Source code
│ ├── __init__.py
│ ├── config.py # Configuration management
│ ├── download.py # Data download and validation
│ ├── mask.py # Mask application and processing
│ ├── minkowski.py # Minkowski Functional computation
│ ├── simulate.py # Simulation generation
│ ├── statistics.py # Statistical analysis
│ └── setup_*.py # Setup utilities
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data products
├── output/
│ ├── figures/ # Generated plots
│ └── logs/ # Execution logs
├── tests/ # Test suite
│ ├── __init__.py
│ └── test_*.py
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quick Start

### 1. Download CMB Data

```bash
python code/download.py
```

This will download the Planck SMICA map and validate its checksum.

### 2. Apply Mask and Compute Statistics

```bash
python code/mask.py
```

### 3. Compute Minkowski Functionals

```bash
python code/minkowski.py
```

### 4. Run Full Analysis Pipeline

```bash
python code/pipeline.py
```

## Configuration

All analysis parameters are managed through `code/config.py`. Key parameters include:

- `nside`: HEALPix resolution parameter (default: 128)
- `beam_fwhm_arcmin`: Beam smoothing (default: 5.0 arcmin)
- `noise_sigma_uK`: Noise level (default: 1.1 μK)
- `random_seed`: Reproducibility seed (default: 42)

To customize settings, modify the `Config` class in `code/config.py` or use the `update_config()` function.

## Testing

Run the test suite with:

```bash
pytest tests/ -v --cov=code
```

## Dependencies

- `healpy`: HEALPix Python bindings
- `numpy`: Numerical computing
- `scipy`: Scientific computing
- `scikit-learn`: Machine learning utilities
- `requests`: HTTP library for data download
- `astropy`: Astronomy utilities
- `matplotlib`: Plotting library
- `pytest`: Testing framework

## License

This project is part of the llmXive automated science pipeline.

## Acknowledgments

- Planck Collaboration: For providing the CMB data
- HEALPix project: For the pixelization framework
- Schmalzing & Gorski (1998): For mask correction methodology