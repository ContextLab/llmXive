# Quickstart: Exploring the Impact of Data Imputation Methods on Causal Inference

## Prerequisites

- Python 3.11+
- Git
- 4GB+ free disk space (for intermediate data)
- 7GB+ RAM (recommended for full simulation)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-047-exploring-the-impact-of-data-imputation-
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins all versions to ensure reproducibility (Constitution Principle I).*

## Running the Simulation

### 1. Run Unit Tests (Sanity Check)
Verify the synthetic generator and estimators work before the full run.
```bash
pytest tests/unit/ -v
```

### 2. Run the Full Simulation
Execute the main orchestration script. This will:
- Generate synthetic datasets.
- Apply multiple imputation methods.
- Estimate ATEs using IPW and PSM.
- Perform statistical tests and sensitivity analysis.
- Save results to `data/results/`.

```bash
python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0
```
*Expected Runtime: < 4 hours on GitHub Actions free tier.*

### 3. Validate Schema
Before generating figures, validate that `simulation_summary.csv` contains all required columns:
```bash
python code/analysis.py --validate-schema --input data/results/simulation_summary.csv
```

### 4. Generate Figures
Once `simulation_summary.csv` is validated, create the paper figures.
```bash
python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png
python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png
python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png
```

### 5. Verify Results
Check that the sensitivity analysis confirms monotonicity and coverage drop.
```bash
python code/analysis.py --verify-sensitivity --input data/results/sensitivity_analysis.json
```

## Troubleshooting

- **Convergence Errors**: If MICE fails to converge, the system logs the run as "failed" and excludes it from the bias average (as per Edge Case handling).
- **Memory Errors**: If RAM usage exceeds 7GB, reduce `--runs` or `--n-samples` in `run_simulation.py`.
- **Statistical Test Warnings**: If Shapiro-Wilk fails due to small sample size, the system defaults to Friedman test.
- **Schema Validation Failure**: If `simulation_summary.csv` is missing required columns, the schema validation task (T028.5) will fail and block figure generation. Ensure all imputation and estimation tasks complete successfully.
