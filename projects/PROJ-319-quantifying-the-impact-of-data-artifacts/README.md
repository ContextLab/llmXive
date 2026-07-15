# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

**Project ID:** PROJ-319-quantifying-the-impact-of-data-artifacts

## Overview

This research pipeline quantifies how instrumental data artifacts—specifically **Gaussian noise** and **pixel saturation**—bias morphological measurements (ellipticity and asymmetry) of Planetary Nebulae (PNe).

Using high-fidelity synthetic planetary nebulae with known ground-truth morphology, we systematically inject controlled levels of noise and saturation. We then measure the deviation in derived metrics to:
1. **Quantify Bias:** Determine the magnitude and direction of bias introduced by specific artifact levels.
2. **Statistical Significance:** Apply rigorous statistical testing (t-tests with Bonferroni correction) to confirm that observed biases are non-random.
3. **Derive Calibration:** Fit regression models to generate correction functions that can de-bias real observational data.

This project adheres to the **llmXive** automated science pipeline principles, ensuring reproducibility, deterministic synthetic data generation, and strict separation of data, code, and analysis.

## Repository Structure

```text
.
├── code/ # Core Python modules
│ ├── analysis/ # Statistical tests and regression models
│ ├── io/ # FITS loading, validation, and writing
│ ├── metrics/ # Ellipticity and Asymmetry calculation
│ ├── synthetic/ # Nebula generation and artifact injection
│ ├── config.py # Global configuration and seeds
│ └── main.py # Pipeline orchestration (entry point)
├── data/
│ ├── raw/ # Real observational data (HST/MST) if available
│ ├── synthetic/ # Generated synthetic images and ground truth JSONs
│ ├── processed/ # Artifact-injected images and measurement results
│ └── validation/ # Manual validation datasets
├── logs/ # Execution logs and statistical reports
├── tests/ # Unit, contract, and integration tests
├── README.md # This file
├── requirements.txt # Python dependencies
└── quickstart.md # Detailed step-by-step execution guide
```

## Quickstart Guide

### 1. Environment Setup

Ensure you are using Python 3.11 or higher.

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Project Initialization

Run the setup script to create the required directory structure.

```bash
python code/setup_dirs.py
```

*This creates: `code/`, `data/`, `logs/`, and `tests/` subdirectories.*

### 3. Generate Synthetic Ground Truth

Before running the pipeline, generate the baseline synthetic planetary nebulae with known ground-truth ellipticity and asymmetry.

```bash
python code/synthetic/generator.py
```

**Output:**
- `data/synthetic/nebula_base.fits`: Clean synthetic image.
- `data/synthetic/gt_metadata.json`: Ground truth parameters (Single Source of Truth).

### 4. Run the Artifact Injection & Measurement Pipeline

Execute the main pipeline to inject noise/saturation, measure metrics, and log bias.

```bash
python code/main.py
```

**Expected Outputs:**
- `data/processed/noise_sweep_{sigma}.fits`: Images with injected noise.
- `data/processed/saturation_sweep_{fraction}.fits`: Images with clipped saturation.
- `logs/stats_results.csv`: Statistical significance of bias.
- `logs/research.log`: Detailed run logs.

### 5. Verification & Testing

Run the test suite to ensure all components (loading, metrics, artifact injection) are functioning correctly.

```bash
pytest tests/ -v
```

### 6. Derive Calibration Functions

Once data is collected, run the analysis module to fit regression models and generate calibration functions.

```bash
python code/analysis/regression.py
```

**Output:**
- `data/processed/calibration_functions.json`: Corrective models for ellipticity and asymmetry.

## Key Dependencies

- **numpy**: Numerical operations
- **scikit-image**: Image processing
- **astropy**: FITS handling and WCS
- **scipy**: Statistical tests
- **statsmodels**: Regression analysis
- **pandas**: Data manipulation
- **matplotlib**: Visualization
- **pytest**: Testing framework

## License

This project is part of the llmXive automated science research initiative.