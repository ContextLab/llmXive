# Quickstart: Assessing the Validity of the Cosmological Principle with Public CMB Data

## Prerequisites

- Python 3.11+
- Git
- Sufficient free disk space (for downloads and intermediate files)
- 7 GB RAM

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-368-assessing-the-validity-of-the-cosmologic
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `healpy` may require compilation. Ensure `gcc` and `fftw3` are installed on your system.*

3.  **Verify Environment**
    ```bash
    python -c "import healpy; print(healpy.__version__)"
    ```

## Running the Analysis

### 1. Download Data
Run the data loader to fetch Planck data (if not already present in `data/raw/`).
```bash
python code/data_loader.py --download
```
*Note: If the ESA archive is unreachable, this script will exit with an error. Check `data/raw/` for existing files.*

### 2. Preprocess
Apply mask and downgrade resolution.
```bash
python code/data_loader.py --preprocess
```
*Output: `data/processed/planck_masked_nside128.fits`*

### 3. Run Full Pipeline
Execute the main analysis script.
```bash
python code/main.py
```
*This will:*
1.  Compute $C_l$ for full sky and hemispheres.
2.  Generate a sufficient number of Monte Carlo simulations to ensure statistical robustness.
3.  Compute the null distribution using the **Maximum Statistic** approach ($T = \max(|A_{NS}|, |A_{EW}|)$).
4.  Calculate p-values based on the Maximum Statistic.
5.  Print results to stdout.

### 4. Sensitivity Analysis
Run the threshold sweep.
```bash
python code/sensitivity.py
```

## Expected Output

The `main.py` script will output a summary:
```text
[INFO] Full-sky C_l computed.
[INFO] Hemispherical splits computed.
[INFO] Generated a series of Monte Carlo simulations.
[INFO] Observed Statistic (N/S):
[INFO] Observed Statistic (E/W): A value near unity
[INFO] Maximum Statistic (T):
[INFO] Null Distribution Mean: 0.00, Std:
[INFO] P-value (Maximum Statistic):
[INFO] Result: Anomaly detected at 95% confidence (p < 0.05).
```
*Note: The Benjamini-Hochberg correction is NOT applied. The p-value is derived from the Maximum Statistic approach, which is statistically appropriate for dependent tests.*

## Troubleshooting

- **ImportError: healpy**: Ensure `fftw3` is installed (`sudo apt-get install libfftw3-dev` on Linux).
- **MemoryError**: Ensure you are using the Nside=128 downgraded map. Do not run on Nside=2048.
- **Checksum Mismatch**: Re-run `data_loader.py --download` to fetch a fresh copy.