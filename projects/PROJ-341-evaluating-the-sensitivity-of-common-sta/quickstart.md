# Quickstart Guide

This guide provides instructions to run the full simulation pipeline and generate the validation report for the "Evaluating the Sensitivity of Common Statistical Tests to Dataset Size" project.

## Prerequisites

- Python 3.8+
- Required packages installed (see `requirements.txt`)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-341-evaluating-the-sensitivity-of-common-sta
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Full Simulation

The main entry point `code/main.py` orchestrates the entire simulation grid. It iterates through sample sizes (n=5 to n=500), effect sizes, and hypothesis states, executing t-tests, ANOVA, and chi-squared tests.

### Basic Execution

To run the full simulation with default parameters:

```bash
python code/main.py
```

This will:
1. Generate synthetic data for all conditions (n=5..500, effect sizes, null/alt hypotheses)
2. Execute statistical tests (t-test, ANOVA, chi-squared) with appropriate fallbacks
3. Save raw p-values to `data/simulation/p_values_raw.csv`
4. Aggregate results and save error rates to `data/simulation/error_rates_summary.csv`
5. Compute thresholds and save to `data/simulation/thresholds.json`
6. Generate visualizations in `data/visualization/`

### Custom Parameters

You can customize the simulation using command-line arguments:

```bash
python code/main.py --sample-sizes 5,10,20,50 --effect-sizes 0.2,0.5,0.8 --test-type t-test --alpha 0.05
```

Available arguments:
- `--sample-sizes`: Comma-separated list of sample sizes (default: 5,10,15,...,500)
- `--effect-sizes`: Comma-separated list of effect sizes (default: 0.2, 0.5, 0.8)
- `--test-type`: Specific test to run (t-test, anova, chi-squared, or all)
- `--alpha`: Significance threshold (default: 0.05)
- `--iterations`: Number of iterations per condition (default: 10000)

## Generating the Validation Report

After the simulation completes, run the validation pipeline to compare simulated results against real-world datasets:

```bash
python code/analysis/validator.py
```

This step:
1. Downloads real datasets (UCI Breast Cancer, Wine, Adult) using `ucimlrepo`
2. Verifies dataset integrity via checksums
3. Runs statistical tests on real data
4. Performs bootstrapped power estimation
5. Calculates KS distance between simulated and real p-value distributions
6. Generates the validation report at `data/reports/validation_report.md`

### Validation Report Contents

The generated `data/reports/validation_report.md` includes:
- Summary of simulation findings
- Comparison of simulated vs. real data p-value distributions
- KS distance metrics and pass/fail status
- Identified reliability thresholds
- Recommendations for small-sample statistical testing

## Output Files

After successful execution, the following files will be generated:

- `data/simulation/p_values_raw.csv`: Raw p-values from all simulation iterations
- `data/simulation/error_rates_summary.csv`: Aggregated Type I and Type II error rates
- `data/simulation/thresholds.json`: Identified sample size thresholds for reliability
- `data/simulation/real_data_pvalues.csv`: P-values from real dataset tests
- `data/simulation/real_data_power.json`: Bootstrapped power estimates and KS distances
- `data/simulation/validation_metrics.json`: Aggregated validation metrics
- `data/visualization/*.png`: Visualization plots
- `data/reports/validation_report.md`: Final validation report

## Troubleshooting

### Memory Issues

If you encounter memory errors, reduce the number of iterations:
```bash
python code/main.py --iterations 1000
```

### Missing Dependencies

Ensure all required packages are installed:
```bash
pip install numpy scipy pandas matplotlib seaborn statsmodels scikit-learn requests ucimlrepo openml
```

### Checksum Verification Failures

If dataset checksum verification fails, the download may be corrupted. Re-run the validator to re-download:
```bash
python code/analysis/validator.py --force-download
```

## Next Steps

After generating the validation report, review `data/reports/validation_report.md` to understand:
- Whether simulation findings hold true for real-world data
- The reliability thresholds for different statistical tests
- Recommendations for small-sample statistical analysis

For detailed API documentation, refer to the docstrings in each module.