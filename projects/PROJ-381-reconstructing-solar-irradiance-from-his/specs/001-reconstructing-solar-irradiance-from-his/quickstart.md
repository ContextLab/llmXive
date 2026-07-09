# Quickstart: Reconstructing Solar Irradiance from Historical Sunspot Records

## Prerequisites
*   Python 3.11+
*   `pip`
*   ~5 GB free disk space (for data and virtual environment).

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

## Data Preparation

The pipeline attempts to download data from verified URLs. If any URL fails, the pipeline halts with a `DataValidationError`.

1.  **Run the ingestion script**:
    ```bash
    python code/data/ingestion.py
    ```
    *Output*: Raw data files in `data/raw/`.

2.  **Preprocess data**:
    ```bash
    python code/data/preprocessing.py
    ```
    *Output*: `data/processed/preprocessed_data.parquet`.

## Running the Pipeline

### 1. Train Models (User Story 1)
Executes Time-Block Cross-Validation and trains RF/GP models.
```bash
python code/models/train.py
```
*Output*: `data/artifacts/model_*.pkl`, `data/artifacts/cv_report.json`.

### 2. Sensitivity Analysis (FR-009)
Sweeps the inconsistency tolerance threshold.
```bash
python code/analysis/sensitivity.py
```
*Output*: `data/artifacts/sensitivity_report.json`.

### 3. Generate Reconstruction (User Story 2)
Applies the best model to pre-satellite data.
```bash
python code/models/predict.py
```
*Output*: `data/processed/tsi_reconstruction_1610_2002.parquet`.

### 4. Compare with Baseline (User Story 3)
Calculates error reduction and variance differences.
```bash
python code/analysis/comparison.py
```
*Output*: `data/artifacts/comparison_report.json`.

## Running Tests

Execute the full test suite:
```bash
pytest tests/ -v
```

## Troubleshooting

*   **Missing TSI Data**: If `ingestion.py` fails to load TSI from the verified URL, the pipeline halts. Do not use synthetic data for scientific claims.
*   **Memory Error**: Ensure you are running on a machine with >4GB RAM. The pipeline is optimized for 7GB.
*   **Cycle Detection Failure**: If cycle boundaries are misaligned, check the `SILSO` cycle definitions in `code/config.py`.