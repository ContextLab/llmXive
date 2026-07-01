# Quickstart: Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository** (if not already done).
2. **Navigate to the feature directory**:
   ```bash
   cd projects/PROJ-182-evaluating-the-impact-of-different-missi
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### 1. Configure Parameters
Edit `code/config/simulation.yaml` and `code/config/missingness.yaml` to set:
- Sample size (`n_samples`).
- True effect (`true_effect`).
- Missingness rates (`missing_rates`).
- Seeds.

### 2. Run the Full Pipeline
Execute the main script to run the Monte-Carlo simulation:
```bash
python code/main.py --config code/config/simulation.yaml --missing code/config/missingness.yaml
```
*Note: This will take several hours on a standard CPU. For testing, use `--replications 10`.*

### 3. View Results
- **Metrics**: `results/metrics.csv` contains Bias, RMSE, and Coverage.
- **Visualizations**: `results/heatmaps/` contains generated plots.
- **Logs**: `logs/simulation.log` contains convergence warnings and errors.

## Testing

Run unit tests to verify data generation and missingness logic:
```bash
pytest code/tests/unit/ -v
```

Run integration tests to verify the full pipeline on a small scale:
```bash
pytest code/tests/integration/ -v --replications 5
```

## Troubleshooting

- **Convergence Errors**: If the Heckman model fails to converge, check `logs/simulation.log` for `error_code: CONVERGENCE_FAIL`. The system will record NaN and continue.
- **Runtime Exceeded**: If the job exceeds 6 hours on CI, reduce `n_samples` or `replications` in the config.
- **Missing Dependencies**: Ensure `statsmodels` and `scikit-learn` are installed; they are required for the estimators.
