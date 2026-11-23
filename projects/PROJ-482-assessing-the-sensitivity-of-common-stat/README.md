# Assessing the Sensitivity of Common Statistical Tests to Dataset Size

This project implements a Monte Carlo simulation pipeline to evaluate how the sensitivity (Type I error rate and statistical power) of common statistical tests (t-test, ANOVA, Chi-squared) varies with dataset size, distribution type, and effect size.

## Project Overview

The pipeline generates synthetic datasets with known ground truth parameters, executes statistical tests under both null and alternative hypotheses, and aggregates results to analyze stability and power curves.

### Key Features
- **Controlled Data Generation**: Generates Normal, Uniform, and Log-Normal distributions with precise effect sizes.
- **Adaptive Monte Carlo Simulation**: Automatically adjusts replicate counts to ensure 95% Confidence Intervals are within a specified width (≤ 0.01).
- **Robust Statistical Testing**: Implements t-tests, ANOVA, Chi-squared, and Fisher's Exact (for small sample sizes).
- **Visualization**: Generates publication-ready plots of error rates vs. sample size.
- **Theoretical Validation**: Compares observed power curves against theoretical non-central distributions.

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

### Installation
1. Clone the repository.
2. Navigate to the project root directory.
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. (Optional) Verify the installation by running the validation script:
 ```bash
 python code/validate_quickstart.py
 ```

## Data Generation

The project uses a synthetic data generator (`code/data_generator.py`) to create datasets with known parameters. This ensures that the "ground truth" is available for validating Type I and Type II errors.

To generate a small validation dataset manually:
```bash
python code/run_data_gen.py
```
This will create `data/raw/sample_validation.csv` containing checksums and statistics for manual verification.

## Simulation Execution

The core simulation is orchestrated by `code/main.py`. It runs the full pipeline:
1. **Setup**: Ensures directory structure exists.
2. **Data Generation**: Creates synthetic datasets across sample sizes (n=10 to n=1000).
3. **Ground Truth Validation**: Verifies generated data matches theoretical parameters.
4. **Simulation**: Runs adaptive Monte Carlo replicates for t-tests, ANOVA, and Chi-squared tests.
5. **Analysis**: Aggregates results, computes bootstrap confidence intervals, and fits regression models.
6. **Export**: Saves results to CSV and generates plots.

### Running the Full Pipeline
```bash
python code/run_analyzer.py
```
Aggregates simulation results, computes confidence intervals, fits regression models, and generates plots.

### Running Specific Stages
- **Run Simulation Only**:
 ```bash
 python code/run_simulation.py
 ```
- **Run Stability Analysis**:
 ```bash
 python code/run_stability_analysis.py
 ```
- **Run Regression Analysis**:
 ```bash
 python code/run_regression_analysis.py
 ```

## Interpreting Results

After the pipeline completes, results are stored in `data/processed/`.

### Key Output Files
- `data/processed/raw_pvalues.csv`: Raw p-values from every replicate (used for bootstrap CI).
- `data/processed/error_rates.csv`: Aggregated error rates (Type I and Type II) by sample size, distribution, and test type.
- `data/processed/stability_trend.csv`: Results of the stability trend analysis (regression of error rate vs. sample size).
- `data/processed/regression_results.json`: Coefficients and McFadden R² from the logistic regression model.
- `data/processed/plots/`: Contains PNG files of error rate curves and power curve comparisons.

### Metrics
- **Type I Error Rate**: The proportion of times the test incorrectly rejects the null hypothesis when it is true. Ideally close to α (0.05).
- **Statistical Power**: The proportion of times the test correctly rejects the null hypothesis when the alternative is true.
- **Stability Metric**: A measure of how much the error rate fluctuates across sample sizes.
- **McFadden R²**: A goodness-of-fit measure for the regression model predicting deviation from the nominal significance level.

## Architecture

- `code/config.py`: Simulation parameters and configuration.
- `code/data_generator.py`: Functions to generate synthetic data.
- `code/simulation_engine.py`: Core logic for running tests and adaptive replication.
- `code/analyzer.py`: Aggregation, bootstrap CI calculation, and regression analysis.
- `code/visualizer.py`: Plot generation.
- `code/export_results.py`: Final data export.
- `code/main.py`: Pipeline orchestration.

## Testing

Unit and integration tests are located in the `tests/` directory.
Run tests using:
```bash
pytest tests/
```

## License

This project is part of the llmXive automated science pipeline.