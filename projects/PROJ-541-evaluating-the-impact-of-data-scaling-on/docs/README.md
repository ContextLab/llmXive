# llmXive: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

## Project Overview

This project investigates how different data scaling methods (Standardization, Min-Max, Robust) affect the robustness of statistical tests (t-test, ANOVA, Chi-squared) under various distributional conditions. The study utilizes both synthetic data with known ground truth and real-world datasets from UCI and OpenML repositories.

## Research Questions

1. How do scaling methods impact Type I error rates under the null hypothesis?
2. What is the effect of scaling on statistical power under alternative hypotheses?
3. How do distributional properties (skewness, heteroscedasticity) interact with scaling methods?
4. Are the findings from synthetic data consistent with real-world datasets?

## User Stories

- **US1 (Simulation Engine)**: Generate synthetic datasets with controlled distributional properties where ground truth is known.
- **US2 (Scaling & Testing)**: Apply scaling methods and run parametric tests to assess robustness.
- **US3 (Aggregation & Visualization)**: Aggregate results to calculate Type I error rates and Power, visualize against nominal alpha.
- **US4 (Real-World Validation)**: Validate simulation findings on public datasets (UCI/OpenML).

## Project Structure

```
code/
├── analysis/
│ ├── metrics.py # Aggregate metrics, mixed-effects models
│ └── tests.py # Statistical tests (t-test, ANOVA, Chi-squared)
├── preprocessing/
│ ├── ingestion.py # Real-world dataset loading and cleaning
│ └── scaling.py # Standardization, Min-Max, Robust scaling
├── simulation/
│ ├── config.py # Simulation configuration management
│ ├── generator.py # Synthetic data generation
│ ├── logger.py # Logging setup
│ └── persistence.py # Data persistence utilities
├── visualization/
│ └── plots.py # Error rate plots and comparisons
├── utils/
│ └── env.py # Environment configuration (CPU-only)
├── tests/
│ ├── unit/ # Unit tests for all modules
│ └── integration/ # Integration tests for pipelines
├── main.py # Pipeline orchestration
└── requirements.txt # Dependencies

data/
├── raw/ # Original real-world datasets
├── scaled/ # Scaled datasets (standardized, minmax, robust)
├── config/ # Dataset configuration (datasets.yaml)
├── synthetic/ # Generated synthetic datasets
└── metadata/ # Manifest of processed datasets

results/
├── figures/ # Generated plots
├── simulation_results.csv # Aggregated simulation results
└── mixed_effects_*.csv # Mixed-effects model outputs

logs/
└── simulation.log # Application logs
```

## Installation

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd llmXive
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify CPU-only configuration**
 ```bash
 python -c "from utils.env import verify_cpu_only; verify_cpu_only()"
 ```

## Quick Start

### 1. Run the Full Pipeline (Synthetic Data)

Execute the simulation and analysis pipeline:
```bash
python code/main.py --mode synthetic
```

This will:
- Generate synthetic datasets with various distributional properties.
- Apply scaling methods (Standardization, Min-Max, Robust).
- Run statistical tests (t-test, ANOVA, Chi-squared).
- Aggregate metrics (Type I error, Power).
- Fit mixed-effects models.
- Generate summary reports and plots.

### 2. Run on Real-World Data

Execute the pipeline on real-world datasets:
```bash
python code/main.py --mode real-world
```

This will:
- Download datasets listed in `data/config/datasets.yaml`.
- Clean and preprocess the data.
- Apply scaling and run tests.
- Generate comparison reports.

### 3. Run Unit Tests

```bash
pytest code/tests/unit/ -v
```

### 4. Run Integration Tests

```bash
pytest code/tests/integration/ -v
```

## Configuration

### Simulation Configuration

Modify `data/config/simulation.yaml` to adjust:
- Sample sizes
- Distribution types (normal, skewed, heteroscedastic)
- Effect sizes
- Number of iterations
- Scaling methods to test

### Dataset Configuration

Edit `data/config/datasets.yaml` to add or modify real-world datasets:
```yaml
- id: uciml/iris
 source: UCI
 expected_size: ~150 rows
- id: openml/d/2
 source: OpenML
 expected_size: ~1000 rows
```

## Key Modules

- **`simulation.generator`**: Generates synthetic data with controlled properties.
- **`preprocessing.scaling`**: Implements Standardization, Min-Max, and Robust scaling.
- **`analysis.tests`**: Runs t-tests, ANOVA, and Chi-squared tests.
- **`analysis.metrics`**: Calculates aggregate metrics and fits mixed-effects models.
- **`visualization.plots`**: Generates error rate plots.

## Output Artifacts

- **`results/simulation_results.csv`**: Per-iteration test results.
- **`results/mixed_effects_synthetic.csv`**: Mixed-effects model results for synthetic data.
- **`results/mixed_effects_summary.csv`**: Mixed-effects model results for real-world data.
- **`results/figures/error_rate_plot.png`**: Empirical error rate vs. nominal alpha.
- **`results/figures/comparison_report.pdf`**: Summary comparison of scaling methods.

## Contributing

1. Ensure all unit tests pass: `pytest code/tests/unit/`
2. Ensure integration tests pass: `pytest code/tests/integration/`
3. Follow the project's coding standards (black, ruff).
4. Update documentation for any new features.

## License

This project is part of the llmXive automated science pipeline. See LICENSE for details.
