# Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

## Overview

This project implements a reproducible pipeline to detect distribution shifts in public health surveillance data (specifically CDC FluView ILI data) using Kernel Maximum Mean Discrepancy (MMD) tests. The pipeline compares the performance of MMD against baseline change-point detection methods (Pettitt test and Bayesian Online Change-Point Detection) and performs sensitivity analysis on key hyperparameters.

## Key Features

- **Automated Shift Detection**: Flags weeks where ILI distribution has changed using Gaussian-kernel MMD with Bonferroni correction
- **Baseline Comparison**: Implements Pettitt rolling-window test and BOCPD (Gaussian observation model)
- **Sensitivity Analysis**: Assesses robustness to kernel bandwidth, window length, and week-alignment tolerance
- **Real Data Pipeline**: Fetches data directly from CDC sources (no synthetic data for final results)
- **Comprehensive Evaluation**: Computes precision, recall, and detection delay metrics against ground truth events

## Project Structure

```
.
├── code/ # Source code
│ ├── main.py # Pipeline orchestration
│ ├── download_data.py # CDC data fetching
│ ├── preprocess.py # Data cleaning and transformation
│ ├── mmd_detector.py # MMD-based shift detection
│ ├── pettitt.py # Pettitt baseline implementation
│ ├── bocpd.py # BOCPD baseline implementation
│ ├── evaluate.py # Metrics calculation
│ ├── sensitivity.py # Sensitivity analysis
│ ├── report_generator.py # PDF report generation
│ └──... # Supporting modules
├── data/
│ ├── raw/ # Raw downloaded data (CDC)
│ └── processed/ # Preprocessed data
├── tests/ # Unit and integration tests
├── contracts/ # Schema definitions
├── data-model.md # Data model documentation
├── plan.md # Project plan
├── quickstart.md # Quick start guide
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Installation

1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Quick Start

See [quickstart.md](quickstart.md) for detailed instructions on running the pipeline.

```bash
# Download real CDC data
python code/download_data.py

# Run the full pipeline
python code/main.py

# Generate sensitivity analysis
python code/sensitivity.py
```

## Configuration

Configuration is managed via `code/config.yaml`:
- `seed`: Random seed for reproducibility
- `permutations`: Number of permutations for MMD p-value estimation
- `window_size`: Sliding window size for analysis
- `stride`: Step size between windows
- `alpha`: Significance level for hypothesis testing

## Data Sources

- **ILI Data**: CDC FluView surveillance data (downloaded via `code/download_data.py`)
- **Ground Truth**: CDC Virological/Hospitalization events (downloaded via `code/download_data.py`)

## Outputs

- `data/processed/flags.csv`: Flagged weeks with distribution shifts
- `data/processed/baselines.csv`: Change points detected by baseline methods
- `data/processed/sensitivity.csv`: Sensitivity analysis results
- `figures/report.pdf`: Comprehensive analysis report with visualizations

## Testing

Run the test suite:
```bash
pytest tests/
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
