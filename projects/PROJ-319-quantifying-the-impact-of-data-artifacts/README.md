# Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

This project investigates how common data artifacts (noise and saturation) bias the measurement of planetary nebula morphology parameters (ellipticity and asymmetry). Using synthetic data with known ground truth, we quantify these biases and derive calibration functions to correct them.

## Project Structure

```
PROJ-319-quantifying-the-impact-of-data-artifacts/
├── code/ # Source code
│ ├── analysis/ # Statistical analysis and regression
│ ├── io/ # Input/output utilities
│ ├── metrics/ # Morphology metric calculations
│ ├── synthetic/ # Synthetic data generation and artifact injection
│ ├── config.py # Project configuration and parameters
│ ├── main.py # CLI entry point
│ └── setup_dirs.py # Directory initialization
├── data/ # Data artifacts
│ ├── raw/ # Raw input data
│ ├── synthetic/ # Generated synthetic planetary nebulae
│ ├── processed/ # Processed data and analysis results
│ └── validation/ # Validation data and reports
├── docs/ # Documentation
│ ├── decisions/ # ADRs
│ └── reports/ # Final research reports
├── logs/ # Execution logs
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ ├── contract/ # Contract tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
├── quickstart.md # Quick start guide
├── research.md # Research documentation
└── README.md # This file
```

## Quick Start

See [quickstart.md](quickstart.md) for detailed instructions on running the full pipeline.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python code/main.py --run-all

# Or run specific modes
python code/main.py --mode generate --n-images 50
python code/main.py --mode process
python code/main.py --mode calibrate
python code/main.py --mode validate
```

## Key Components

- **Synthetic Data Generation** (`code/synthetic/generator.py`): Creates realistic planetary nebulae with known ground-truth ellipticity and asymmetry.
- **Artifact Injection** (`code/synthetic/artifacts.py`): Injects controlled noise and saturation artifacts.
- **Metric Calculation** (`code/metrics/`): Computes ellipticity (second-order moments) and asymmetry (Conselice 2003).
- **Statistical Analysis** (`code/analysis/`): Performs regression analysis to quantify bias and derive calibration functions.
- **Validation** (`code/analysis/validation.py`): Applies corrections and validates residual bias.

## Configuration

Key parameters are defined in `code/config.py`:
- Random seeds for reproducibility
- Artifact ranges: noise levels `{0.01, 0.05, 0.10}`, saturation `0.0` to `0.5` in `0.05` increments
- Default paths for data and outputs

## Validation

- **Qualitative**: Real HST images (NGC 7009, NGC 6543) validated against known morphologies (see `data/validation/`).
- **Quantitative**: Synthetic data with known ground truth used to measure bias.
- **Statistical**: Power analysis and cross-validation ensure robustness.

## License

This project is part of the llmXive automated science pipeline.
