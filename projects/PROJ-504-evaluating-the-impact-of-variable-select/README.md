# PROJ-504: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Overview

This project investigates how different variable selection methods (Forward Stepwise, Backward Elimination, LASSO) impact statistical power in linear regression models. We evaluate these methods across diverse real-world datasets from OpenML, varying signal-to-noise ratios (SNR), and sparsity levels.

## Research Question

How does the choice of variable selection method affect the empirical power to detect true non-zero coefficients in linear regression, and under what conditions (SNR, sparsity, collinearity) do certain methods outperform others?

## Methodology

1. **Data Collection**: Fetch 10 diverse regression datasets from OpenML with ≥100 rows and ≥3 predictors.
2. **Simulation**: Generate synthetic outcome vectors across multiple SNR (low to moderate) and sparsity (0.0, 0.2, 0.4) levels with ground-truth coefficients.
3. **Variable Selection**: Apply Forward Stepwise (AIC), Backward Elimination, and LASSO to each simulated dataset.
4. **Power Calculation**: Compute empirical power as the proportion of true non-zero coefficients that are both selected and statistically significant (p < α).
5. **Statistical Comparison**: Use Kruskal-Wallis tests and Dunn's post-hoc analysis (with Holm correction) to compare power rates across methods.
6. **Visualization**: Generate power curves faceted by SNR, sparsity, and alpha thresholds.

## Project Structure

```
projects/PROJ-504-evaluating-the-impact-of-variable-select/
├── code/
│ ├── __init__.py
│ ├── config.py # Configuration management
│ ├── models.py # Data models (SimulatedDataset, PowerMetric)
│ ├── cleanup.py # Code cleanup utilities
│ ├── quickstart_validator.py # Quickstart validation script
│ ├── analysis/
│ │ ├── __init__.py
│ │ ├── selectors.py # Variable selection methods
│ │ ├── metrics.py # Power and collinearity metrics
│ │ └── comparators.py # Statistical comparison tests
│ ├── data/
│ │ ├── __init__.py
│ │ ├── downloader.py # OpenML dataset fetching
│ │ ├── simulators.py # Synthetic outcome generation
│ │ └── storage.py # Results persistence
│ ├── viz/
│ │ ├── __init__.py
│ │ └── plots.py # Visualization generation
│ └── utils/
│ ├── __init__.py
│ ├── logger.py # Logging infrastructure
│ ├── limits.py # Resource constraints
│ └── watchdog.py # Runtime/memory monitoring
├── data/
│ ├── raw/ # Downloaded OpenML datasets
│ └── processed/ # Simulation results and metrics
├── results/
│ ├── plots/ # Generated power curves
│ ├── final_report.md # Comprehensive analysis report
│ └── sensitivity_report.csv # Alpha sensitivity analysis
├── tests/
│ ├── unit/ # Unit tests (TDD-first)
│ ├── integration/ # Integration tests
│ └── contract/ # Schema validation tests
├── docs/ # Additional documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Black configuration
└──.flake8 # Flake8 configuration
```

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Navigate to project root
cd projects/PROJ-504-evaluating-the-impact-of-variable-select/

# Install dependencies
pip install -r requirements.txt

# Validate environment
python code/quickstart_validator.py
```

### Running the Pipeline

```bash
# Run the full simulation and analysis pipeline
python code/data/pipeline.py

# Run statistical comparisons and generate visualizations
python code/analysis/comparators.py

# Generate final report
python code/analysis/report_generator.py
```

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run contract tests
pytest tests/contract/ -v
```

## Configuration

Edit `code/config.py` to customize:

- `seed`: Random seed for reproducibility
- `openml_ids`: List of OpenML dataset IDs to fetch
- `snr_levels`: Signal-to-noise ratio levels to simulate
- `sparsity_levels`: Proportion of true zero coefficients
- `alpha`: Significance threshold for power calculation
- `simulations_per_condition`: Number of simulations per condition

## Key Outputs

- `data/processed/simulation_results.csv`: Individual simulation results (n=24,000)
- `results/plots/`: Power curves and diagnostic plots
- `results/final_report.md`: Comprehensive analysis with statistical tests
- `results/sensitivity_report.csv`: Alpha threshold sensitivity analysis

## Validation & Reproducibility

- **Checksums**: All raw data files have SHA-256 checksums stored in `state/checksums.json`
- **Seed Control**: All simulations use deterministic seeds for reproducibility
- **Resource Monitoring**: Runtime and memory usage tracked via `watchdog.py`
- **Schema Validation**: Results validated against `simulation_result.schema.yaml`

## Performance Constraints

- **Runtime Limit**: 6 hours maximum (enforced by `watchdog.py`)
- **Memory Limit**: 6.5 GB maximum (enforced by `limits.py`)
- **CI Width**: Target < 0.1 for pilot run validation

## References

- OpenML: https://www.openml.org/ (DOI:10.21105/joss.01686)
- Statsmodels: https://www.statsmodels.org/
- Scikit-learn: https://scikit-learn.org/

## License

This project is for research purposes. All data from OpenML is subject to their license terms.
