# PROJ-483: Evaluating the Robustness of Common Statistical Tests to Non-Independence

## Overview

This project quantifies the inflation of Type I error rates and the reduction of statistical power in common parametric tests (t-test, ANOVA, Chi-squared) when the assumption of independence is violated. We simulate various dependency structures (AR(1), Block Bootstrap, Spatial) across public datasets to measure how robust these tests are to non-independence.

## Project Structure

```text
PROJ-483-evaluating-the-robustness-of-common-stat/
├── code/
│ ├── config.py # Configuration loading and validation
│ ├── data_loader.py # Real data fetching and validation
│ ├── dependency_injector.py # AR(1), Block, and Spatial dependency injection
│ ├── metrics.py # Error rate, power, and CI calculations
│ ├── simulation_runner.py # Monte Carlo simulation engine
│ ├── visualizer.py # Plot generation (error curves, power loss)
│ ├── main.py # Pipeline orchestration
│ └──... (other execution scripts)
├── data/
│ ├── manifests/ # Dataset definitions and proxy reports
│ ├── raw/ # Downloaded CSVs
│ └──...
├── results/
│ ├── aggregated_unified.csv # Final simulation results
│ ├── type1_error_table.md # Human-readable error rate table
│ ├── power_analysis.csv # Power reduction metrics
│ └──... (logs, reports, models)
├── docs/
│ ├── README.md # This file
│ └── binning_strategy.md # Chi-squared binning methodology
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└──...
```

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`:
 - `numpy`, `scipy`, `pandas`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `scikit-learn`, `requests`

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Data Sources

Ensure real datasets are accessible. The pipeline will fail loudly if verified URLs in `data/manifests/datasets.yaml` are unreachable.

```bash
python code/run_data_loader.py
```

### 3. Run the Full Simulation

Execute the sensitivity analysis sweep (Type I Error) and Power Analysis.

```bash
python code/main.py
```

This will:
- Load configurations from `code/config.yaml`
- Fetch/validate real datasets
- Run 10,000 replications per configuration
- Aggregate results into `results/aggregated_unified.csv`
- Generate visualizations and reports

### 4. Validate Results

Run the validation script to ensure all expected artifacts were generated and data integrity is maintained.

```bash
python code/validate_quickstart.py
```

## Configuration

Edit `code/config.yaml` to adjust:
- `seed`: Random seed for reproducibility
- `n_replications`: Number of Monte Carlo iterations (default: 10,000)
- `dependency_strengths`: Set of $r$ values to test (default: `[0.0, 0.1, 0.2, 0.3, 0.5]`)
- `use_real_data`: Toggle between real dataset permutation and synthetic generation
- `use_streaming`: Enable streaming for large datasets (if applicable)

## Methodology

### Null Hypothesis Construction
- **Synthetic Data**: Generate independent data, then inject dependency (Generate-then-Inject).
- **Real Data**: Inject dependency, then permute labels to break true effects (Inject-then-Permute).

### Dependency Injection
- **AR(1)**: Temporal autocorrelation with tunable strength $r$.
- **Block Bootstrap**: Hierarchical dependency via block resampling.
- **Spatial Kernel**: Spatial dependency using feature-space clustering proxies (validated by silhouette score > 0.25).

### Metrics
- **Type I Error Rate**: Proportion of rejections under true null.
- **Power**: Proportion of rejections under true effect ($\delta=1.0\sigma$).
- **Confidence Intervals**: Clopper-Pearson 95% CI for error rates.

## Output Artifacts

- `results/aggregated_unified.csv`: Master results file.
- `results/type1_error_table.md`: Formatted Markdown table of error rates.
- `results/power_analysis.csv`: Power reduction metrics.
- `results/logistic_models.pkl`: Trained models predicting error rates.
- `figures/`: Generated plots (error curves, power loss).

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Key tests:
- `tests/unit/test_dependency_injector.py`: Verify injection accuracy.
- `tests/unit/test_simulation_runner.py`: Verify null hypothesis validity.
- `tests/integration/test_cross_test_comparison.py`: Multi-test pipeline integration.

## Performance Targets

- **10,000 replications** must complete in **< 6 hours** on a 2-core, 7GB RAM runner.
- Memory footprint for largest dataset estimated pre-flight; skipped if > 6GB.

## License

MIT License.
