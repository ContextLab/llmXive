# Quickstart: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## Prerequisites

- Python 3.11+
- Internet access (to download SNAP/Network Repository datasets)
- The project dependencies installed (see `requirements.txt`)

## Running the Pipeline

The entire workflow can be started with a single command:

```bash
python -m src.main --config config.yaml
```

This command will:

1. Load the configuration from `config.yaml`.
2. Download the required network datasets (if not already present).
3. Compute topological metrics for each network.
4. Run the Kuramoto synchronization simulations.
5. Perform regression analysis linking topology to synchronization robustness.
6. Generate visualisations and summary reports.

### Expected Output Files

After successful execution, the following files will be created (all under the project root):

- `results/sim_results.json` – JSON array containing the synchronization threshold for each processed network.
- `results/regression_summary.json` – Summary of the linear/polynomial regression analysis (R², coefficients, p‑values, etc.).
- `results/pipeline_status.json` – Execution status (`SUCCESS` or `TIMEOUT`) with timing information.
- `results/figures/heatmap_thresholds.png` – Heatmap visualising the relationship between topological predictors and thresholds.
- `results/figures/comparison_plot.png` – Bar chart of regression coefficients with confidence intervals.
- `results/figures/model_comparison_plot.png` – Side‑by‑side plot of R² values for primary and secondary models.

## Verification

```bash
# Run the full pipeline
python -m src.main --config config.yaml

# Run the test suite to ensure the command works
pytest -v tests/test_quickstart.py
```

The test suite checks that the command executes without errors and that the expected
result files are created (or, in the early development stage, that the script exits
cleanly). Once the later phases of the project are complete, the presence and
validity of the output files will be verified as part of the overall pipeline
verification.