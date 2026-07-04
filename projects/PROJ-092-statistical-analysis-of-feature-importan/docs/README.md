# Statistical Analysis of Feature Importance Drift in Pre-trained Models

## Project Overview

This project implements a pipeline to detect and quantify statistical drift in feature importance rankings over time using pre-trained Random Forest models. The system processes the UCI Electricity Load Diagrams dataset, splits it into sequential time windows, trains models, and analyzes drift using Spearman rank correlation and Mann-Kendall trend tests.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- CPU-only execution environment (no GPU required)

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

```bash
pip install -r code/requirements.txt
```

3. Ensure the data directory structure exists:
 - `data/raw/` (for downloaded datasets)
 - `data/processed/` (for windowed data)
 - `outputs/` (for generated reports and metrics)

## Usage

### Running the Full Pipeline

Execute the main pipeline script to process all data windows, train models, and compute importance profiles:

```bash
python code/main.py
```

This will:
1. Download and verify the UCI Electricity Load Diagrams dataset (if not present).
2. Preprocess data (handle missing values, check variance, split into 30-day windows).
3. Train Random Forest models on each window.
4. Calculate permutation importance for each model.
5. Save importance profiles to `outputs/importance_profiles.csv`.

### Drift Analysis

After generating importance profiles, run the drift analysis to compute Spearman rank correlations between consecutive windows:

```bash
python code/drift_analysis.py
```

This generates:
- `outputs/drift_metrics.csv`: Pairwise drift metrics (rho, p-value)
- `outputs/null_baseline.json`: Baseline statistics from shuffled data
- `outputs/high_drift_flags.json`: Flags for significant drift events

### Significance Testing

Run statistical significance tests on the correlation sequence:

```bash
python code/significance_test.py
```

This performs:
- Mann-Kendall trend test (returns Kendall's Tau)
- Block permutation test (returns p-value)

### Final Report Generation

Generate the aggregated final report:

```bash
python code/generate_final_report.py
```

Output: `outputs/global_stats.json` containing:
- `mean_rho`: Average Spearman correlation
- `trend_direction`: "monotonic increase", "monotonic decrease", or "no trend"
- `p_value`: Block permutation p-value
- `stable_window_count`: Number of windows with valid model performance

### Null Model Baseline

Generate the null baseline for significance testing:

```bash
python code/null_baseline.py
```

This shuffles window order and recalculates correlations to establish a baseline distribution.

## Project Structure

```
PROJ-092-statistical-analysis-of-feature-importan/
├── code/
│ ├── download.py # Dataset fetching and verification
│ ├── preprocess.py # Data cleaning and windowing
│ ├── train_and_importance.py # Model training and importance calculation
│ ├── drift_analysis.py # Spearman correlation and drift metrics
│ ├── significance_test.py # Mann-Kendall and permutation tests
│ ├── null_baseline.py # Null model baseline generation
│ ├── generate_final_report.py # Aggregation and reporting
│ ├── main.py # Pipeline orchestration
│ ├── setup_directories.py # Directory initialization
│ └── utils/
│ ├── config.py # Configuration management
│ ├── logger.py # Logging setup
│ └── stats_aggregator.py # Statistical aggregation utilities
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Preprocessed windowed data
├── outputs/
│ ├── importance_profiles.csv
│ ├── drift_metrics.csv
│ ├── null_baseline.json
│ ├── high_drift_flags.json
│ └── global_stats.json
├── docs/
│ └── README.md # This documentation
├── tests/
│ └── conftest.py # Pytest configuration
├── requirements.txt # Python dependencies
└── tasks.md # Task tracking and implementation plan
```

## Configuration

Configuration is managed via `code/utils/config.py`. Environment variables can override defaults:

- `DATA_DIR`: Path to data directory (default: `data/`)
- `OUTPUT_DIR`: Path to output directory (default: `outputs/`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`)

## Testing

Run the test suite:

```bash
pytest tests/
```

## Key Features

- **Windowed Analysis**: Processes data in sequential 30-day windows to capture temporal evolution.
- **Model Validation**: Skips windows where model R² < 0.8 to ensure reliability.
- **Drift Quantification**: Uses Spearman rank correlation to measure importance ranking changes.
- **Statistical Rigor**: Implements Mann-Kendall trend test and block permutation significance testing.
- **Null Baseline**: Generates baseline distribution by shuffling window order to validate drift significance.

## Dependencies

See `code/requirements.txt` for the full list of pinned dependencies.

## License

[Add license information here]
