# Quickstart: Predicting Molecular Properties

## Prerequisites

- Python 3.11+
- `dftb+` and `psi4` installed and available in PATH (CPU-only version).
- `git` for version control.
- Access to a GitHub Actions runner (or local machine with equivalent resources).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-546-predicting-molecular-properties-from-qua
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline consists of four main steps. Execute them in order.

### Step 1: Download and Validate Data
```bash
python code/download_data.py
```
- Downloads the MAESTRO dataset from the verified Zenodo/HuggingFace URL.
- Computes checksums and stores them in `data/checksums.txt`.

### Step 2: Generate Descriptors
```bash
# Semi-Empirical (DFTB) - Uses DFT-optimized geometries
python code/generate_descriptors.py --method dftb --subset all

# High-Level (DFT) - Restricted to subset
python code/generate_descriptors.py --method dft --subset 30
```
- **Note**: The DFT step is restricted to a computationally feasible number of molecules to fit within the 6-hour runtime limit.

### Step 3: Train and Evaluate Models
```bash
python code/train_models.py
```
- Trains Random Forest models on both descriptor sets.
- Performs 5-fold cross-validation.
- Outputs MAE and p-values for the bootstrap resampling test.

### Step 4: Sensitivity Analysis
```bash
python code/sensitivity_analysis.py
```
- Sweeps feature importance thresholds.
- Generates the sensitivity report.

## Verification

To verify the pipeline:
1.  Check `data/processed/model_results.json` for MAE values.
2.  Verify that the semi-empirical MAE is within 20% of the DFT MAE (or flagged if not).
3.  Ensure `data/checksums.txt` matches the expected hashes.

## Troubleshooting

- **Out of Memory**: If DFT calculation fails, reduce the subset size in `generate_descriptors.py`.
- **Convergence Failure**: The script logs failures and skips the molecule. Check `logs/dftb_failures.log`.
- **Missing Dependencies**: Ensure `dftb+` and `psi4` are in your PATH.