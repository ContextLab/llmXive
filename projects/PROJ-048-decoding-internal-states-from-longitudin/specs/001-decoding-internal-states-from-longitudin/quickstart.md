# Quickstart: Decoding Internal States from Longitudinal Calcium Imaging Data

## Prerequisites
*   Python 3.11+
*   5GB+ free RAM (recommended 7GB+ for safety)
*   Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-048-decoding-internal-states-from-longitudin
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `scikit-learn`, `numpy`, and `scipy` are installed in CPU-only mode.*

## Running the Pipeline

### 1. Download Data
Run the download script. This will attempt to fetch the Allen dataset or the verified fallback.
```bash
python code/data/download.py
```
*   *Output*: `data/raw/session_*.parquet`
*   *Check*: Verify file size < 5GB.

### 2. Preprocess Data
Normalize, detrend, and deconvolve the data.
```bash
python code/data/preprocess.py
```
*   *Output*: `data/processed/dF_norm.npz`
*   *Check*: Ensure no `NaN` values in output.

### 3. Run NMF Analysis
Extract latent states with temporal regularization.
```bash
python code/analysis/nmf_engine.py --k 10 20 30
```
*   *Output*: `data/processed/components_H.npz`, `data/processed/weights_W.npz`
*   *Check*: Ensure runtime < 6h.

### 4. Statistical Validation
Perform correlation and permutation tests.
```bash
python code/analysis/stats.py
```
*   *Output*: `data/results/correlations.csv`
*   *Check*: Verify p-values and significance flags.

## Testing
Run the test suite to verify contract compliance.
```bash
pytest tests/ -v
```

## Troubleshooting
*   **MemoryError**: Reduce the session subset size or `k` value.
*   **DataGapError**: The required dataset is missing. Check `research.md` for fallback strategies.
*   **NMF Convergence**: Increase `max_iter` or try different `init` strategies.
