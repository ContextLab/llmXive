# Assessing the Sensitivity of Common Statistical Tests to Dataset Size

This project evaluates how the power and Type I/II error rates of common statistical tests (t-test, ANOVA, Chi-squared, Fisher's Exact) vary with dataset size and underlying data distribution.

## Project Structure

```
.
├── code/ # Source code for the simulation pipeline
│ ├── config.py # Simulation parameters and grid definitions
│ ├── data_generator.py # Synthetic data generation utilities
│ ├── simulation_engine.py # Core Monte Carlo simulation logic
│ ├── analyzer.py # Result aggregation and statistical analysis
│ ├── visualizer.py # Plot generation
│ ├── export_results.py # Final result export and plotting orchestration
│ ├── main.py # Main entry point for the full pipeline
│ ├── setup_directories.py # Directory initialization
│ └──...
├── data/
│ ├── raw/ # Raw generated datasets (e.g., sample_validation.csv)
│ └── processed/ # Aggregated results, plots, and intermediate files
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip

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

## Running the Simulation

The full pipeline can be executed via the `main.py` script located in the `code/` directory.

```bash
cd code
python main.py
```

This will:
1. Ensure necessary directories (`data/raw`, `data/processed`) exist.
2. Generate synthetic datasets across various sample sizes (10-1000) and distributions (Normal, Uniform, Log-Normal).
3. Run adaptive Monte Carlo simulations for t-tests, ANOVA, Chi-squared, and Fisher's Exact tests.
4. Aggregate results, compute confidence intervals, and fit regression models.
5. Generate publication-ready plots and export results to CSV.

### Output Files

- `data/raw/sample_validation.csv`: Small sample dataset for manual verification.
- `data/processed/raw_pvalues.csv`: Raw p-values from all simulation replicates.
- `data/processed/error_rates.csv`: Aggregated error rates with confidence intervals.
- `data/processed/plots/`: Directory containing generated PNG/SVG plots.

## Interpreting Results

### Error Rates
The primary output is the relationship between sample size (`n`) and the observed error rate (Type I or Type II).
- **Type I Error**: The rate at which the null hypothesis is rejected when it is true. Ideally, this should be close to the significance level (alpha = 0.05).
- **Type II Error**: The rate at which the null hypothesis is *not* rejected when the alternative is true. This measures the test's power (Power = 1 - Type II Error).

### Visualizations
- **Error Rate vs. Sample Size**: Plots showing how error rates converge as `n` increases.
- **Test Comparison**: Side-by-side comparisons of different statistical tests under identical conditions.

### Stability Analysis
The project calculates the variance of Type I error rates across sample sizes to verify stability (SC-002). A low variance indicates that the test maintains consistent error rates regardless of dataset size.

## Configuration

Simulation parameters (sample sizes, distributions, alpha levels, effect sizes) are defined in `code/config.py`. To modify the simulation grid, edit the `get_simulation_grid` and `get_test_grid` functions in that file.

## Testing

Run the test suite using pytest:

```bash
pytest tests/
```

## Dependencies

See `requirements.txt` for the full list of dependencies:
- numpy
- scipy
- pandas
- matplotlib
- seaborn
- scikit-learn
- pytest

## License

[Insert License Here]