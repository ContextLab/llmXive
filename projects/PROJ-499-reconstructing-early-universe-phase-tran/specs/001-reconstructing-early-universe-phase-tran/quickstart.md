# Quickstart: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

## Prerequisites

-   Python 3.11+
-   `pip`
-   Access to the internet (for dataset download).

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `pyhealpix`, `dynesty`, `emcee`, `numpy`, `scipy`, `requests`, `astropy`, `astroquery`.*

## Running the Pipeline

### 1. Synthetic Validation (Mandatory First Step)

Validate the pipeline using synthetic data before running on real observations.
```bash
python code/validation.py --mode synthetic
```
*Expected Output*: Check that recovered $r$ is within $1\sigma$ of the input value AND that Phase Transition signals are correctly identified.

### 2. Data Ingestion and Preprocessing

Run the data ingestion script to download and mask the CMB maps.
```bash
python code/data_ingestion.py
```
*Expected Output*: `data/derived/masked_bmode_nside64.fits` and `data/derived/observed_cl_bb.json`.

### 3. Model Fitting and Comparison

Run the full inference and model comparison.
```bash
python code/inference.py
python code/model_comparison.py
```
*Expected Output*: `data/derived/posterior_samples.h5`, `data/derived/model_comparison_results.json`.

### 4. Visualization

Generate diagnostic plots (power spectra, corner plots, Bayes factor analysis).
```bash
python code/plotting.py
```
*Output*: Figures in `docs/figures/`.

## Troubleshooting

-   **Dataset Unavailable**: If the download fails, check the logs for "Connection refused" or "DNS failure". The script retries 3 times. If it fails permanently, verify network connectivity.
-   **MCMC Convergence**: If the output indicates "Convergence Failed", check `data/derived/posterior_samples.h5` for `convergence_status: false`. Consider increasing the number of steps in `code/inference.py`.
-   **Memory Error**: Ensure `Nside` is set to 64 in `data_ingestion.py`. Higher resolutions may exceed RAM on the free-tier runner.

## Verification

To verify the installation and data integrity:
```bash
python -c "import pyhealpix; import dynesty; print('Dependencies OK')"
python code/validation.py --mode check
```