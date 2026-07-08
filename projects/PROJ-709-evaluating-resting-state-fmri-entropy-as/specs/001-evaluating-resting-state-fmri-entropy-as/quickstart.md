# Quickstart: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

## Prerequisites

- Python 3.11+
- Git
- ~10GB free disk space (for raw fMRI data)
- Internet access (to fetch OpenNeuro ds000305)

## Data Setup

The pipeline automatically fetches the **ADHD-200** dataset from OpenNeuro (ds000305).

1.  **Create Directories**:
    ```bash
    mkdir -p data/raw data/processed data/derived
    ```

2.  **Fetch Data**:
    - The `code/main.py` script includes a fetcher for `ds000305`.
    - Alternatively, you can run `python code/data_loader.py --fetch` to download the data manually.
    - Ensure the phenotypic CSV contains columns: `subject_id`, `Diagnosis`, `ADHD-RS`.

3.  **Verify Data**:
    - Check that `data/raw/` contains at least 10 subjects for testing.
    - Run `python code/utils.py --verify` to check file integrity.

## Installation

1.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

    *Dependencies*: `antropy`, `scikit-learn`, `nibabel`, `nilearn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pytest`, `statsmodels`.

## Running the Pipeline

1.  **Run on Subset (Test)**:
    ```bash
    python code/main.py --subset 5 --output data/processed/test_output.csv
    ```
    - This processes a small cohort of subjects to verify the pipeline runs without errors.
    - Check `exclusions.log` for any excluded subjects.

2.  **Run Full Pipeline**:
    ```bash
    python code/main.py --output data/processed/full_output.csv
    ```
    - This runs the full entropy computation, modeling, and validation.
    - Estimated time: Several hours.

3.  **View Results**:
    - Metrics: `data/derived/model_metrics.json`
    - Plots: `data/derived/` (e.g., `sensitivity_analysis.png`, `permutation_hist.png`)
    - Significant Parcels: `data/derived/significant_parcels.csv`
    - Motion Confound Flag: `data/derived/motion_confound_report.json`

## Troubleshooting

- **Memory Error**: Ensure you are not loading all NIfTI files at once. The pipeline processes subjects sequentially and uses chunked processing for connectivity.
- **Missing Data**: If a subject is missing phenotypic data, it will be excluded from regression but retained for diagnosis if possible. Check `exclusions.log`.
- **No GPU**: The pipeline is designed for CPU. Do not attempt to install CUDA libraries.

## Testing

Run the unit tests:
```bash
pytest tests/unit/
```

Run the integration test (subset):
```bash
pytest tests/integration/test_full_pipeline.py --subset 5
```