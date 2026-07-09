# Quickstart: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient RAM available (for data processing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-199-predicting-the-impact-of-cold-rolling-re
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `orix` and `scikit-learn` are CPU-optimized. No GPU drivers required.*

## Data Acquisition

The pipeline automatically downloads the synthetic EBSD dataset from the verified HuggingFace source.

```bash
python code/main.py --task download
```
-   **Output**: `data/raw/data_synth_ebsd.zip`
-   **Verification**: Checksum is recorded in `state/...yaml`.

## Pre-processing & Texture Quantification

This step filters low-confidence points, re-indexes to FCC symmetry, and calculates texture descriptors.

```bash
python code/main.py --task preprocess
python code/main.py --task quantify
```
-   **Output**: `data/processed/texture_descriptors.parquet`
-   **Validation**: Mass balance check (sum ≈ unity) is performed automatically.

## Model Training & Validation

Train the Gaussian Process and Polynomial models with 5-fold cross-validation.

```bash
python code/main.py --task train
```
-   **Output**: `data/processed/model_metrics.json` (R², RMSE per metal/descriptor).
-   **Success Criterion**: R² ≥ 0.85 for all metals and descriptors.

## Sensitivity Analysis & Robustness

Run the sensitivity sweep and residual variance analysis.

```bash
python code/main.py --task robustness
```
-   **Output**: `data/processed/robustness_report.json` (R² stability, residual variance %).

## Reproducing Results

To ensure reproducibility (Constitution Principle I), run the full pipeline:

```bash
python code/main.py --task full-pipeline
```
-   This executes download → preprocess → quantify → train → robustness in order.
-   Random seeds are pinned in `code/`.

## Troubleshooting

-   **Memory Error**: If processing fails due to RAM, the pipeline automatically samples data. Check logs for "Sampling enabled".
-   **Missing Data**: If a specific metal/reduction combination is missing, the pipeline logs a warning and proceeds with available data (US-1, AC-3).
-   **Symmetry Error**: Ensure `orix` is installed correctly; re-indexing to FCC is mandatory.
