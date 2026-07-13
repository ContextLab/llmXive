# Quickstart: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

## Prerequisites

-   Python 3.11+
-   Git
-   Access to GitHub Actions (for CI execution) or local environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-314-predicting-the-impact-of-composition-on-/
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Data Ingestion & Cleaning
Fetches data (if available) and performs initial cleaning.
```bash
python code/ingestion.py --output data/processed/cleaned.csv
```
*Note: If no data is found, this script will exit with error code 1 and a "Power Limitation" message.*

### 2. Feature Engineering
Computes elemental descriptors.
```bash
python code/descriptors.py --input data/processed/cleaned.csv --output data/processed/features.csv
```

### 3. Model Training & Evaluation
Trains RF and GBM, performs CV, and generates SHAP values.
```bash
python code/modeling.py --input data/processed/features.csv --output data/outputs/results.json
```

### 4. Diagnostics & Reporting
Checks collinearity and generates the final report.
```bash
python code/diagnostics.py --input data/outputs/results.json --output reports/final_report.md
```

## Verification

To verify the installation and data flow:
```bash
pytest tests/
```
Ensure all tests pass, particularly `test_descriptors.py` (verifies calculation logic) and `test_ingestion.py` (verifies filtering logic).

## Troubleshooting

-   **Error: "Power Limitation"**: The dataset contains fewer than 30 valid entries. Check the data source or relax the $N \ge 30$ constraint (requires spec change).
-   **Error: "Missing Data"**: If `sintering_temp` is missing for all entries in a group, the global median fallback is used. Check logs for imputation details.
-   **Memory Error**: Ensure the dataset is not larger than 7GB. The pipeline automatically samples if necessary (future enhancement).
