# Quick Start Guide: Statistical Analysis of Publicly Available Election Poll Aggregates

This guide provides instructions to run the full pipeline on a CPU-only environment.
The pipeline ingests real election poll data from FiveThirtyEight, harmonizes it,
computes frequentist and Bayesian forecasts, and evaluates their predictive accuracy.

## Prerequisites

- **Python**: Version 3.9 or higher
- **OS**: Linux, macOS, or Windows (with WSL2 recommended)
- **Hardware**: CPU-only execution (no GPU required). Minimum 4GB RAM recommended.
- **Network**: Internet connection required to fetch data from FiveThirtyEight.

## 1. Setup Environment

Create a virtual environment and install dependencies:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Initialize Project Structure

Ensure the necessary directories exist:

```bash
python code/setup_state_dir.py
python code/setup_data_dirs.py
```

## 3. Run the Full Pipeline

Execute the main pipeline script. This will:
1. Download raw poll data from FiveThirtyEight.
2. Harmonize and clean the data.
3. Calculate historical weights.
4. Generate Frequentist (Simple & Weighted) forecasts.
5. Fit the Bayesian Random Walk model.
6. Compute evaluation metrics (RMSE, MAE, Coverage).
7. Run Diebold-Mariano tests for model comparison.
8. Generate the final report.

```bash
python code/src/main.py
```

### Expected Outputs

Upon successful completion, the following artifacts will be generated:

- **Data**:
 - `data/raw/`: Raw CSVs downloaded from FiveThirtyEight.
 - `data/processed/poll_data_cleaned.csv`: Harmonized poll data.
 - `data/processed/historical_weights.csv`: Pollster-specific weights.
 - `data/processed/frequentist_forecasts.csv`: Point forecasts.
 - `data/processed/bayesian_forecasts.csv`: Bayesian posterior summaries.
- **State**:
 - `state/projects/PROJ-206-*.yaml`: Checksums and metadata for all artifacts.
- **Reports**:
 - `research.md`: Mathematical formulations and architectural decisions.
 - `figures/`: Visualization of forecasts and convergence diagnostics.

## 4. Verification

To verify the pipeline ran successfully:

```bash
# Check that output files exist
ls -lh data/processed/

# Verify artifact integrity
python code/src/utils/state_manager.py verify
```

## Troubleshooting

### Data Access Errors
If the pipeline fails to download data:
- Ensure you have an active internet connection.
- Verify the FiveThirtyEight URL is accessible: `curl https://projects.fivethirtyeight.com/polls/`
- Check that `data/raw/` is writable.

### Convergence Issues (Bayesian Model)
If the Bayesian model reports `R-hat > 1.05`:
- This indicates the MCMC sampler did not converge.
- The pipeline will halt and report this error.
- Try increasing the number of tuning steps in `src/models/bayesian.py` (requires code modification).
- Ensure your CPU is not throttling; run in a stable environment.

### Memory Errors
If you encounter `MemoryError`:
- The dataset is processed in chunks, but large election cycles may require more RAM.
- Close other applications to free up memory.
- Ensure you are running in a 64-bit Python environment.

## Architecture Notes

- **RCP Exclusion**: Per the project's "Verified Accuracy" principle, RealClearPolitics data is excluded. The pipeline logs a warning for this exclusion.
- **CPU-Only**: All models, including PyMC NUTS sampling, are configured to run on CPU. No GPU acceleration is used.
- **Sanctioned Exceptions**: The Random Walk Bayesian model and Diebold-Mariano tests are implemented as per the Spec, overriding specific Plan decisions. These deviations are documented in `research.md`.

## Next Steps

- Review `research.md` for detailed mathematical formulations.
- Examine `data/processed/` files to inspect the data and forecasts.
- Run `python -m pytest tests/` to execute the full test suite.