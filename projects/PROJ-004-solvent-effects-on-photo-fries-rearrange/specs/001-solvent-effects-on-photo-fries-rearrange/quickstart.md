# Quickstart: Solvent Effects on Photo-Fries Rearrangement Kinetics

## Prerequisites

*   Python 3.11+
*   `pip` (Python package installer)
*   Git

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    cd projects/PROJ-004-solvent-effects-on-photo-fries-rearrange
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Generate/Simulate Data (Optional)
If `data/raw/` and `data/compute/` are empty, run the data generator:
```bash
python code/main.py --generate-data
```
*This creates synthetic kinetic traces and DFT solvation energies for multiple solvents with 3 replicates each. Note: The synthetic data is generated under a null hypothesis (no correlation) to validate the pipeline.*

### 2. Execute Analysis
Run the full analysis pipeline:
```bash
python code/main.py --run-analysis
```
*This performs:*
*   *Data loading and validation (including SC-010 lookup table check)*
*   *Global kinetic fitting (exponential decay)*
*   *Power analysis documentation (SC-007)*
*   *Statistical correlation (Linear Regression with bootstrapped CIs, VIF)*
*   *Sensitivity analysis (SC-008)*
*   *Output generation (CSV, JSON, Plots)*

### 3. View Results
Results are saved to `data/processed/`:
*   `kinetic_metrics.csv`: Fitted lifetimes and statistics.
*   `correlation_results.json`: Regression coefficients, bootstrapped CIs, VIF scores.
*   `power_analysis.md`: Documented power analysis for sample size.
*   `sensitivity_analysis.csv`: Error rates for different cutoffs.
*   `plots/`: Regression plots and residual analysis.

### 4. Run Tests
Verify the pipeline integrity:
```bash
pytest tests/
```

## Troubleshooting

*   **Memory Error**: The pipeline is designed for < 7 GB RAM. If you encounter OOM, reduce the number of simulated traces in `code/config.py`.
*   **Fit Failure**: If `scipy.optimize` fails to converge, check `data/raw/` for noisy data. The pipeline flags these as `status: failed_fit`.
*   **Environment Tolerance**: If temperature/humidity logs exceed tolerances, the run is flagged in `kinetic_metrics.csv` but continues.
*   **Lookup Mismatch**: If dielectric constants do not match the lookup table (SC-010), the run is flagged in `kinetic_metrics.csv`.

## Next Steps

*   Review `docs/deviation_analysis.md` for discrepancies between simulated and expected values.
*   Review `docs/power_analysis.md` for the documented power analysis.
*   Review `docs/sensitivity_report.md` for the sensitivity analysis results.
*   Extend the `solvents.yaml` in `data/chemicals/` to include more solvents.
*   Replace synthetic data with real instrument exports in `data/raw/` (format must match `contracts/dataset.schema.yaml`).