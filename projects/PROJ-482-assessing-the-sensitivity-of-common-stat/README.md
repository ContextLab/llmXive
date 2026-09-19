# Assessing the Sensitivity of Common Statistical Tests to Dataset Size

This project implements a Monte Carlo simulation pipeline to evaluate how sample size affects the sensitivity (power) and Type I error rates of common statistical tests: the independent samples t-test, ANOVA, and Chi-squared test.

## Overview

The pipeline generates synthetic datasets with known ground truth (null and alternative hypotheses) across a range of sample sizes and distributions (Normal, Uniform, Log-Normal). It then executes statistical tests using adaptive Monte Carlo replication to ensure precise confidence intervals for the observed error rates. Finally, it aggregates results, fits regression models to analyze sensitivity trends, and generates publication-ready visualizations.

## Prerequisites

- Python 3.11+
- A Unix-like environment (Linux/macOS) is recommended for file locking utilities used in the simulation engine.

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

The `main.py` script orchestrates the entire workflow: data generation, simulation, analysis, and visualization.

```bash
python code/main.py
```

This will:
1. Ensure output directories exist (`data/raw/`, `data/processed/`, `figures/`).
2. Generate synthetic datasets with known parameters.
3. Run adaptive Monte Carlo simulations for t-tests, ANOVA, and Chi-squared tests.
4. Aggregate results and compute 95% confidence intervals using bootstrap resampling.
5. Fit regression models to analyze the relationship between sample size and error rates.
6. Generate plots comparing observed vs. theoretical power and error rates.
7. Export final results to `data/processed/error_rates.csv` and `data/processed/regression_results.json`.

### Running Individual Components

You can also run specific stages of the pipeline independently.

**Data Generation:**
```bash
python code/run_data_gen.py
```
Generates a validation dataset to `data/raw/sample_validation.csv`.

**Simulation Execution:**
```bash
python code/run_optimized_simulation.py
```
Runs the full batch of Monte Carlo simulations with adaptive replication. Results are saved to `data/processed/raw_pvalues.csv` and intermediate checkpoints.

**Analysis & Visualization:**
```bash
python code/run_analyzer.py
```
Aggregates simulation results, computes confidence intervals, fits regression models, and generates plots.

**Benchmarking:**
```bash
python code/benchmark.py
```
Measures the execution time of the full simulation suite and logs results to `logs/benchmark.log`.

## Output Artifacts

After running the pipeline, you will find the following outputs:

- **`data/raw/sample_validation.csv`**: A small dataset used to validate the data generation logic against theoretical parameters.
- **`data/processed/raw_pvalues.csv`**: Raw p-values from every simulation replicate, stored with schema `sample_size`, `distribution_type`, `test_type`, `p_value`, `hypothesis_type`.
- **`data/processed/error_rates.csv`**: Aggregated error rates with 95% bootstrap confidence intervals for each (sample_size, distribution, test) configuration.
- **`data/processed/regression_results.json`**: Results of the log-p-value regression analysis, including coefficients and McFadden pseudo-R².
- **`data/processed/stability_trend.csv`**: Trend analysis results showing error rate stability across sample sizes.
- **`figures/`**: Directory containing publication-ready plots (PNG/SVG) visualizing error rates vs. sample size and power curves.

## Interpreting Results

### Sensitivity Analysis
The primary goal is to observe how the observed Type I error rate (under the null hypothesis) and statistical power (under the alternative) change as sample size increases.
- **Type I Error**: Should remain close to the nominal alpha level (0.05) across all sample sizes if the test is valid. Deviations indicate sensitivity issues.
- **Power**: Should increase as sample size increases, approaching 1.0 for the alternative hypothesis.

### Regression Analysis
The regression model (T027) predicts the magnitude of deviation from the nominal significance threshold (`|p - α|`) using log(sample size), distribution type, and test type.
- **McFadden R²**: A value > 0.1 (SC-005) indicates the model explains a significant portion of the variance in sensitivity.
- **Interaction Terms**: The model includes an interaction between sample size and distribution type (T037) to capture distribution-specific sensitivity patterns.

### Visualization
- **Error Rate vs. Sample Size**: Plots show the observed error rate with 95% confidence interval bands (T038). Wider bands at small sample sizes indicate higher uncertainty.
- **Power Curves**: Comparisons of observed power vs. theoretical power (for t-tests) help validate the simulation logic.

## Configuration

Simulation parameters (sample sizes, distributions, alpha levels, effect sizes) are defined in `code/config.py`.
- `MAX_REPLICATES`: Maximum number of Monte Carlo iterations per configuration (default: 10000).
- `LOG_EPSILON`: Small constant for numerical stability in log-transforms (default: 1e-15).

## Testing

Run the test suite to verify implementation correctness:
```bash
pytest tests/ -v
```

## License

This project is part of the llmXive automated science pipeline.