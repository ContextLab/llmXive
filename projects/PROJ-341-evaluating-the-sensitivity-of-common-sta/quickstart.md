# Quickstart Guide: Evaluating the Sensitivity of Common Statistical Tests

This guide provides instructions to run the full simulation pipeline, generate visualizations, and produce the final validation report.

## Prerequisites

- Python 3.8+
- pip
- Access to the internet (to download real datasets from UCI via `ucimlrepo`)

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Full Pipeline

The pipeline consists of three main phases: Simulation, Analysis/Visualization, and Validation.

### Step 1: Run the Core Simulation (User Story 1)

This step generates synthetic data and calculates empirical Type I and Type II error rates across various sample sizes and effect sizes.

```bash
python code/main.py
```

**Outputs:**
- `data/simulation/p_values_raw.csv`: Raw p-values from all simulation iterations.
- `data/simulation/error_rates_summary.csv`: Aggregated error rates per condition.

### Step 2: Generate Thresholds and Visualizations (User Story 2)

This step analyzes the simulation results to identify reliability thresholds and generates comparative plots.

```bash
# Calculate thresholds
python code/analysis/threshold_finder.py

# Generate plots
python code/visualization/plotter.py
```

**Outputs:**
- `data/simulation/thresholds.json`: Identified sample size thresholds.
- `data/visualization/*.png`: Line plots with 95% CI bands and comparative divergence plots.

### Step 3: Validate Against Real-World Datasets (User Story 3)

This step downloads real-world small-sample datasets (Breast Cancer, Wine, Adult), runs statistical tests, and compares results against the simulation predictions.

```bash
python code/analysis/validator.py
```

**Outputs:**
- `data/raw/`: Downloaded datasets (Wisconsin Diagnostic, Wine, Adult).
- `data/simulation/real_data_pvalues.csv`: Observed p-values from real data.
- `data/simulation/real_data_power.json`: Bootstrapped power estimates.
- `data/simulation/validation_metrics.json`: KS statistics and validation metrics.

### Step 4: Generate the Final Validation Report

This step compiles all metrics, thresholds, and validation results into a comprehensive markdown report.

```bash
python code/analysis/report_generator.py
```

**Output:**
- `data/reports/validation_report.md`: The final validation report stating whether the simulation held true or if deviations were observed.

## Sensitivity Analysis (Optional)

To perform sensitivity analysis across different alpha thresholds:

```bash
python code/analysis/alpha_sensitivity.py
```

**Output:**
- `data/simulation/alpha_sensitivity_results.json`: Results showing critical sample size shifts across alpha levels.

## Running Tests

Ensure all unit and integration tests pass before deploying:

```bash
pytest tests/ -v
```

## Troubleshooting

- **Dataset Download Failures**: Ensure you have an active internet connection. The `ucimlrepo` package is required to fetch UCI datasets.
- **Memory Errors**: The simulation is optimized for <7GB RAM usage. If errors occur, try reducing the number of iterations or sample sizes in `code/main.py`.
- **Missing Output Files**: Verify that previous steps completed successfully. The pipeline is sequential; Step 2 requires output from Step 1, and Step 4 requires output from Step 3.