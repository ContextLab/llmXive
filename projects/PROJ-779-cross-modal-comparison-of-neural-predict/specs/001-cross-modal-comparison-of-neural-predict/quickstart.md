# Quickstart: Cross-Modal Comparison of Neural Prediction Error Signals

## Prerequisites

-   Python 3.11+
-   GB RAM minimum (for processing)
-   Internet access (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-779-cross-modal-comparison-of-neural-predict
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `mne`, `numpy`, `scipy`, `scikit-learn`.*

## Running the Pipeline

### 1. Download & Preprocess
Download the canonical OpenNeuro oddball datasets (Auditory and Visual) and run preprocessing.
```bash
python code/main.py --stage download_preprocess
```
*Expected Output*: `data/processed/` directory with cleaned `.h5` files and a `log.txt` confirming trial counts and sampling rates.

### 2. Extract Metrics
Compute difference waves and extract latency/amplitude.
```bash
python code/main.py --stage extract_metrics
```
*Expected Output*: `data/results/metrics.parquet` containing peak latency and amplitude for both modalities.

### 3. Source Localization
Run Minimum Norm Estimation (MNE) and sensitivity analysis.
```bash
python code/main.py --stage localize_sources
```
*Expected Output*: `data/results/sources.parquet` with source strength maps.

### 4. Statistical Analysis
Perform t-tests/permutation tests with BH correction and reliability checks.
```bash
python code/main.py --stage statistical_analysis
```
*Expected Output*: `data/results/stats.json` with p-values, decisions, and Cronbach's α.

### 5. Full End-to-End (CI Mode)
Run the entire pipeline as it would on GitHub Actions.
```bash
python code/main.py --stage full_run
```
*Validation*: Checks for exit code 0, runtime < 6h, and memory < 7GB.

## Troubleshooting

-   **"Sampling rate < 500 Hz"**: The dataset does not meet FR-011. The pipeline halts.
-   **"Insufficient trials"**: Fewer than 100 oddball trials (FR-008). Pipeline halts.
-   **"MNE Failed"**: Low SNR or head model mismatch (FR-010). Pipeline reports failure and skips source analysis for that modality.
-   **"Dataset Not Found"**: If the canonical OpenNeuro fetch fails or is blocked, the pipeline reports the mismatch with the verified list.
