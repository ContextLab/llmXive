# Quickstart: Predicting Plant Root Architecture from Soil Nutrient Availability

## Prerequisites
-   Python 3.11+
-   `pip` or `conda`

## Installation

1.  **Clone the repository** (or navigate to the project directory).
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

### 1. Data Ingestion & Preprocessing
Download and clean the data. This step handles missing ISRIC data gracefully.
```bash
python code/ingestion.py
python code/preprocessing.py
```
*Output*: `data/processed/merged_dataset.parquet`

### 2. Modeling
Fit LMM and Random Forest models with species-level stratified validation.
```bash
python code/modeling.py
```
*Output*: `artifacts/metrics.json`, `artifacts/logs/model_fitting.log`

### 3. Visualization & Reporting
Generate partial dependence plots and the final report.
```bash
python code/visualization.py
```
*Output*: `artifacts/reports/final_report.pdf`, `artifacts/reports/plots/*.png`

### 4. Contract Testing
Verify data and output schemas.
```bash
pytest tests/contract/test_schemas.py
```

## Troubleshooting
-   **Missing Soil Data**: If the pipeline logs "ISRIC unavailable", it will proceed with root-only data. Check `artifacts/logs/deviation.log` for details.
-   **Memory Error**: If RAM exceeds 7GB, reduce the dataset size by filtering for top 5 species by sample count.
