# Quickstart: Testing Cosmic Ray Arrival Direction Isotropy

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the internet (for downloading dependencies and data)

## Installation

1.  **Clone the repository** (or the specific feature branch):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso
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

## Running the Pipeline

The pipeline is executed via the main script located in `code/`.

### Step 1: Data Ingestion
Download and preprocess the UHECR event catalogs.
```bash
python code/ingestion/download_events.py
python code/ingestion/preprocess.py
```
*Note: This step will **fail** if the specific pinned versions of the Pierre Auger or Telescope Array data are unavailable. No synthetic data is generated.*

### Step 2: Analysis
Compute the HEALPix maps and the Angular Power Spectrum.
```bash
python code/analysis/healpix_conversion.py
python code/analysis/power_spectrum.py
```

### Step 3: Monte Carlo Simulations
Generate the null distribution.
```bash
python code/analysis/monte_carlo.py
```
*This step runs a sufficient number of simulations to balance statistical precision with the runtime limit.*

### Step 4: Statistical Testing
Calculate the global p-value and determine significance.
```bash
python code/stats/significance_test.py
```

### Step 5: View Results
The final results will be saved in `data/processed/results.json`.
```bash
cat data/processed/results.json
```

## Verification

To verify the installation and pipeline integrity:
1.  Run the unit tests:
    ```bash
    pytest tests/unit/
    ```
2.  Run the integration test (full pipeline on synthetic data **only for code validation**, not scientific results):
    ```bash
    pytest tests/integration/test_full_pipeline.py
    ```
    *Note: The integration test uses a synthetic dataset to verify the code logic, but the main pipeline (Step 1) requires real data for the scientific result.*

## Troubleshooting

*   **Missing Data**: If `data/raw/` is empty, check your internet connection and the status of the Pierre Auger/Telescope Array public websites. If the specific pinned versions are unavailable, the pipeline will halt.
*   **Memory Errors**: The pipeline is optimized for < 7 GB RAM. If you encounter OOM errors, reduce `Nside` in `config.yaml` (though this is not recommended for $\ell=5$).
*   **Slow Execution**: Ensure you are running on a multi-core environment. The Monte Carlo step can be parallelized by setting `NUM_WORKERS` in `code/config.yaml`.