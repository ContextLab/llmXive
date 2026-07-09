# Quickstart: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Prerequisites

- Python 3.11+
- pip
- ~10 GB free disk space (for raw data and temporary files)
- Internet connection (to download Planck data)

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `healpy`, `numpy`, `scipy`, `scikit-learn`, `requests`, `astropy`.*

## Running the Pipeline

The full analysis pipeline can be executed via the main script. This will:
1.  Download Planck SMICA map and mask (with retry logic).
2.  Apply the mask.
3.  Compute Minkowski Functionals for the observed map.
4.  Generate a large set of Gaussian simulations.
5.  Compute MFs for simulations.
6.  Perform the Likelihood Ratio Test.
7.  Output results to `output/results.json`.

```bash
python code/main.py
```

### Configuration

To adjust parameters (e.g., number of simulations, thresholds), edit `code/config.yaml` or pass arguments:

```bash
python code/main.py --n-simulations 500 --thresholds "-1 -0.5 0 0.5 1"
```

## Expected Output

Upon successful completion, the following files will be generated:

- `data/processed/masked_cmb.fits`: The masked CMB map.
- `data/processed/mf_vectors.csv`: Table of Minkowski Functional values.
- `output/results.json`: Final statistical results including $p$-value and $G\mu$ upper bound.

### Sample Output Structure (`output/results.json`)

```json
{
  "p_value": 0.045123,
  "g_mu_upper_bound": 1.234567e-07,
  "degrees_of_freedom": 3,
  "model_used": "Gaussian + Cosmic String",
  "covariance_matrix": [
    [0.0012, 0.0005, 0.0001],
    [0.0005, 0.0021, 0.0008],
    [0.0001, 0.0008, 0.0015]
  ],
  "status": "completed"
}
```

## Troubleshooting

- **Memory Error**: If the process crashes with "Memory Error", the system is exceeding the 7GB limit. The script includes a monitor to abort gracefully. If this happens frequently, reduce `--n-simulations` to 500.
- **Download Failed**: If the Planck archive is unreachable, the script will retry 3 times. If it fails, check your internet connection or firewall.
- **Checksum Mismatch**: If the downloaded file does not match the expected checksum, the script will abort. This indicates a corrupted download or a change in the source file.

## Verification

To verify the installation and basic functionality without running the full 1,000 simulation pipeline:

```bash
python code/main.py --dry-run
```

This will download the data, apply the mask, and compute MFs for the observed map only, then exit.
