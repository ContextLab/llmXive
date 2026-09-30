# Quickstart: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Internet access (for downloading BMG data)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins all dependencies (pandas, scikit-learn, etc.) to ensure reproducibility.*

## Running the Pipeline

The pipeline consists of three main stages: Ingestion, Modeling, and Analysis.

### 1. Data Ingestion & Feature Engineering
Download the **BMG data**, filter for ternary alloys, and compute thermodynamic descriptors.

```bash
python code/ingestion.py
```
- **Output**: `data/processed/processed_alloys.csv`
- **Logs**: `data/logs/exclusion_log.txt`, `data/logs/ingestion_hash.txt`
- **Error Handling**: If the dataset is empty after filtering, the script raises a `ValueError` and logs to `data/logs/empty_dataset_error.log`.

### 2. Model Training & Validation
Train the Random Forest model and perform 5-fold cross-validation.

```bash
python code/modeling.py
```
- **Output**: `data/models/random_forest_model.pkl`, `data/models/cv_metrics.json`
- **Metrics**: Prints Mean CV RMSE and Test RMSE to console.

### 3. Sensitivity & Importance Analysis
Perform permutation importance and threshold sensitivity analysis.

```bash
python code/analysis.py
```
- **Output**: `data/models/sensitivity_report.json`
- **Validation**: Checks for collinearity and flags high-correlation pairs.

## Running Tests

Execute unit and integration tests to verify data integrity and pipeline correctness.

```bash
pytest tests/ -v
```
- **Unit Tests**: `tests/unit/test_features.py` (validates thermodynamic formulas).
- **Integration Tests**: `tests/integration/test_pipeline.py` (validates end-to-end flow).

## Validating Schemas

Ensure all generated artifacts match the defined contracts.

```bash
python code/validate_schemas.py
```
- **Output**: Prints validation status for `processed_alloys.csv`, `cv_metrics.json`, and `sensitivity_report.json`.

## Reproducibility Check

To verify reproducibility, re-run the ingestion step and compare the hash:

```bash
python code/utils.py --check-hash
```
- Compares the SHA-256 hash of `data/processed/processed_alloys.csv` against the stored value in `data/logs/ingestion_hash.txt`.