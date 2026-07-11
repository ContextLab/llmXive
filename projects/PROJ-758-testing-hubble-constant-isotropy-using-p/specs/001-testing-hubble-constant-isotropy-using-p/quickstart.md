# Quickstart: Testing Hubble Constant Isotropy

## Prerequisites

- Python 3.11+
- Git
- Access to the Pantheon+ dataset (fetched automatically from Zenodo)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd llmXive/projects/PROJ-758-testing-hubble-constant-isotropy-using-p
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

4.  **Verify environment**:
    ```bash
    python -c "import healpy; import astropy; print('Environment OK')"
    ```

## Running the Analysis

The analysis is driven by a CLI script.

1.  **Download and process data**:
    ```bash
    python src/main.py --action ingest --redshift-limit 0.15
    ```
    This will:
    - Fetch Pantheon+ from Zenodo.
    - Apply quality cuts and redshift limits.
    - Assign HEALPix pixels.
    - Calculate peculiar velocity corrections.
    - Save to `data/processed/`.

2.  **Estimate H0**:
    ```bash
    python src/main.py --action estimate
    ```
    This will:
    - Fit the global model.
    - Fit local models for pixels with N >= 30.
    - Apply Empirical Bayes shrinkage for pixels with N < 30.
    - Save results to `data/processed/h0_estimates.parquet`.

3.  **Run Anisotropy Test**:
    ```bash
    python src/main.py --action anisotropy --n-simulations 1000
    ```
    This will:
    - Compute dipole and quadrupole moments.
    - Run 1,000 Monte Carlo simulations (using linearized approximation).
    - Apply FDR correction.
    - Save results to `data/results/anisotropy_metrics.json`.

4.  **Sensitivity Analysis** (Optional):
    ```bash
    python src/main.py --action sensitivity --cuts 0.10,0.15,0.20 --no-pecvel
    ```

## Verification

To verify the results:

1.  **Check Data Integrity**:
    ```bash
    python tests/contract/test_schemas.py
    ```
    Ensure all output files match the expected schema.

2.  **Reproduce Global H0**:
    Check `data/processed/h0_estimates.parquet` for the "global" entry.

3.  **Check Anisotropy Significance**:
    Review `data/results/anisotropy_metrics.json`. The `is_significant` flag should be `False` if the universe is isotropic.

## Troubleshooting

- **Memory Error**: If you encounter memory issues, reduce the number of Monte Carlo simulations (`--n-simulations`).
- **Missing Data**: If the pipeline fails to fetch Pantheon+, check your internet connection or the Zenodo URL.
- **HEALPix Errors**: Ensure `healpy` is installed correctly; it requires a C compiler.