# Quickstart: Ambient Temperature Influence on Moral Decision Speed

## Prerequisites

- Python 3.11+
- Access to the Moral Machine dataset (local CSV or verified URL).
- Access to the NOAA dataset (via HuggingFace or local Parquet).
- 7 GB RAM, 2 CPU cores.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-743-ambient-temperature-influence-on-moral-d
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Setup

1. **Download Moral Machine Data**:
 - If not available via verified URL, place `MoralMachineData.csv` in `data/raw/`.
 - *Note*: The pipeline expects this file. If missing, run `python code/ingestion.py --generate-synthetic` to create a test dataset.

2. **Download NOAA Data**:
 - The script will attempt to fetch from `.
 - Alternatively, place `NOAA_buoy_2023.parquet` in `data/raw/`.

## Running the Pipeline

1. **Ingest and Merge**:
 ```bash
 python code/ingestion.py
 ```
 - Output: `data/processed/merged_dataset.parquet`, `results/logs/data_quality_log.json`.

2. **Fit Models**:
 ```bash
 python code/modeling.py
 ```
 - Output: `results/figures/diagnostics.png`, `results/logs/model_summary.json`.

3. **Run Robustness Checks**:
 ```bash
 python code/robustness.py
 ```
 - Output: `results/figures/sensitivity_plots.png`, `results/logs/robustness_summary.json`.

4. **Generate Final Report**:
 ```bash
 python code/main.py
 ```
 - Output: All figures and summary statistics in `results/`.

## Verification

- Check `results/logs/data_quality_log.json` for exclusion reasons.
- Verify `results/figures/diagnostics.png` shows normal residuals (QQ-plot).
- Confirm `results/logs/model_summary.json` contains a p-value for `temperature_celsius`.

## Troubleshooting

- **Memory Error**: Reduce the sample size in `code/config.py` (`SAMPLE_FRACTION = 0.05`).
- **Convergence Warning**: Check `results/logs/model_summary.json` for optimizer warnings. Try simplifying random effects.
- **Missing Data**: Ensure `MoralMachineData.csv` has `latitude`, `longitude`, and `timestamp` columns.
