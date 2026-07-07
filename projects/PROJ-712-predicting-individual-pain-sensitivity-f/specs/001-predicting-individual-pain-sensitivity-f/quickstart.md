# Quickstart: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Prerequisites

-   **Python**: 3.11 or higher.
-   **Memory**: At least 8 GB RAM recommended (minimum 7 GB for CI).
-   **Disk**: Sufficient free space for data and artifacts.
-   **Dependencies**: `mne`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `statsmodels`, `joblib`, `pytest`, `pyyaml`.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-712-predicting-individual-pain-sensitivity-f
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Setup

The pipeline expects raw data in `data/raw/`.

1.  **Download Dataset**:
    -   **CRITICAL**: The project is currently **BLOCKED** because no verified source for the `heat_pain_threshold` variable exists in the "Verified datasets" block.
    -   If a verified source becomes available, fetch the dataset and ensure the `events.csv` and EEG signal files are present in `data/raw/`.
    -   *Note*: Do not use placeholder IDs like "ds003XXX". Use the exact URL from the verified list.

2.  **Verify Integrity**:
    ```bash
    python code/utils.py --verify-checksums
    ```

## Running the Pipeline

**Pre-Run Validation**:
Before running the analysis, the system must validate citations and data availability.
```bash
bash scripts/pre-run-validation.sh
```
If this script fails (non-zero exit), the pipeline will not proceed.

Execute the full analysis pipeline:

```bash
python code/main.py
```

This script will:
1.  **Preprocess**: Load, filter, ICA, and extract microstate features.
2.  **Model**: Run Elastic Net with nested CV and **global** permutation testing.
3.  **Diagnose**: Calculate VIF, Permutation Importance, and perform dual sensitivity analysis.
4.  **Output**: Save results to `artifacts/` and record artifact hashes in `state/projects/...yaml`.

### Running Specific Steps

-   **Preprocessing Only**:
    ```bash
    python code/main.py --step preprocess
    ```
-   **Modeling Only** (requires preprocessed data):
    ```bash
    python code/main.py --step model
    ```
-   **Diagnostics Only**:
    ```bash
    python code/main.py --step diagnostics
    ```

## Testing

Run the test suite to verify the pipeline:

```bash
pytest tests/ -v
```

-   **Unit Tests**: Verify feature extraction logic and ICA component removal.
-   **Integration Tests**: Run the pipeline on a sample of 5 participants (as per US-1).

## Output Interpretation

-   **`artifacts/model_results.json`**: Contains the primary correlation (r), p-value (global permutation), and MAE.
-   **`artifacts/diagnostics.csv`**: Lists feature coefficients, FDR-adjusted p-values (from Permutation Importance), and VIF scores.
-   **`artifacts/sensitivity_report.md`**: Summarizes both the median-split sweep (spec compliance) and the regularization path sweep (scientific validity).

## Troubleshooting

-   **Memory Error**: If you encounter `MemoryError`, ensure the dataset is not loaded entirely into RAM. The pipeline uses chunking (`DataChunk` entity); if issues persist, reduce the number of bootstrap resamples in `code/config.py`.
-   **Convergence Warning**: If Elastic Net fails to converge, the script automatically increases `max_iter` (see Edge Case 2).
-   **Missing Data**: Participants with < 4 minutes of valid EEG are automatically excluded and logged.
-   **Blocked Status**: If the script exits with "Dataset lacks verified pain threshold labels", check the "Verified datasets" block in the project context. The project cannot proceed without a valid source.