# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Navigate to the project root.
2. Create a virtual environment and activate it:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Simulation
The main entry point is `code/main.py`. It orchestrates the full pipeline:
- Data generation (US1)
- Imputation and Estimation (US2)
- Metrics and Sensitivity Analysis (US3)

**Basic Run:**
```bash
python code/main.py --beta-sweep 0.0,0.2,0.5,0.8,1.0 --runs 200
```

**Parallel Execution (Optimized for T052):**
To ensure completion within the 4-hour window (SC-003), the script supports parallel execution across beta levels using `joblib`.
```bash
python code/main.py --beta-sweep 0.0,0.2,0.5,0.8,1.0 --runs 200 --parallel True --n-jobs 2
```

**Custom Output Directory:**
```bash
python code/main.py --output data/results_custom
```

## Generating Visualizations
Once the simulation is complete, generate plots using `code/visualization.py`:

```bash
# Bias vs Beta
python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png

# Coverage vs Beta
python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png

# Bias Distributions
python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png
```

## Validating Results
The pipeline automatically validates the schema of `simulation_summary.csv` and runs statistical tests.
To manually verify the schema:
```bash
python code/analysis/schema_validator.py --input data/results/simulation_summary.csv
```

## Output Artifacts
- `data/results/simulation_summary.csv`: Aggregated results for all runs.
- `data/results/statistical_test_results.json`: Results of ANOVA/Friedman/Bootstrap tests.
- `data/results/power_analysis.json`: Statistical power report.
- `data/results/oracle_benchmark.json`: Comparison against the oracle (complete data) benchmark.
- `data/results/bias_trend_verification.json`: Verification of monotonic bias trends.
- `docs/paper/figures/`: Generated plots.
