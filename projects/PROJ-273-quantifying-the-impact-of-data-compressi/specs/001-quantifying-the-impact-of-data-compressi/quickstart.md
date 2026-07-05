# Quickstart: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GWOSC API (no API key required for public data, but network access needed)
-   Sufficient free disk space (for raw and processed data)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <repo-root>
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `lalsuite` is installed via pip or system package manager (e.g., `pip install lalsuite`).*

## Running the Pipeline

### 1. Download and Validate Data
Fetch a set of CBC injection events and validate metadata.
```bash
python src/main.py --step download --count 15
```
*Output*: `data/raw/gwosc_injections/` containing `.h5` files.

### 2. Apply Compression
Run compression algorithms on the downloaded events.
```bash
python src/main.py --step compress --methods all
```
*Output*: `data/interim/compressed/` containing compressed files and a `metrics.json` with MSE/SNR.

### 3. Run Parameter Estimation
Run LALInference on original and compressed data.
```bash
python src/main.py --step pe --events 12
```
*Note*: This step may take several hours. It is designed to run on CPU-only runners.

### 4. Analyze Results
Compute posterior overlaps and statistical tests.
```bash
python src/main.py --step analyze
```
*Output*: `results/summary_report.md`, `results/figures/`.

## Testing

Run unit tests for compression logic:
```bash
pytest tests/unit/test_compression.py -v
```

Run integration tests for the full pipeline (may be skipped in CI if time-constrained):
```bash
pytest tests/integration/test_pipeline.py -v --maxfail=1
```

## Troubleshooting

-   **Memory Error**: If the pipeline crashes due to RAM, reduce the number of events or enable sampling in `src/utils/config.py`.
-   **GWOSC API Timeout**: Check network connectivity. The API may be rate-limited; add a retry delay in `src/data/download.py`.
-   **LALInference Failures**: Ensure `lalsuite` is correctly installed. Check log files in `data/logs/` for specific error messages.
