# Quickstart: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins versions of `healpy`, `astropy`, `scipy`, etc., to ensure reproducibility.*

## Running the Analysis

### Step 1: Download and Ingest Data
The system automatically downloads the Pantheon+ dataset if `data/raw/` is empty.
```bash
python code/ingest.py
```
*Output*: `data/processed/supernova_records.csv` and `data/metadata.json`.

### Step 2: Run Likelihood Analysis
Computes dipole and quadrupole amplitudes using Maximum Likelihood Estimation.
```bash
python code/likelihood_analysis.py
```
*Output*: `data/processed/likelihood_results.json`.

### Step 3: Run Null Simulations
Generates a sufficient number of isotropic mock catalogs (streaming scalar storage) to establish significance.
```bash
python code/simulations.py
```
*Output*: `data/processed/simulation_results.csv` and `data/processed/analysis_summary.json`.

### Step 4: Validate Results
Run the contract tests to ensure data integrity.
```bash
pytest tests/contract/
```

## Verification

- **Check Data Count**: Ensure `data/processed/supernova_records.csv` contains a sufficient volume of records (excluding filtered entries).
- **Check Reproducibility**: Re-run `main.py` with the same seed and verify that the `dipole_amplitude` and `p-value` in `analysis_summary.json` are identical.
- **Check Disk Usage**: Verify that `data/processed/simulation_results.csv` is small (<1MB) despite containing [deferred] runs, confirming the streaming approach.

## Troubleshooting

- **Memory Error**: If running out of RAM, reduce `N_SIMULATIONS` in `code/simulations.py` to a lower value and note the reduced power.
- **Network Error**: If the Pantheon+ download fails, check the GitHub URL in `code/ingest.py` or manually download `pantheon_plus.csv` and place it in `data/raw/`.
- **Likelihood Convergence**: If the MLE fails to converge, check the `intrinsic_scatter` initialization in `code/likelihood_analysis.py`.