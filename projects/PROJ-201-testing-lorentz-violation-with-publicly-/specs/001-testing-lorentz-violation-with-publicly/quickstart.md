# Quickstart: Testing Lorentz Violation with Publicly Available CMB Data

## Prerequisites

*   Python 3.11+
*   `pip`
*   Substantial disk space (for raw maps and simulations)
*   Internet access (for initial data download from ESA)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-201-testing-lorentz-violation-with-publicly-/code
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
    *Note: `healpy` requires a C++ compiler. If installation fails, install `libhealpix` via your system package manager first.*

4.  **Configure**:
    *   Edit `config.yaml` to set the ESA download URLs and random seeds.

## Running the Pipeline

The pipeline is executed via `main.py`.

### 1. Download and Verify Data
```bash
python main.py --step download
```
*This step fetches the PR3 data from the ESA Legacy Archive (FITS format) and verifies checksums.*

### 2. Process Maps
```bash
python main.py --step process
```
*Applies masks and deconvolves beam functions.*

### 3. Run Analysis
```bash
python main.py --step analyze
```
*Computes power spectra (\(\ell < 200\)), dipole modulation, and BipoSH coefficients (L=2,3). Includes Minkowski functional check.*

### 4. Run Inference (MCMC)
```bash
python main.py --step infer --samples 10000
```
*Performs MCMC sampling to constrain the SME coefficient. This step may take several hours.*

## Output

Results are saved in `data/results/`:
*   `anisotropy_metrics.yaml`: Dipole and BipoSH results (with FDR corrected p-values).
*   `sme_constraints.json`: Final posterior distributions.
*   `diagnostics.log`: Convergence warnings and runtime stats.

## Troubleshooting

*   **RAM Error**: If the job fails due to memory limits, the script will automatically attempt to subsample multipoles. If this fails, reduce the `--nside` parameter in `config.yaml`.
*   **Data Missing**: If the ESA archive is unreachable, the script will exit with `ERROR_DATA_UNAVAILABLE`. Check the `research.md` for the specific dataset gap.