# Quickstart: Predicting Plant Root Architecture from Soil Nutrient Profiles

## Prerequisites

- Python 3.11+
- `git`
- Access to the project repository

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-434-predicting-plant-root-architecture-from-/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import sklearn, pandas, rasterio; print('Dependencies OK')"
    ```

## Running the Pipeline

The pipeline is orchestrated via `main.py`.

### Step 1: Data Ingestion (Phase 0)
Downloads and merges soil and trait data.
```bash
python main.py --stage ingestion
```
*Output*: `data/processed/merged_dataset.csv`
*Note*: If no verified root trait data is found, a synthetic proxy is generated for pipeline testing only.

### Step 2: Model Training (Phase 1)
Trains the Random Forest and runs Stratified 5-Fold CV + Permutation Tests.
```bash
python main.py --stage modeling
```
*Output*: `artifacts/model_metrics.json`, `artifacts/feature_importance.csv`

### Step 3: Sensitivity Analysis (Phase 2)
Runs the p-value threshold sweep for feature importance.
```bash
python main.py --stage sensitivity
```
*Output*: `artifacts/sensitivity_report.md`

### Full Run
To run the entire pipeline end-to-end:
```bash
python main.py --full
```

## Verifying Results

1.  **Check Metrics**:
    ```bash
    cat artifacts/model_metrics.json
    ```
    Ensure R² > 0 for both targets and that the permutation test p-value < 0.05.
    *Note*: If synthetic data was used, results are for pipeline validation only.

2.  **Inspect Feature Importance**:
    ```bash
    cat artifacts/feature_importance.csv
    ```
    Verify the top 3 features are stable across the sensitivity analysis.

3.  **Run Tests**:
    ```bash
    pytest tests/
    ```

## Troubleshooting

- **Missing Data**: If `merged_dataset.csv` is empty, check the log for "No verified source" errors regarding root trait data.
- **API Errors**: If SoilGrids fails, ensure network access on the runner.
- **Memory Errors**: If RAM exceeds 7GB, reduce the sample size in `config.yaml` (if applicable) or enable streaming.
- **Data Quality**: If the pipeline halts with `DataQualityError`, the match proportion (SC-001) was < 90%.