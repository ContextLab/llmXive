# Quickstart: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Prerequisites

- Python 3.11+
- Git
- Access to the internet (for downloading Kepler data)

## Installation

1.  **Clone the repository** and navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: pandas, numpy, scikit-learn, scipy, astropy, requests, tqdm, pytest.*

## Data Setup

The pipeline will automatically download the required datasets from the NASA MAST archive on first run. Ensure you have a stable internet connection.

```bash
# Run the ingestion script to download and filter data
python code/ingest/download_kepler.py
python code/ingest/filter_data.py
```

*Note: If manual download is required, place `kepler_dr25.csv` and `kic.csv` in `data/raw/`.*

## Running the Analysis

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1.  Load filtered data.
2.  Bin planets by orbital period.
3.  Estimate gap locations using GMM and validate with KDE.
4.  Perform regression and theoretical comparison.
5.  Save results to `data/processed/final_analysis_results.json`.

## Verifying Results

Check the output logs for:
- **Validation Status**: Should be "PASS" if KDE and GMM agree.
- **Sensitivity Status**: Should be "PASS" if gap difference ≤ 0.05 $R_{\oplus}$.
- **P-values**: Review `p_value_photoevaporation` and `p_value_core_powered`.

## Testing

Run the test suite to ensure pipeline integrity:

```bash
pytest tests/ -v
```

Specific tests:
- `tests/unit/test_gmm_gap_finder.py`: Validates GMM logic on synthetic bimodal data.
- `tests/integration/test_full_pipeline.py`: Runs the full flow on a small subset.

## Troubleshooting

- **MAST Download Failures**: The script includes retry logic (3 attempts with exponential backoff). If it fails, check your internet connection or MAST status page.
- **Memory Errors**: The pipeline is optimized for < 7 GB RAM. If issues arise, reduce the number of bootstrap iterations in `config.yaml` (not implemented yet, but planned).
- **Unresolved Bins**: If a bin is marked "unresolved", it means the data does not show a clear bimodal distribution. This is expected for bins with < 30 planets or low signal-to-noise.
