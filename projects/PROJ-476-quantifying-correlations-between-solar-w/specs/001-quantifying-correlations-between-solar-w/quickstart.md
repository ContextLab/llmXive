# Quickstart: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites

*   Python 3.11+
*   `pip` (package manager)
*   Internet access (to fetch data from CDAWeb/NOAA)

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-476-quantifying-correlations-between-solar-w
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `matplotlib`, `seaborn`.*

## Running the Pipeline

### 1. Data Acquisition & Synchronization

Run the main script to fetch and sync data for the default period (1998–2020).
```bash
python code/main.py --fetch --sync --start 1998-01-01 --end 2020-12-31
```
*   **Output**: `data/processed/synced.csv`
*   **Logs**: Check `logs/sync.log` for interpolation warnings.

### 2. Correlation Analysis

Run the analysis on the synced data.
```bash
python code/main.py --analyze --period train
```
*   **Output**: `results/correlations.csv`
*   **Method**: Pearson/Spearman with Bonferroni correction and $N_{eff}$ adjustment.

### 3. Validation & Visualization

Run validation on the held-out period (2018–2020) and generate plots.
```bash
python code/main.py --validate --period test --plots
```
*   **Output**:
    *   `results/validation_report.md`
    *   `figures/ts_overlay.png`
    *   `figures/heatmap.png`

## Verifying Results

1.  **Check the report**: Open `results/validation_report.md` to see if any pair exceeded $|r| > 0.5$ with corrected significance.
2.  **Inspect the heatmap**: Ensure the `figures/heatmap.png` shows the lagged correlations clearly.
3.  **Reproducibility**: Run the pipeline again. Results should be identical (due to fixed random seeds and deterministic data fetch).

## Troubleshooting

*   **Missing Data**: If the pipeline aborts with "Missing variable: helium_abundance", check the ACE data source for gaps > 6 hours.
*   **Network Error**: If data fetch fails, ensure your firewall allows access to `cdaweb.gsfc.nasa.gov` and `www.swpc.noaa.gov`.
*   **Memory Error**: The pipeline is designed for < 7 GB RAM. If you encounter memory issues, ensure no other heavy processes are running.
