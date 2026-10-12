# Quickstart Guide

This guide provides the minimal steps required to run the full analysis pipeline for the **Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems** project.

## Prerequisites

- Python 3.11 or newer
- Internet connection (required for downloading the raw network datasets)
- All dependencies installed (see `requirements.txt`)

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline is orchestrated through a single command that invokes the `src.main` module:

```bash
python -m src.main --config config.yaml
```

- `--config config.yaml` points to the configuration file located at the project root.
- The command will automatically:
 1. Download the raw network files (if they are not already present) into `data/raw/`.
 2. Compute topological metrics for each network.
 3. Run the Kuramoto oscillator simulations to obtain the synchronization robustness threshold.
 4. Perform regression analysis (if enough data are available) and generate statistical summaries.
 5. Produce visualisations (heatmaps, bar charts, model comparison plots).
 6. Write a pipeline status report indicating success or timeout.

## Expected Output Files

After successful execution, the following files will be generated inside the `results/` directory (additional sub‑folders may be created for figures):

- `results/sim_results.json` – A JSON array containing one entry per processed network with the computed synchronization threshold and status.
- `results/regression_summary.json` – Summary of the linear/polynomial regression, including R², p‑values, coefficients, and a `significant` flag.
- `results/descriptive_stats.json` – Generated when fewer than 10 networks are available; contains mean, median, and standard deviation of the available metric(s) along with a warning message.
- `results/pipeline_status.json` – Indicates overall pipeline outcome (`SUCCESS` or `TIMEOUT`) and, in the case of a timeout, the network ID that caused the delay.
- `results/verification_report.json` – Manual verification package required by SC‑003 (contains a small subset of network IDs and their thresholds).
- `results/manual_verification_log.csv` – CSV log for human reviewers to confirm the thresholds listed in the verification report.
- `results/figures/heatmap_thresholds.png` – Heatmap visualising the synchronization threshold across two topological predictors.
- `results/figures/comparison_plot.png` – Bar chart of regression coefficients with error bars.
- `results/figures/model_comparison_plot.png` – Side‑by‑side comparison of primary and secondary model R² values.

## Verification

To confirm that the pipeline executed correctly:

1. Run the command shown above.
2. Verify that all files listed in the *Expected Output Files* section exist.
3. Optionally, run the test suite:

```bash
pytest -v
```

The test suite checks schema validation, metric computation, simulation correctness, and regression logic. [UNRESOLVED-CLAIM: c_ac55a0b9 — status=not_enough_info]

## Troubleshooting

- **Timeouts**: If the pipeline exceeds the allotted runtime, inspect `results/pipeline_status.json` for the offending network ID.
- **Insufficient Data**: When fewer than 10 raw networks are present, regression is skipped and `results/descriptive_stats.json` is produced instead.
- **Disconnected Graphs**: Networks that are not fully connected will be flagged in `sim_results.json` with `status: "disconnected"` and a `threshold` of `null`.

For further details, see the documentation files in the `docs/` directory.