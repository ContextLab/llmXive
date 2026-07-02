# Quickstart: Solar Flare-Storm Correlation

## Prerequisites

-   Python 3.11+
-   `pip` (or `venv`/`conda`)
-   Network access to NOAA SWPC and CDAWeb (for data ingestion).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-031-exploring-the-correlation-between-solar-/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `scipy`, `statsmodels`, and `pandas` are installed:
    ```bash
    python -c "import scipy, statsmodels, pandas; print('Dependencies OK')"
    ```

## Running the Pipeline

### 1. Ingest Data
Download raw data from NOAA/CDAWeb:
```bash
python code/ingest.py --years 10 --output data/raw/
```
*Note: This step may take a few minutes depending on network speed.*

### 2. Align Events
Match storms to solar events within the 3-day window:
```bash
python code/align.py --input data/raw/ --output data/processed/aligned_events.csv
```

### 3. Run Analysis
Perform correlations, regression, and threshold sensitivity:
```bash
python code/analysis.py --input data/processed/aligned_events.csv --output results/
```

### 4. Validate Results
Check output against schema contracts:
```bash
python code/validate.py --data results/metrics.json --schema contracts/metrics.schema.yaml
```

## Expected Outputs

-   `data/processed/aligned_events.csv`: Unified dataset with flags.
-   `results/metrics.json`: Correlation coefficients, p-values, R², VIF, and detection rates.
-   `results/figures/`: Plots of correlations and threshold sensitivity.
-   `results/logs/pipeline.log`: Execution time, RAM usage, and power analysis warnings.

## Troubleshooting

-   **Network Errors**: If `ingest.py` fails, check firewall settings. The pipeline requires access to `ftp.swpc.noaa.gov` and `cdaweb.gsfc.nasa.gov`.
-   **Missing Data**: If `aligned_events.csv` has many nulls, this is expected for slow CMEs. The analysis handles this via flags.
-   **Power Warning**: If `results/metrics.json` contains a `power_limitation_warning`, the sample size was < 30. Interpret threshold claims with caution.
