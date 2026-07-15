# Assessing the Sensitivity of Common Statistical Tests to Dataset Size

This project implements a Monte Carlo simulation pipeline to evaluate how the sensitivity (Type I and Type II error rates) of common statistical tests (t-test, ANOVA, Chi-squared, Fisher's Exact) varies with dataset size and underlying distribution.

## Prerequisites

- Python 3.11+
- pip

## Environment Setup

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (optional but recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Quick Start

The entire pipeline can be executed via the main entry point:

```bash
python code/main.py
```

This command orchestrates the following stages:
1. **Setup**: Ensures output directories exist (`data/raw`, `data/processed`, `logs`).
2. **Data Generation**: Generates synthetic datasets with known ground truth parameters.
3. **Simulation**: Runs adaptive Monte Carlo simulations for various sample sizes, distributions, and statistical tests.
4. **Analysis**: Aggregates results, computes bootstrap confidence intervals, and performs regression analysis.
5. **Visualization**: Generates publication-ready plots.
6. **Export**: Saves final results to CSV and plot files.

## Data Generation (US1)

The data generator creates datasets for Normal, Uniform, and Log-Normal distributions under both Null (effect=0) and Alternative (effect=0.5) hypotheses.

To generate a validation dataset manually:
```bash
python code/run_data_gen.py
```
Output: `data/raw/sample_validation.csv`

## Simulation Execution (US2)

The simulation engine performs adaptive Monte Carlo replicates. It starts with 1000 replicates and extends the count until the 95% Clopper-Pearson confidence interval width is ≤ 0.01 (or hits the maximum cap).

To run the full simulation batch:
```bash
python code/run_simulation.py
```
Or via the main pipeline:
```bash
python code/main.py
```

Outputs:
- `data/processed/error_counts.csv`: Aggregated Type I and Type II error counts.
- `data/processed/raw_pvalues.csv`: Raw p-values for every replicate.

## Visualization (US3)

The visualizer generates plots showing Error Rate vs. Sample Size with confidence interval bands.

To generate all plots:
```bash
python code/visualizer.py
```
Or via the main pipeline (which calls the analyzer and visualizer automatically).

Outputs:
- `data/processed/plots/`: Contains PNG/SVG files of the analysis.

## Interpretation of Results

### Error Rates
- **Type I Error**: The rate at which the test incorrectly rejects the null hypothesis when it is true. Ideally, this should be close to the significance level (α = 0.05).
- **Type II Error**: The rate at which the test fails to reject the null hypothesis when the alternative is true. Lower values indicate higher power.

### Sensitivity Analysis
The generated plots (`data/processed/plots/`) illustrate how these error rates converge as sample size increases.
- **Small Sample Sizes**: Tests may exhibit higher variance in error rates or fail to detect effects (high Type II error).
- **Large Sample Sizes**: Error rates should stabilize near the nominal levels (Type I) or approach 0 (Type II).

### Distribution Impact
Compare curves for Normal, Uniform, and Log-Normal distributions to assess robustness. Deviations from expected behavior in non-normal distributions highlight the sensitivity of parametric tests to distributional assumptions.

### Regression Insights
The `data/processed/stability_trend.csv` and regression coefficients (from `data/processed/error_rates.csv`) quantify the relationship between sample size and error rate deviation, providing a mathematical model of the test's sensitivity.

## Project Structure

```
.
├── code/
│ ├── config.py # Simulation parameters
│ ├── data_generator.py # Synthetic data generation
│ ├── simulation_engine.py # Monte Carlo loop & test execution
│ ├── analyzer.py # Aggregation, CI, regression
│ ├── visualizer.py # Plot generation
│ ├── main.py # Pipeline orchestrator
│ └──... (other scripts)
├── data/
│ ├── raw/ # Raw generated data (e.g., sample_validation.csv)
│ └── processed/ # Simulation results, plots, logs
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt
└── README.md
```

## License

MIT