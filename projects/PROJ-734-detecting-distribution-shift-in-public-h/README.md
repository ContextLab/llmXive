# Detecting Distribution Shift in Public Health Surveillance Data

This project implements an automated pipeline to detect distribution shifts in public health surveillance data (specifically CDC FluView ILI data) using Kernel Two-Sample Tests (Maximum Mean Discrepancy - MMD). It compares MMD performance against baseline change-point detection methods (Pettitt test and BOCPD).

## Features

- **Automated Shift Detection**: Uses Gaussian-kernel MMD with multi-week windows to identify weeks where the ILI distribution has significantly changed.
- **Baseline Comparisons**: Implements Pettitt rolling-window test and Bayesian Online Change-Point Detection (BOCPD) for comparison.
- **Robustness & Sensitivity Analysis**: Evaluates sensitivity to kernel bandwidth, window length, and week-alignment tolerance.
- **Real Data Integration**: Fetches real CDC FluView ILI data and ground truth events directly from official sources.
- **Reproducible Reporting**: Generates a comprehensive PDF report with metrics, plots, and sensitivity analysis.

## Prerequisites

- Python 3.8+
- pip package manager
- Access to the internet (to download CDC data)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd detecting-distribution-shift
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── __init__.py
│ ├── main.py # Main entry point
│ ├── config.yaml # Configuration file
│ ├── download_data.py # Data fetching scripts
│ ├── preprocess.py # Data preprocessing
│ ├── mmd_detector.py # MMD-based shift detection
│ ├── pettitt.py # Pettitt test implementation
│ ├── bocpd.py # BOCPD implementation
│ ├── evaluate.py # Evaluation metrics
│ ├── sensitivity.py # Sensitivity analysis
│ ├── report_generator.py # PDF report generation
│ └──... # Other modules
├── data/
│ ├── raw/ # Raw downloaded data
│ │ ├── fluview_ili.csv
│ │ └── ground_truth_events.csv
│ └── processed/ # Processed data
├── tests/ # Unit and integration tests
├── contracts/ # Data schemas
├── specs/ # Design documents
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Quick start guide
```

## Usage

### Quick Start

See [quickstart.md](quickstart.md) for a step-by-step guide to running the pipeline.

### Running the Full Pipeline

1. **Download Data**:
 ```bash
 python code/download_data.py
 ```
 This fetches CDC FluView ILI data and ground truth events, saving them to `data/raw/`.

2. **Run the Pipeline**:
 ```bash
 python code/main.py
 ```
 This executes the full pipeline:
 - Preprocessing
 - MMD shift detection
 - Baseline comparisons (Pettitt, BOCPD)
 - Evaluation against ground truth
 - Sensitivity analysis
 - Report generation

3. **Outputs**:
 - `data/processed/flags.csv`: Flagged weeks with distribution shifts
 - `data/processed/baselines.csv`: Baseline change-point detections
 - `data/processed/sensitivity.csv`: Sensitivity analysis results
 - `figures/report.pdf`: Comprehensive PDF report

### Running Tests

```bash
pytest tests/
```

## Configuration

Edit `code/config.yaml` to adjust parameters:
- `seed`: Random seed for reproducibility
- `permutations`: Number of permutations for MMD p-value estimation
- `window_size`: Size of the sliding window for analysis
- `stride`: Step size between windows
- `alpha`: Significance level for Bonferroni correction

## Data Sources

- **CDC FluView ILI Data**: Downloaded directly from the CDC API or verified direct CSV source.
- **Ground Truth Events**: Sourced from CDC Virological/Hospitalization data.

The pipeline enforces data integrity by validating checksums and raising `E-NO-DATA` if real CDC data cannot be fetched.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please follow the project's coding standards and ensure all tests pass before submitting pull requests.
