# PROJ-483: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

## Overview
This project implements a Monte Carlo simulation pipeline to quantify the robustness of common statistical tests (t-test, ANOVA, Chi-squared) to violations of the independence assumption. It investigates how various dependency structures (AR(1), Block Bootstrap, Spatial Kernel Smoothing) inflate Type I error rates and reduce statistical power.

## Key Features
- **Generate-then-Inject Paradigm**: Ensures a true null hypothesis by generating independent data and then injecting specific dependency structures.
- **Multiple Dependency Models**: Supports temporal (AR(1)), hierarchical (Block Bootstrap), and spatial (Kernel Smoothing with feature-space clustering proxy) dependencies.
- **Comprehensive Metrics**: Calculates Type I error rates, statistical power, and Clopper-Pearson confidence intervals.
- **Real Data Integration**: Fetches and validates datasets from verified public sources (UCI, OpenML).
- **Visualization**: Generates comparative plots for error rates and power across different tests and dependency strengths.

## Project Structure
```
PROJ-483-evaluating-the-robustness-of-common-stat/
├── code/
│ ├── config.py # Configuration loading and validation
│ ├── config.yaml # Simulation parameters (seeds, strengths, etc.)
│ ├── data_loader.py # Data fetching, validation, and checksumming
│ ├── dependency_injector.py # AR(1), Block Bootstrap, Spatial smoothing logic
│ ├── exceptions.py # Custom exceptions (CriticalValidationError, etc.)
│ ├── main.py # Orchestration and sensitivity analysis sweep
│ ├── metrics.py # Error rate, power, CI, and logistic regression logic
│ ├── simulation_runner.py # Monte Carlo loop (Generate-then-Inject)
│ ├── visualizer.py # Plot generation functions
│ └──... (utility scripts)
├── data/
│ ├── manifests/ # Dataset URLs, checksums, proxy reports
│ └── raw/ # Fetched raw CSV datasets
├── results/
│ ├── simulation_raw.csv # Individual replication p-values
│ ├── aggregated.csv # Aggregated error rates and power metrics
│ ├── logistic_models.pkl # Trained logistic regression models
│ ├── edge_case_report.json # Logs of edge case handling
│ └──...
├── tests/
│ ├── unit/ # Unit tests for core logic
│ └── integration/ # Integration tests for pipelines
├── docs/ # Documentation (this file, design docs)
└── requirements.txt # Python dependencies
```

## Prerequisites
- Python 3.10+
- `pip`
- System dependencies for building scientific packages (e.g., `gcc`, `gfortran` on Linux/macOS)

## Installation
1. Clone the repository and navigate to the project directory.
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
Edit `code/config.yaml` to set simulation parameters:
- `random_seed`: Seed for reproducibility.
- `dependency_strengths`: List of correlation strengths ($r$) to sweep.
- `replications`: Number of Monte Carlo replications per configuration.
- `alpha`: Nominal significance level (default 0.05).
- `datasets`: Reference to `data/manifests/datasets.yaml`.

## Usage

### 1. Data Preparation
Fetch and validate datasets:
```bash
python code/run_data_loader.py
```
This populates `data/raw/` and generates `data/manifests/checksums.json`.

### 2. Run Simulation
Execute the main sensitivity analysis:
```bash
python code/main.py
```
This runs the Monte Carlo loop for t-tests, ANOVA, and Chi-squared tests across dependency structures, saving results to `results/`.

### 3. Analyze Results
The `results/aggregated.csv` file contains Type I error rates, power, and confidence intervals.
Logistic regression models relating error rates to dependency strength are saved in `results/logistic_models.pkl`.

### 4. Visualization
Use the `visualizer.py` module to generate plots. Example usage in a script:
```python
from visualizer import plot_error_rate_curve
import pandas as pd

df = pd.read_csv("results/aggregated.csv")
plot_error_rate_curve(df, "t-test", "ar1")
```

## Testing
Run the test suite:
```bash
pytest tests/
```
- **Unit Tests**: Validate individual components (dependency injection, metrics calculation).
- **Integration Tests**: Verify end-to-end pipeline behavior and output schemas.

## Design Principles
- **Scientific Validity**: The "Generate-then-Inject" method ensures a controlled null hypothesis.
- **Reproducibility**: All random seeds are pinned in `config.yaml` and logged.
- **Data Integrity**: Only real, verified public datasets are used; no synthetic input data.
- **Modularity**: Core logic (metrics, injection) is separated from execution (simulation runner).

## Contributing
1. Create a feature branch.
2. Implement changes following the existing code structure.
3. Ensure all tests pass (`pytest`).
4. Submit a pull request.

## License
[Insert License Here]
