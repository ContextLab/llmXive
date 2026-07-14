# Quickstart: Ambient Temperature Influence on Moral Decision Speed

## Prerequisites

* Python 3.11+
* `pip`
* Sufficient disk space for raw and processed data.
* Internet access (to download ERA5 and Moral Machine data)

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins versions for `pandas`, `numpy`, `statsmodels`, `xarray`, `h5netcdf`, `geopy`, `matplotlib`, `seaborn`, `pytest`, `cdsapi`.*

## Data Setup

The ingestion script will automatically download the required datasets to `data/raw/`.

1. **Run the ingestion script**:
 ```bash
 python code/ingestion.py
 ```
 * This script:
 * Downloads ERA hourly data for a five-year period via the Copernicus Climate Data Store API.
 * Downloads the Moral Machine dataset from the verified HuggingFace repository.
 * Performs spatial/temporal matching using a KD‑Tree with a defined distance cutoff.
 * Filters outliers (response time < 100 ms or > 10 000 ms; temperature < ‑30 °C or > 50 °C).
 * Generates `results/logs/exclusion_log.csv` (failed matches) **and** `results/logs/match_log.csv` (successful matches).
 * Saves the cleaned dataset to `data/processed/merged_dataset.parquet`.

2. **Verify Data**:
 * Check `results/logs/exclusion_log.csv` for exclusion reasons.
 * Check `results/logs/match_log.csv` for match quality.
 * Inspect `data/processed/merged_dataset.parquet` for expected columns.

## Running the Analysis

### Primary Scalable Model (recommended)

```bash
python code/modeling.py --mode scalable
```
* **What it does**:
 * Aggregates response times per participant (or samples up to 10 k participants).
 * Fits an OLS model with clustered robust SEs by cultural region.
 * Saves `results/models/model_summary.json`, diagnostic plots, and convergence info.

### Full Mixed‑Effects Model (optional, runs on sampled subset)

```bash
python code/modeling.py --mode full_lmm --sample-size large-scale
```
* Outputs: same artifacts as above, plus random‑effect variances.

### Robustness Checks

```bash
python code/robustness.py
```
* Generates:
 * Temperature metric comparison figures.
 * Distance‑threshold sensitivity tables.
 * Non‑linearity comparison JSON (`results/robustness/nonlinearity_comparison.json`).
 * Indoor/outdoor proxy analysis (or limitation report).

## Running Tests

```bash
pytest tests/ -v
```

## Expected Outputs

* `results/logs/exclusion_log.csv` – excluded records with reasons.
* `results/logs/match_log.csv` – successful match details (station ID, timestamp, distance).
* `results/models/model_summary.json` – coefficients, p‑values, LRT/Wald test results, convergence status.
* `results/figures/` – diagnostic plots, effect plots, robustness visualizations.
* `data/processed/merged_dataset.parquet` – cleaned dataset for further analysis.

## Troubleshooting

* **Memory Error** – If the full dataset exceeds memory, the script automatically samples a representative subset of rows (adjustable via `--sample-size`).
* **ERA5 Download Failed** – Ensure internet access; the script uses the official CDS API URL `.
* **Model Convergence Warning** – Check `results/logs/convergence_log.txt`. If convergence fails, the script will fall back to the GLMM with Gamma distribution.
