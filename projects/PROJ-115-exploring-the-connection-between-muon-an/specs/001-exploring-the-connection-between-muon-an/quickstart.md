# Quickstart: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

## Prerequisites

- Python +
- A minimal multi-core CPU configuration and 4 GB RAM (minimum for 30-min runtime)
- Internet access (for downloading LEP data)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-115-exploring-the-connection-between-muon-an/code
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
    *Dependencies*: `scipy`, `numpy`, `matplotlib`, `pandas`, `requests`, `reportlab`.

4.  **Download external data**:
    ```bash
    python scripts/download_data.py
    ```
    *Note*: This script fetches `lepaute_data.json` and verifies its SHA-256 checksum against `data_manifest.json`. If the checksum does not match, the script will abort with a clear error message. If `xenon1t_limits.csv` is missing, the script will use the hardcoded curve from the 2014 paper and log a warning.

## Running the Scan

### 1. Validate Physics Implementation
Before running the full scan, verify the $\Delta a_\mu$ calculation against the benchmark.
```bash
python scripts/validate_delta_a.py
```
*Expected Output*: "Validation passed: relative error < 2%".

### 2. Validate Sommerfeld Calculation
Verify the Sommerfeld enhancement calculation against a non-perturbative solver.
```bash
python scripts/validate_sommerfeld.py
```
*Expected Output*: "Sommerfeld validation passed: relative error < 5%".

### 3. Execute the Parameter Scan
Run the full grid scan:
```bash
python scripts/run_scan.py
```
*Output*:
- `viable_points.csv` (list of viable parameter points)
- `viable_region.png` (contour plot)
- `summary.txt` (scan summary)

*Runtime*: Expected ≤ 30 minutes on 2-core CPU.

### 4. Generate the Report
Create the PDF report:
```bash
python scripts/make_report.py
```
*Output*: `g2_dm_report.pdf` containing plots, tables, and reproducibility metadata.

## Troubleshooting

- **Error: "Checksum mismatch"**: The downloaded data file does not match the expected hash. Check your internet connection and re-run `download_data.py`.
- **Error: "Xenon1T data missing"**: The script will use the hardcoded curve from the 2014 paper and log a warning. The scan will proceed.
- **Error: "Numerical overflow"**: Coupling $g$ is too large. The script caps $g$ at 1.0 and logs a warning.
- **Runtime > 30 mins**: The adaptive scanning strategy and pre-computation tables should prevent this. If it occurs, check for system resource constraints.

## Data Hygiene

- All downloaded files are stored in `data/` with checksums.
- Do not modify files in `data/` manually.
- To clear cache and re-download: `rm -rf data/* && python scripts/download_data.py`.