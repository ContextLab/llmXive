# Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

**Project ID**: PROJ-504
**Status**: Research Pipeline Implementation Complete

## Overview

This project implements a rigorous simulation study to evaluate how different variable selection methods (Forward Stepwise, Backward Elimination, and LASSO) impact statistical power in linear regression models. The study uses real-world datasets from OpenML, simulates synthetic outcome vectors across varying Signal-to-Noise Ratio (SNR) and sparsity levels, and computes empirical power rates for each method.

## Research Question

How does variable selection method choice affect the ability to detect true non-zero coefficients (statistical power) across different data conditions (SNR, sparsity, collinearity)?

## Key Features

- **Real Data Pipeline**: Fetches 10 diverse regression datasets from OpenML with validation
- **Simulation Engine**: Generates synthetic outcomes with ground-truth coefficients
- **Selection Methods**: Implements Forward Stepwise, Backward Elimination, and LASSO
- **Power Metrics**: Calculates empirical power, false discovery rates, and collinearity diagnostics
- **Statistical Analysis**: Kruskal-Wallis tests with Dunn's post-hoc (Holm correction)
- **Visualization**: Power curves faceted by SNR, sparsity, and alpha thresholds
- **Reproducibility**: SHA-256 checksums, seed management, and configuration tracking

## Project Structure

```
projects/PROJ-504-evaluating-the-impact-of-variable-select/
├── code/
│ ├── analysis/
│ │ ├── metrics.py # Power calculations, VIF, condition numbers
│ │ ├── selectors.py # Variable selection methods (Stepwise, LASSO)
│ │ └── comparators.py # Statistical tests (Kruskal-Wallis, Dunn)
│ ├── data/
│ │ ├── downloader.py # OpenML dataset fetching with retry logic
│ │ ├── simulators.py # Synthetic outcome generation
│ │ └── storage.py # Parquet/CSV result persistence
│ ├── utils/
│ │ ├── logger.py # Logging infrastructure
│ │ ├── limits.py # CPU/RAM constraints
│ │ └── watchdog.py # Runtime monitoring and early stopping
│ ├── config.py # Configuration management
│ ├── models.py # Data models (SimulatedDataset, PowerMetric)
│ ├── pipeline.py # Main execution pipeline
│ ├── verify.py # Pilot run and validation
│ └── quickstart_validator.py # Quickstart validation checks
├── data/
│ ├── raw/ # Downloaded OpenML datasets
│ └── processed/ # Simulation results, power metrics
├── results/
│ ├── plots/ # Power curves and diagnostic plots
│ ├── sensitivity_report.csv # Alpha sensitivity analysis
│ └── final_report.md # Comprehensive research report
├── tests/
│ ├── unit/ # Unit tests (TDD-first)
│ ├── integration/ # Integration tests
│ └── contract/ # Schema validation tests
├── docs/
│ └── methodology.md # Detailed methodology documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Black formatting config
└──.flake8 # Linting configuration
```

## Installation

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd projects/PROJ-504-evaluating-the-impact-of-variable-select
 ```

2. **Create virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify environment**
 ```bash
 python code/quickstart_validator.py
 ```

## Quickstart

### Run the Full Pipeline

```bash
# 1. Verify pilot run and validate environment
python code/verify.py

# 2. Download datasets and run simulations (Phase 1)
python code/data/pipeline.py --stage download
python code/data/pipeline.py --stage simulate

# 3. Compute power metrics (Phase 2)
python code/analysis/metrics.py

# 4. Statistical comparison and visualization (Phase 3)
python code/analysis/comparators.py

# 5. Generate final report
python code/analysis/comparators.py --report
```

### Run Individual Components

```bash
# Download datasets only
python code/data/downloader.py

# Generate simulations only
python code/data/simulators.py

# Calculate power metrics only
python code/analysis/metrics.py

# Run statistical tests only
python code/analysis/comparators.py
```

## Configuration

Edit `code/config.py` to customize:

- `seed`: Random seed for reproducibility
- `openml_ids`: List of OpenML dataset IDs to fetch
- `snr_levels`: Signal-to-Noise Ratio levels (default: low to moderate)
- `sparsity_levels`: Proportion of zero coefficients (default: {0.0, 0.2, 0.4})
- `simulations_per_condition`: Number of simulations per condition (set by pilot run)
- `alpha_thresholds`: Significance levels for hypothesis testing (default: 0.05)

## Data Flow

1. **Raw Data**: Downloaded from OpenML (10 datasets, ≥100 rows, ≥3 predictors)
2. **Processed Data**: Simulated outcomes with ground-truth coefficients
3. **Results**: Power metrics, selection statistics, collinearity diagnostics
4. **Outputs**: Power curves, statistical test results, final report

## Key Metrics

- **Empirical Power**: Proportion of true non-zero coefficients selected AND significant (p < α)
- **False Discovery Rate**: Proportion of selected zero coefficients that are significant
- **Condition Number**: Measure of multicollinearity in the design matrix
- **VIF (Variance Inflation Factor)**: Per-variable collinearity diagnostic

## Statistical Methods

- **Variable Selection**:
 - Forward Stepwise (AIC criterion)
 - Backward Elimination (AIC criterion)
 - LASSO (L1 regularization)

- **Hypothesis Testing**:
 - Kruskal-Wallis test for method comparison
 - Dunn's post-hoc with Holm correction for multiplicity
 - Sensitivity analysis across α thresholds (0.01, 0.05, 0.10)

## Reproducibility

This project ensures reproducibility through:

- **SHA-256 Checksums**: All raw and processed files are checksummed
- **Seed Management**: All random operations use configurable seeds
- **Configuration Tracking**: Full parameter logging for every run
- **Manifest Generation**: `data/processed/simulation_manifest.json` tracks all runs

Verify reproducibility:
```bash
python code/reproduce.py --verify
```

## Testing

Run all tests:
```bash
pytest tests/ -v --cov=code
```

Run specific test suites:
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests (schema validation)
pytest tests/contract/ -v
```

## Performance Constraints

- **Runtime Limit**: 6 hours total (enforced by `code/utils/watchdog.py`)
- **Memory Limit**: 6.5 GB RAM (enforced by `code/utils/limits.py`)
- **CPU Constraints**: Configurable parallelism based on available vCPUs

## Output Files

| File | Description |
|------|-------------|
| `data/processed/simulation_results.csv` | All simulation-level results (n=24,000) |
| `data/processed/memory_profile.log` | Peak memory usage per batch |
| `results/plots/power_curves.png` | Power vs. SNR curves by method and sparsity |
| `results/sensitivity_report.csv` | Power rates at different α thresholds |
| `results/final_report.md` | Comprehensive research report |
| `state/checksums.json` | SHA-256 checksums for all data files |

## Contributors

- Research Design: [Your Team]
- Implementation: llmXive Automated Science Pipeline
- Validation: TDD-First Testing Protocol

## License

This project is part of the llmXive research initiative. See LICENSE for details.

## References

- OpenML: https://www.openml.org/
- scikit-learn: https://scikit-learn.org/
- statsmodels: https://www.statsmodels.org/
- DOI: 10.21105/joss.01686 (OpenML paper)