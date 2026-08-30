# Quickstart: Evaluating Calibration of Probabilistic Weather Forecasts

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local machine with sufficient RAM).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    cd projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/
    pip install -r requirements.txt
    ```

## Execution

Run the full pipeline:

```bash
cd projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/
python main.py
```

### Steps Performed
1.  **Download**: Fetches SubseasonalRodeo data. Checks for `probability_value`.
2.  **Align**: Joins forecasts and observations.
3.  **Baseline**: Computes Brier/CRPS for raw forecasts.
4.  **Isotonic**: Applies recalibration and sensitivity analysis.
5.  **Bayesian**: Runs MCMC (with a timeout fallback).
6.  **Compare**: Runs Diebold-Mariano/Wilcoxon tests.

## Output

Results are saved in `projects/PROJ-763-evaluating-calibration-of-probabilistic-/results/`:

- `results_baseline.csv`: Raw metrics.
- `results_isotonic.csv`: Isotonic metrics + sensitivity logs.
- `results_bayesian.csv`: Bayesian metrics + convergence status.
- `figures/`: Reliability diagrams and PIT histograms.

## Troubleshooting

- **Data Availability Gate Failed**: The dataset lacks `probability_value`. Check the download source.
- **Bayesian Timeout**: The model exceeded the time threshold. Results will fall back to Isotonic. Check logs for `convergence_status: Timeout`.
- **Convergence Failed**: R-hat > 1.05. Check `results_bayesian.csv` for `Unconverged` status.
