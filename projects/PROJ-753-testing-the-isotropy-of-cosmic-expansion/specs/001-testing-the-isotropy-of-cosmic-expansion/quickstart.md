# Quickstart: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-753-testing-isotropy-of-cosmic-expansion
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `healpy` installs the CPU wheel. If it fails, install `numpy` and `scipy` first, then `healpy`.*

## Data Preparation

The `code/ingest.py` script will automatically download the Pantheon+ dataset if `data/raw/` is empty.

1. **Run the ingestion script**:
   ```bash
   python code/ingest.py
   ```
   This will:
   - Download the Pantheon+ release.
   - Verify the SHA‑256 checksum and record it in `data/metadata.json`.
   - Filter out entries with missing RA, Dec, redshift, or distance‑modulus uncertainty.
   - Apply the **redshift cut `z > 0.02`** (to suppress peculiar‑velocity bias) and compute theoretical distance moduli.
   - Save `data/processed/supernovae_clean.csv`.

## Running the Analysis

Execute the full pipeline (Ingest → Harmonics → Simulation → Report):

```bash
python code/main.py
```

The script will:

1. Load the cleaned supernova catalogue.  
2. Project residuals onto a HEALPix grid (Nside = 32) with inverse‑variance weighting.  
3. Compute dipole and quadrupole amplitudes using the pseudo‑Cₗ + MASTER pipeline (regularised λ = 1e‑6).  
4. Run up to **10 000** rotation‑based mock catalogs (runtime monitor will halve the remaining iterations if the wall‑clock time exceeds 5 h).  
5. Calculate p‑values, flag significance, and write `data/processed/final_results.json`.  
6. Generate diagnostic plots in `reports/`.

## Verifying Results

1. **Check the output**:
   ```bash
   cat data/processed/final_results.json
   ```
   Look for `is_significant`: `true` if the dipole p‑value < 0.05.

2. **Reproducibility Check**:
   Re‑run `python code/main.py`; results must be identical because the random seed is fixed.

## Troubleshooting

- **`healpy` installation error**: Ensure you are using Python 3.11 and have `numpy`/`scipy` installed before `healpy`.  
- **Missing data**: If the script cannot download the dataset, manually download the Pantheon+ release from the official GitHub repo and place the CSV in `data/raw/`.  
- **Runtime > 6 h**: The pipeline automatically reduces the number of simulations after the 5‑hour mark; you can also manually lower `N_SIM_MAX` in `code/config.py` (default = 10 000).
