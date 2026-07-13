# Quickstart: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Internet access (to fetch verified datasets)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed sequentially via the provided scripts.

### Step 1: Download and Validate Data
```bash
python code/01_download.py
```
*Expected Output*: `data/raw/MeLiDC.parquet` and `data/checksums.txt`.

### Step 2: Preprocess and Engineer Features
```bash
python code/02_preprocess.py
```
*Expected Output*: `data/processed/dataset_cleaned.csv`.
*Note*: This step filters for BCC, computes descriptors, and logs the diffusion coefficient.

### Step 3: Train Models
```bash
python code/03_train.py
```
*Expected Output*: `code/outputs/model_results.json`.
*Note*: This runs the grid search for RF, XGBoost, and Elastic Net.

### Step 4: Evaluate and Analyze
```bash
python code/04_evaluate.py
```
*Expected Output*: `code/outputs/feature_importance.json`, `code/outputs/variance_partition.csv`, and SHAP plots.

## Verification

To ensure the pipeline meets the contract:
```bash
pytest tests/test_contracts.py
```
This validates that output files match the schemas defined in `contracts/`.

## Troubleshooting

- **HTTP 401 on Download**: The `MeLiDC` URL is the only verified source. If it fails, the script will raise `DataInsufficientError`. Do not attempt to use other URLs.
- **Memory Error**: Ensure you are running on a machine with at least 7 GB RAM. The script will attempt to load data in chunks if necessary.
- **Data Insufficient**: If the BCC filter yields < 30 samples, the script will halt with a `PowerWarning`.
