# Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Project Overview

This project investigates the validity of statistical significance in Randomized Controlled Trials (RCTs) when data is missing. It simulates three missingness mechanisms (MCAR, MAR, MNAR), compares analysis methods (Complete-Case, Multiple Imputation, Inverse Probability Weighting), and identifies "tipping points" where statistical validity breaks down.

## Prerequisites

- Python 3.11+
- pip (Python package manager)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```text
.
├── code/ # Source code modules
│ ├── analysis.py # Analysis methods (CC, MI, IPW)
│ ├── config.py # Configuration handling
│ ├── data_loader.py # Real data loading from OpenML
│ ├── main.py # Main execution logic
│ ├── metrics.py # Statistical metrics and error rates
│ ├── simulation.py # Missing data simulation logic
│ ├── visualize.py # Plotting utilities
│ └──...
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/ # Simulation results (JSON/CSV)
├── tests/ # Unit and integration tests
├── contracts/ # JSON schemas for data contracts
├── requirements.txt # Python dependencies
└── README.md
```

## Execution Instructions

### 1. Configuration

Before running simulations, ensure you have a valid configuration. You can create a `config.json` file in the project root or use defaults.

Example `config.json`:

```json
{
 "dataset_id": 538,
 "mechanism": "MAR",
 "missing_rate": 0.2,
 "outcome_type": "continuous",
 "iterations": 500,
 "seed": 42
}
```

### 2. Running User Story 1: Type I Error Simulation

To simulate a single condition (e.g., MAR mechanism, 20% missingness) and calculate empirical Type I error:

```bash
python code/main_us1.py --config config.json
```

**Output**: `data/processed/us1_results.json` containing p-value distribution and error rates.

### 3. Running Power Analysis (Alternative Hypothesis)

To evaluate statistical power under a specific effect size (Cohen's d=0.5):

```bash
python code/main_power_analysis.py --config config.json
```

**Output**: `data/processed/power_results.json`.

### 4. Running Sensitivity Analysis (Tipping Points)

To sweep across multiple missingness rates and identify tipping points:

```bash
python code/main.py --mode sensitivity --config config.json
```

**Output**: `data/processed/sensitivity_results.json` and tipping point reports.

### 5. Running Method Comparison (CC vs MI vs IPW)

To compare analysis methods under a specific condition:

```bash
python code/main.py --mode comparison --config config.json
```

**Output**: `data/processed/comparison_results.json`.

### 6. Visualization

Generate plots for error rates and method comparisons:

```bash
python code/visualize.py --input data/processed/sensitivity_results.json
```

**Output**: Figures saved in `figures/` directory.

## Seed Handling

All simulations use a deterministic random seed for reproducibility.
- **Default Seed**: 42
- **Override**: Set the `seed` field in your configuration JSON or pass `--seed <value>` if the script supports it.

Example:
```json
{
 "seed": 12345,
 "iterations": 1000
}
```

## Expected Outputs

All output artifacts are written to `data/processed/` or `figures/`:

- `us1_results.json`: Empirical Type I error rates and p-value distributions.
- `power_results.json`: Statistical power estimates under alternative hypothesis.
- `sensitivity_results.json`: Error rates across missingness rates.
- `comparison_results.json`: Comparison of CC, MI, and IPW methods.
- `tipping_point_report.json`: Specific rates where CC analysis fails validity thresholds.

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Run specific test suites:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Data Loading Constraints

- **Real Data Only**: This project strictly loads real RCT datasets from OpenML.
- **No Synthetic Fallbacks**: If a dataset cannot be fetched or validated, the `data_loader` will raise a `DataLoadError`. Do not expect synthetic data generation.
- **Minimum Size**: Datasets with N < 100 are skipped with a warning.

## Dependencies

See `requirements.txt` for the full list of dependencies, including:
- `openml` (Data retrieval)
- `scikit-learn`, `scipy`, `statsmodels` (Statistical analysis)
- `miceforest` (Multiple Imputation)
- `pandas`, `numpy` (Data manipulation)
- `matplotlib`, `seaborn` (Visualization)

## License

[Insert License Here]