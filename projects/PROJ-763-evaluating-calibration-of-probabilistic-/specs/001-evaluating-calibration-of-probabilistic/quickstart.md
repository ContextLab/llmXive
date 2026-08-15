# Quickstart: Evaluating Calibration of Probabilistic Weather Forecasts

## Prerequisites
- Python 3.11 or higher.
- `pip` package manager.
- Access to the SubseasonalRodeo dataset (or a verified fallback).
- (Optional) Kaggle account for GPU offload if CPU sampling fails.

## Installation
1. Clone the repository and navigate to the project directory.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
1. Edit `code/config.py` to set the dataset URL if the default is incorrect.
2. Set the random seed for reproducibility (default: 42).

## Running the Pipeline
Execute the main pipeline script:
```bash
python code/main.py
```
This will:
1. Download and verify the dataset (halts if unavailable).
2. Align forecasts and observations.
3. Compute baseline metrics and generate `reliability_diagram_raw.png`.
4. Fit isotonic and Bayesian models (ADVI first, then MCMC if needed).
5. Compare results and generate diagrams.
6. Output results to the `results` directory.

## Output Artifacts
- `results_baseline.csv`: Baseline Brier scores and CRPS.
- `results_isotonic.csv`: Isotonic recalibration results.
- `results_bayesian.csv`: Bayesian recalibration results.
- `reliability_diagram_raw.png`: Baseline reliability diagram.
- `reliability_diagram_isotonic.png`: Isotonic reliability diagram.
- `reliability_diagram_bayesian.png`: Bayesian reliability diagram.
- `pit_histogram_raw.png`: Raw forecast PIT histogram.
- `pit_histogram_bayesian.png`: Bayesian forecast PIT histogram.
- `pit_histogram.png`: Aggregated PIT histogram.
- `results_decomposition.csv`: Brier score decomposition (Reliability, Resolution, Uncertainty).
- `power_analysis_report.json`: Power analysis results.

## Troubleshooting
- **Dataset Download Failed**: Check the URL in `config.py` or verify network connectivity. If the dataset is unverified, the pipeline halts.
- **MCMC Convergence Failed**: Check `results_bayesian.csv` for "Unconverged" status. The pipeline will fall back to isotonic results.
- **Out of Memory**: Reduce the dataset size or use the Kaggle GPU escape hatch.
- **Underpowered Results**: Check `power_analysis_report.json` for "Underpowered" flag.