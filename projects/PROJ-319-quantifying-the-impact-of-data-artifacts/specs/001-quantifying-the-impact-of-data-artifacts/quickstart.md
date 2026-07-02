# Quickstart: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

## Prerequisites

*   Python 3.11+
*   Git
*   A POSIX-compliant environment (Linux/macOS/WSL). GitHub Actions `ubuntu-latest` is the target.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-319-quantifying-the-impact-of-data-artifacts
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install --upgrade pip
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins all versions to ensure reproducibility (Constitution Principle I & V).*

## Running the Pipeline

### 1. Generate Synthetic Data
Generates a set of synthetic planetary nebulae with known ground-truth morphology.
```bash
python code/main.py --mode generate --n-images 50 --output data/synthetic
```
*   **Output**: `data/synthetic/*.fits` and `data/synthetic/ground_truth.json`.
* **Time**: [deferred].

### 2. Inject Artifacts & Measure
Applies noise and saturation, then calculates ellipticity and asymmetry.
```bash
python code/main.py --mode process --input data/synthetic --output data/processed
```
*   **Output**: `data/processed/metrics.csv`, `data/processed/artifacts_injected.fits` (optional, can be disabled).
* **Time**: [deferred].

### 3. Fit Calibration Models
Performs regression analysis to derive correction functions.
```bash
python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json
```
*   **Output**: `data/processed/models.json` containing coefficients and p-values.
*   **Time**: < 1 minute.

### 4. Validate Corrections
Applies the correction functions to a held-out test set and reports residual bias.
```bash
python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv
```
*   **Output**: `data/processed/validation_results.csv` with p-values for residual bias (should be $\ge$ 0.05).
*   **Time**: < 1 minute.

### 5. Verify Reproducibility
Generates the verification log required by Constitution Principle II.
```bash
python code/main.py --mode verify --output logs/verification.log
```
*   **Output**: `logs/verification.log` containing citation verification status, random seeds, and file checksums.
*   **Time**: < 1 minute.

## Verification

To ensure the pipeline is reproducible and meets the success criteria (SC-001 to SC-004):

1.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/
    ```
2.  **Run Contract Tests** (Schema Validation):
    ```bash
    pytest tests/contract/
    ```
3.  **Check Reproducibility**:
    Re-run the `generate` and `process` steps with the same random seed (defined in `code/config.py`) and verify that checksums of `data/processed/metrics.csv` and `logs/verification.log` match the previous run.

## Troubleshooting

*   **Memory Error**: If running out of RAM, reduce `--n-images` in the generate step or process images in smaller batches (modify `code/main.py` batch size).
*   **Missing Metadata**: If FITS files are rejected, ensure `astropy` is installed and the input files contain valid `EXPTIME` and `FILTER` keywords.
*   **Non-Reproducible Results**: Ensure `random.seed` is set in `code/config.py` and no external data is fetched dynamically without caching.
*   **Verification Log Missing**: Ensure the `--mode verify` step is run after `calibrate` to generate `logs/verification.log`.