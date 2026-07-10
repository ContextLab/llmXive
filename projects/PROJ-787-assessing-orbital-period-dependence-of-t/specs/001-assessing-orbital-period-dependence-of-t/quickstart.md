# Quickstart: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Prerequisites

-   Python 3.11+
-   `git`
-   Internet access (to fetch Kepler data from MAST)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-787-assessing-orbital-period-dependence-of-t
    ```

2.  **Create a virtual environment**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Verify environment**:
    ```bash
    python -c "import pandas, sklearn, scipy; print('All dependencies loaded successfully.')"
    ```

## Running the Pipeline

The pipeline is executed via the main entry point:

```bash
# This script will download and parse the Kepler DR25 and KIC catalogs
python code/data/ingest.py
```
*Output*: `data/raw/kepler_dr25.csv`, `data/raw/kic.csv`

### Step 2: Preprocessing and Filtering
```bash
python code/data/preprocess.py
```
*Output*: `data/processed/filtered_planets.csv`

### Step 3: Gap Analysis
```bash
python code/main.py
```
*Output*: `output/results/analysis_results.json`, `output/plots/radius_gap_distribution.png`

This command performs the following steps in order:
1.  **Ingestion**: Downloads Kepler DR25 and KIC from MAST (if not present), filters by uncertainty thresholds.
2.  **Binning**: Creates log-spaced period bins, merges small bins.
3.  **Analysis**: Fits GMMs, runs bootstraps, validates with KDE.
4.  **Regression**: Calculates slope and compares to theories.
5.  **Validation**: Runs synthetic test.

**Output**: Results are saved to `data/processed/final_analysis.json` and visual plots to `data/processed/plots/`.

## Verification

To verify the pipeline against synthetic data (FR-009):

```bash
python code/validation.py --mode synthetic
```

## Troubleshooting

-   **Data Download Failures**: The script retries up to 3 times with exponential backoff. If it fails, check your internet connection or MAST status.
-   **Memory Errors**: The pipeline is optimized for 7GB RAM. If you encounter OOM, ensure no other heavy processes are running.
-   **GMM Convergence**: If GMM fails to converge in a bin, the bin is flagged as "unresolved" and excluded from the final regression (as per spec).
