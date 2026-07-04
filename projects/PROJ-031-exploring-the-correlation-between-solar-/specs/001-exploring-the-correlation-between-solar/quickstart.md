# Quickstart: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to the internet (for data download)

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Execution

Run the full pipeline:
```bash
python code/main.py
```

This command will:
1.  Download raw data from NOAA SWPC and CDAWeb (if not already present).
2.  Align events and generate `data/processed/aligned_events.csv`.
3.  Perform statistical analysis (correlation, regression, power analysis).
4.  Identify thresholds and run sensitivity analysis.
5.  Write results to `results/metrics.json`.
6.  Validate all outputs against `contracts/`.

## Verification

After execution, verify the results:
1.  Check `results/metrics.json` for correlation coefficients, p-values, and performance metrics.
2.  Run the validation script manually:
    ```bash
    python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml
    ```
3.  Ensure `data/source_manifest.yaml` contains the correct URLs and checksums.

## Troubleshooting

- **Network Errors**: If data download fails, check your internet connection and firewall settings. The pipeline will retry up to 3 times.
- **Missing Data**: If `aligned_events.csv` contains many `NaN` values, this is expected if no solar precursor was found within the 3-day window.
- **Memory Errors**: If the pipeline exceeds 7 GB RAM, reduce the historical window in `config.py` (not recommended for standard runs).
