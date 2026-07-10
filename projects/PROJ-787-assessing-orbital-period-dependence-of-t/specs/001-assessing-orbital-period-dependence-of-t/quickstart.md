# Quickstart: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Prerequisites

- Python 3.11+
- `pip`
- Access to the Kepler MAST archive (for data download).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-787-assessing-orbital-period-dependence-of-t
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Verify environment**:
    ```bash
    python -c "import pandas, sklearn, scipy; print('All dependencies loaded successfully.')"
    ```

## Running the Pipeline

### Step 1: Data Ingestion (Manual or Automated)
*Note: Due to MAST access requirements, ensure network connectivity.*

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

### Step 4: Validation
The pipeline automatically runs KDE validation and synthetic tests. Check `output/results/validation_report.json` for pass/fail status.

## Testing

Run the unit tests to verify GMM logic and filtering:

```bash
pytest tests/ -v
```

## Troubleshooting

- **Data Download Failures**: The `ingest.py` script includes exponential backoff. If it fails after 3 retries, check your network or MAST status.
- **Memory Errors**: The pipeline processes data in chunks. If you encounter OOM, ensure no other heavy processes are running.
- **Unimodal Bins**: If a bin is flagged as "unimodal" (BIC diff < 10), it is automatically merged with the adjacent bin. Check logs for merge events.