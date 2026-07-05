# Quickstart: Neural Entropy and Cognitive Flexibility in Aging

## Prerequisites

*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI) or a local Linux environment with 7GB+ RAM.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-454-investigating-the-relationship-between-n/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import mne; import neurokit2; import statsmodels; print('All imports OK')"
    ```

## Running the Pipeline

### 1. Data Download & Verification
Run the data loader to fetch verified datasets and check for required variables (specifically WCST).
```bash
python main.py --stage download
```
*   **Output**: `data/raw/` populated with parquet files.
*   **Check**: If `wcst_perseverative_errors` is missing, the script will exit with `DATASET_VARIABLE_MISMATCH`.

### 2. Preprocessing
Preprocess EEG signals (filter, ICA, epoch).
```bash
python main.py --stage preprocess
```
*   **Output**: `data/processed/` containing cleaned epochs.
*   **Note**: Participants with SNR < 5 dB are excluded here.

### 3. Entropy Computation
Compute Sample and Approximate Entropy.
```bash
python main.py --stage entropy
```
*   **Output**: `data/derived/entropy.parquet`.

### 4. Statistical Analysis
Run OLS, VIF checks, and FDR correction.
```bash
python main.py --stage analyze
```
*   **Output**: `data/derived/correlations.parquet`, `data/derived/report.json`.

### 5. Sensitivity Analysis
Run exclusion and threshold sweeps.
```bash
python main.py --stage sensitivity
```
*   **Output**: `data/derived/sensitivity_report.json`.

## Testing

Run unit and contract tests:
```bash
pytest tests/
```

## Troubleshooting

*   **Memory Error**: Reduce the number of participants processed in parallel or use chunked processing in `preprocess.py`.
*   **NaN Entropy**: Check for insufficient epochs (< 60s total). The pipeline should exclude these participants automatically.
*   **Missing WCST**: The pipeline will fail if the verified dataset lacks WCST columns. This is a spec gap; no workaround is provided.
*   **High Collinearity**: If VIF > 5, ApEn is automatically dropped from the joint model.