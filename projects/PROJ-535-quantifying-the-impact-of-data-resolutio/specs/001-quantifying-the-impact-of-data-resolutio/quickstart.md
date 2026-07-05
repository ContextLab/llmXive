# Quickstart: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

## Prerequisites

*   Python 3.11+
*   7 GB+ RAM (required for slice processing)
*   14 GB+ disk space
*   Internet connection (for JHTDB data download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-535-quantifying-the-impact-of-data-resolutio
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
    *Note: This installs CPU-optimized versions of numpy, scipy, and h5py.*

## Usage

### 1. Download Data
Run the download script to fetch a verified JHTDB snapshot.
```bash
python code/download.py --snapshot-id coarse_t420 --output data/raw/snap_001.h5
```
*This script verifies the checksum and ensures the file is not corrupted.*

### 2. Generate Downsampled Variants
Create lower-resolution datasets via Fourier truncation.
```bash
python code/downsample.py \
  --input data/raw/snap_001.h5 \
  --factors 2 4 8 16 \
  --output-dir data/processed
```

### 3. Compute Statistics
Calculate energy spectra and structure functions.
```bash
python code/stats.py \
  --input-dir data/processed \
  --output-dir data/stats
```

### 4. Run Full Analysis (Bias & Bootstrap)
Perform bias quantification and bootstrap resampling.
```bash
python code/analysis.py \
  --stats-dir data/stats \
  --bootstrap-iterations 1000 \
  --output results/report.json
```

### 5. Generate Report
The `analysis.py` script automatically generates:
*   `results/bias_plots.png`
*   `results/scaling_exponents.csv`
*   `results/confidence_intervals.csv`

## Verification

To verify the installation and pipeline:
```bash
pytest tests/
```
*This runs unit tests for spectral computation and integration tests for memory limits.*

## Troubleshooting

*   **Memory Error**: If you encounter `MemoryError`, ensure you are not loading the full 1024³ array at once. The scripts are designed to stream data.
*   **Runtime Limit**: If the analysis takes > 6 hours, reduce `--bootstrap-iterations` to 500.
*   **No Inertial Subrange**: If the report flags "Inertial Subrange Not Resolved", try a different snapshot with a higher Reynolds number.
