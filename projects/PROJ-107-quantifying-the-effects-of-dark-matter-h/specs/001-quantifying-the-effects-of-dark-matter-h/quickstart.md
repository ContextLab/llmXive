# Quickstart: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## Prerequisites

*   Python 3.11+
*   `git`
*   Access to the IllustrisTNG public data portal (for TNG-100).
*   (Optional) Millennium-II data access (conditional).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd specs/001-quantifying-the-effects-of-dark-matter-h
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Configuration

1.  **Set Data Paths**:
    Edit `code/utils/config.py` to point to your local data directory or configure the download URLs.
    ```python
    # config.py
    DATA_DIR = "data/raw"
    TNG_API_URL = "https://www.tng-project.org/api/"
    ```

2.  **Set Random Seeds**:
    Ensure reproducibility by setting the seed in `code/utils/config.py`:
    ```python
    RANDOM_SEED = 42
    ```

## Running the Pipeline

### Step 1: Ingest Data
Download and prepare the TNG-100 dataset (chunked).
```bash
python code/main.py --step ingest --dataset tng100
```
*Output*: `data/processed/halo_shapes.csv`, `data/processed/galaxy_properties.csv`

### Step 2: Compute Shapes & Alignments
Calculate inertia tensors and misalignment angles.
```bash
python code/main.py --step compute_shapes
```
*Output*: Updated `halo_shapes.csv` with triaxiality and `alignment_angles.csv`.

### Step 3: Null Simulation Control
Run the shuffled null simulation to check for artifacts.
```bash
python code/main.py --step null_control --iterations 10000
```
*Output*: `data/processed/null_control_results.csv`

### Step 4: Statistical Analysis
Run hypothesis tests and regression.
```bash
python code/main.py --step analyze --mass-match
```
*Output*: `data/processed/analysis_results.csv`

### Step 5: Sensitivity Analysis
Sweep binning thresholds (Effect Size Stability).
```bash
python code/main.py --step sensitivity --thresholds "0.45,0.55,0.75,0.85"
```
*Output*: `data/processed/sensitivity_report.csv`

### Step 6: Generate Report
Compile results into a summary.
```bash
python code/main.py --step report
```
*Output*: `outputs/reports/summary.md`

## Testing

Run the unit tests to verify tensor calculations and statistical logic:
```bash
pytest code/tests/ -v
```

## Troubleshooting

*   **Memory Error**: Reduce the chunk size in `code/utils/config.py` (e.g., `CHUNK_SIZE = 2000`).
*   **Missing Data**: Ensure you have registered with the IllustrisTNG website and have an API key set in the environment variable `TNG_API_KEY`.
*   **Millennium-II Unavailable**: If the pipeline logs "Data Gap: Millennium-II not found", the cross-validation step is skipped. This is expected if no verified URL is provided.