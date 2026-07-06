# Quickstart: Quantifying Uncertainty in Small Sample Regression Models

## Prerequisites

*   Python 3.11+
*   `pip` or `poetry`
*   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-034-quantifying-uncertainty-in-small-sample-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Simulation

### 1. Generate Synthetic Data
Run the simulation engine with default settings ($N=30$, $\rho=0.85$, 100 replications):
```bash
python code/main.py --simulate --n-samples 30 --target-correlation 0.85 --replications 100
```

### 2. Run the Analysis Pipeline
Execute the full pipeline (OLS, Bootstrap BCa, Bayesian) on the generated data:
```bash
python code/main.py --analyze --replications 100
```

### 3. Real-World Validation
Run the validation on the UCI Concrete dataset (subsampled to $N=40$):
```bash
python code/main.py --validate --dataset concrete --n-samples 40
```

## Generating Reports

To generate the calibration plots and coverage summary:
```bash
python code/main.py --report --output data/results/report.pdf
```

## Verification

To verify the simulation engine:
```bash
pytest tests/unit/test_simulation.py
```

To verify the full pipeline:
```bash
pytest tests/integration/test_pipeline.py
```

## Troubleshooting

*   **Bayesian convergence issues**: If R-hat > 1.05, check `logs/bayesian.log` for divergent transitions. Consider reducing $N$ or adjusting priors.
*   **Runtime too long**: Reduce `--replications` or `--bootstrap-samples` (default: a standard resampling quantity).
*   **Memory error**: Ensure $N < 50$ and reduce `--n-predictors`.
*   **Collinearity filtering**: If too many datasets are discarded due to low realized VIF, the target correlation may be too low for the sample size; increase target $\rho$.