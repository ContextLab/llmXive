# Evaluating the Robustness of Common Statistical Tests to Non-Independence

## Project Overview

This project quantifies the inflation of Type I error rates and the reduction of statistical power in common statistical tests (t-test, ANOVA, Chi-squared) when the assumption of data independence is violated. Using a Monte Carlo simulation framework, we inject varying degrees of dependency (temporal, spatial, hierarchical) into real public datasets and synthetic data to measure the robustness of these tests.

## Key Findings & Methodology

The study employs two primary paradigms for null hypothesis construction:
1. **Generate-then-Inject**: Used for synthetic data. Data is generated under true independence ($r=0$), then dependency is injected to simulate violations.
2. **Inject-then-Permute**: Used for real public datasets. Dependency is injected into the raw data, and then target labels are permuted to break any existing signal, creating a valid null hypothesis on real-world feature structures.

Dependency strengths are swept across the discrete set $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$.

## Project Structure

```text
PROJ-483-evaluating-the-robustness-of-common-stat/
├── code/
│ ├── config.py # Configuration loading and validation
│ ├── data_loader.py # Fetches real datasets from verified UCI URLs
│ ├── dependency_injector.py # AR(1), Block Bootstrap, Spatial Kernel Smoothing
│ ├── metrics.py # Type I error, Power, Clopper-Pearson CI, Logistic Models
│ ├── simulation_runner.py # Monte Carlo loop, Null construction, Test execution
│ ├── visualizer.py # Plot generation for error rates and power
│ ├── main.py # Pipeline orchestration and aggregation
│ └──... (utility scripts)
├── data/
│ ├── raw/ # Downloaded datasets (CSV)
│ └── manifests/ # Dataset definitions, checksums, proxy reports
├── results/
│ ├── aggregated_unified.csv # Final simulation results
│ ├── type1_error_table.md # Human-readable Markdown table
│ └──... (logs, models, reports)
├── tests/ # Unit and integration tests
├── docs/ # This documentation
└── requirements.txt
```

## Prerequisites

- Python 3.11+
- System dependencies: `gcc`, `make` (for compiling some scipy/numpy extensions)

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

## Configuration

The pipeline is controlled by `code/config.yaml`. Key parameters include:
- `seed`: Random seed for reproducibility.
- `n_replications`: Number of Monte Carlo iterations (default: 10,000).
- `dependency_strengths`: List of $r$ values to test.
- `use_real_data`: Toggle between real public datasets and synthetic generation.
- `use_streaming`: Enable streaming for large datasets (if supported).

## Execution

### Full Pipeline

To run the complete sensitivity analysis sweep (Type I Error and Power):

```bash
python code/main.py
```

This script:
1. Loads configuration and dataset manifests.
2. Validates datasets (T035).
3. Generates spatial proxies if needed (T037, T041).
4. Runs the Monte Carlo simulation for all test types (t-test, ANOVA, Chi-squared) and dependency structures.
5. Aggregates results into `results/aggregated_unified.csv`.
6. Generates the Type I Error table (`results/type1_error_table.md`).
7. Trains logistic regression models (`results/logistic_models.pkl`).
8. Generates visualizations.

### Specific Tasks

- **Data Loading**: `python code/run_data_loader.py`
- **AR(1) Validation**: `python code/validate_ar1.py`
- **Block Bootstrap Validation**: `python code/validate_block_bootstrap.py`
- **Spatial Proxy Validation**: `python code/validate_spatial_proxy.py`
- **Quickstart Validation**: `python code/validate_quickstart.py`

## Output Artifacts

- `results/aggregated_unified.csv`: The primary data artifact containing error rates, power, and confidence intervals.
- `results/type1_error_table.md`: A formatted Markdown table summarizing Type I error inflation.
- `results/power_analysis.csv`: Summary of power reduction under dependency.
- `results/logistic_models.pkl`: Trained models predicting error rates based on dependency strength.
- `figures/`: Generated plots (error rate curves, power comparisons).

## Data Sources

This project uses **verified real-world datasets** from the UCI Machine Learning Repository:
- **Wine**: Continuous variables (ANOVA/t-test).
- **Car Evaluation**: Categorical variables (Chi-squared).
- **Zoo**: Categorical variables (Chi-squared).

Datasets are fetched directly from canonical URLs defined in `data/manifests/datasets.yaml`. No synthetic data is used as input; synthetic generation is strictly controlled via the "Generate-then-Inject" paradigm in `simulation_runner.py`.

## Performance Targets

The pipeline is optimized to complete 10,000 replications within **6 hours** on a standard 2-core, 7GB RAM runner. Vectorized NumPy operations and efficient aggregation strategies are employed to meet this target.

## Contributing

When adding new features:
1. Ensure all new dependencies are added to `requirements.txt`.
2. Update `code/config.yaml` schema if new parameters are introduced.
3. Write unit tests in `tests/unit/` and integration tests in `tests/integration/`.
4. Verify that the pipeline fails loudly if real data fetches fail (do not fallback to synthetic).

## License

[Insert License Here]
