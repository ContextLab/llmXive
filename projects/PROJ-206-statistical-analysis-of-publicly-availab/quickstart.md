# Quickstart Guide: Statistical Analysis of Publicly Available Election Poll Aggregates

This guide provides instructions to run the full pipeline on a CPU-only environment.
The pipeline ingests real poll data from FiveThirtyEight, harmonizes it, calculates
historical weights, and executes Frequentist and Bayesian forecasting models.

## Prerequisites

- **Operating System**: Linux, macOS, or Windows (with WSL2 recommended for Linux-like behavior)
- **Python**: Version 3.9 or higher
- **Hardware**: CPU only (No GPU required). The Bayesian model uses PyMC NUTS sampler optimized for CPU.
- **Disk Space**: ~500MB for dependencies and data artifacts.

## 1. Environment Setup

Create and activate a virtual environment, then install dependencies.

```bash
# Navigate to project root
cd /path/to/PROJ-206-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv

# Activate environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Directory Structure Initialization

Ensure the required data and state directories exist.

```bash
python code/setup_data_dirs.py
python code/setup_state_dir.py
```

*Expected Output*: Creation of `data/raw/`, `data/processed/`, `state/projects/`, etc.

## 3. Data Acquisition (User Story 1)

Download real poll data from FiveThirtyEight and election outcomes from MEDSL/FEC.
**Note**: RCP data is explicitly excluded per project design (see `research.md`).

```bash
python code/src/data/download.py
```

*Output*:
- `data/raw/fivethirtyeight_polls.csv` (raw download)
- `data/raw/election_outcomes.csv` (raw download)

## 4. Data Harmonization & Weight Calculation (User Story 1)

Parse dates, bin into weekly intervals, check data sufficiency, and calculate
pollster-specific historical RMSE weights.

```bash
python code/src/data/harmonize.py
python code/src/data/weights.py
```

*Output*:
- `data/processed/poll_data_cleaned.csv`
- `data/processed/historical_weights.csv`
- `state/projects/PROJ-206-*.yaml` (updated with file hashes)

*Validation*: The pipeline will halt with a warning if fewer than 5 polls exist
in the 30 days preceding an election or if the total poll count is < 500.

## 5. Frequentist Aggregation (User Story 2)

Compute point forecasts using Simple Unweighted Averaging and Accuracy-Weighted Averaging.

```bash
python code/src/models/frequentist.py
```

*Output*:
- `data/processed/frequentist_forecasts.csv` (contains `simple_avg_forecast` and `weighted_avg_forecast`)

## 6. Bayesian Hierarchical Modeling (User Story 3)

Fit the Random Walk hierarchical model using PyMC.
*Note*: This step may take 5-15 minutes depending on CPU speed and data volume.

```bash
python code/src/models/bayesian.py
```

*Output*:
- `data/processed/bayesian_forecasts.csv`
- `data/processed/bayesian_model_stats.json` (R-hat, ESS, convergence status)

## 7. Evaluation & Meta-Analysis

Calculate RMSE/MAE, verify credible interval coverage, and run Diebold-Mariano tests
with Westfall-Young correction.

```bash
python code/src/evaluation/metrics.py
python code/src/evaluation/meta_analysis.py
```

*Output*:
- `data/processed/evaluation_metrics.csv`
- `data/processed/dm_test_results.csv`

## 8. Reporting

Generate the final comparative report.

```bash
python code/src/evaluation/reporting.py
```

*Output*:
- `data/processed/final_report.md`

## 9. Full Pipeline Execution (Optional)

To run the entire pipeline sequentially from download to report:

```bash
bash scripts/run_full_pipeline.sh
```

*(If the script does not exist yet, run the individual steps 3-8 in order).*

## Troubleshooting

- **Convergence Warnings**: If the Bayesian model reports R-hat > 1.05, increase the `tune` steps in `src/models/bayesian.py` or reduce the `draws` count.
- **Data Sufficiency Errors**: If the pipeline halts due to insufficient data, ensure the download script completed successfully and that the selected election cycles have sufficient historical records.
- **Memory Errors**: If running out of RAM, reduce the number of MCMC draws in the Bayesian configuration.

## Verification

To verify the installation and data integrity:

```bash
python -m pytest tests/ -v
```

Ensure all unit tests pass and that `data/processed/` contains the expected CSV files.