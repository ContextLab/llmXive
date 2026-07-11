# Quickstart: Exploring the Impact of Data Imputation Methods on Causal Inference

## Prerequisites

- Python 3.11+
- pip
- git

## Installation

1.  **Clone and Navigate**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-047-exploring-the-impact-of-data-imputation-/code
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs CPU-only compatible versions of `scikit-learn`, `statsmodels`, `linearmodels`, etc.*

## Running the Simulation

### 1. Generate Synthetic Data (Single Run)
To verify ground truth generation and alpha tuning:
```bash
python simulate.py --seed 42 --beta 0.5 --n 1000
```
*Output*: `data/raw/synth_{run_id}.csv` and `data/results/ground_truth_42.json`.

### 2. Run Full Simulation
Execute the full study (multiple runs, 5 beta values, parallelized):
```bash
python main.py
```
*Output*: `data/results/simulation_summary.csv`, `data/results/trend_verification.json`, `data/results/coverage_slope_verification.json`, and `data/results/plots/`.

### 3. Statistical Analysis & Plots
If you have run the simulation and want to regenerate plots or re-run statistical tests:
```bash
python analyze.py --input data/results/simulation_summary.csv
python visualize.py --input data/results/simulation_summary.csv
```

### 4. Run Tests
Verify reproducibility and logic:
```bash
pytest tests/ -v
```

## Expected Outputs

- **`data/results/simulation_summary.csv`**: The single source of truth for all bias, RMSE, and coverage metrics.
- **`data/results/trend_verification.json`**: Verification of the monotonic bias trend (Spearman rho).
- **`data/results/coverage_slope_verification.json`**: Verification of the negative slope in coverage vs. beta.
- **`data/results/plots/bias_vs_beta.png`**: Bias trends across MNAR strength.
- **`data/results/plots/coverage_vs_beta.png`**: Confidence interval coverage trends.
- **`data/results/plots/bias_distributions.png`**: Distribution of bias per method.

## Troubleshooting

- **Memory Error**: Ensure `sample_size` in `main.py` is not increased beyond 1000. The default is optimized for a moderate memory footprint.
- **Convergence Failure (MICE)**: The script automatically flags runs where MICE fails to converge. These are excluded from the final bias average but recorded in `data/results/failed_runs.json`.
- **Statistical Test Failure**: The LMM is robust to non-normality. If convergence fails, the script falls back to a non-parametric permutation test.
