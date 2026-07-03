# Quickstart: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## 1. Prerequisites

*   Python 3.11+
*   `pip` (or `conda`)
*   Internet access (for dataset download)

## 2. Installation

```bash
# Clone the repository (placeholder command)
git clone <repo-url>
cd <project-root>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Key Dependencies**:
*   `mne`: EEG processing
*   `scikit-learn`: Modeling
*   `pandas`, `numpy`: Data manipulation
*   `statsmodels`: Statistics
*   `pyyaml`: Contract validation

## 3. Running the Pipeline

The pipeline is designed to run end-to-end on a CPU-only environment.

### Step 1: Ingest & Preprocess
```bash
python code/01_ingest_preprocess.py
```
*   Downloads datasets from verified URLs.
*   Computes SHA-256 checksums and verifies integrity.
*   Detects missing paired data; switches to **Positive Control Mode**.
*   Generates synthetic targets with **injected signal**.
*   Output: `data/processed/epochs.csv` (or `.fif`).

### Step 2: Feature Extraction
```bash
python code/02_feature_extraction.py
```
*   Computes spectral power and **ROI-specific connectivity** (C3-C4, etc.).
*   Output: `data/processed/features.csv`.

### Step 3: Modeling
```bash
python code/03_modeling.py
```
*   Fits Ridge Regression with 5-fold CV.
*   In Positive Control Mode: Verifies detection of injected signal.
*   Output: `models/ridge_model.pkl`, `data/processed/model_metrics.json`.

### Step 4: Validation
```bash
python code/04_validation.py
```
*   Runs 1,000 permutations.
*   Applies FDR correction.
*   Performs sensitivity analysis (p ∈ {0.01, 0.05, 0.1}, R² ∈ {0.2, 0.3, 0.4}).
*   Calculates `stability_variance`.
*   Output: `data/processed/validation_report.csv`.

### Step 5: Report Generation
```bash
python code/05_report.py
```
*   Generates final summary table and plots.

## 4. Verification

To verify the pipeline on a small subset:

```bash
# Run unit tests
pytest tests/ -v

# Run integration test (Positive Control mode)
python code/03_modeling.py --mode positive_control --test
```

## 5. Troubleshooting

*   **Memory Error**: Reduce `--epochs-per-subject` in `config.py` or enable `--batch-processing`.
*   **Missing Data**: If the dataset lacks pairing, the system will automatically switch to **Positive Control Mode** and log a warning. No manual intervention required.
*   **CUDA Error**: Ensure no GPU-specific flags are set. The pipeline is CPU-only by design.
*   **Checksum Mismatch**: If raw data checksums do not match the manifest, the pipeline will halt. Re-download data.