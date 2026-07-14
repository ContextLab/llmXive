# Quickstart: Predicting Corrosion Potential from Composition and Environment

## Prerequisites

- **Python**: 3.11+
- **Environment**: GitHub Actions `ubuntu-latest` (or local equivalent with 7 GB+ RAM).
- **Access**: No special API keys required if using public NIST data (or verified HuggingFace mirrors).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-376-predicting-corrosion-potential-from-comp
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the main entry script.

### 1. Data Ingestion & Preprocessing
This step downloads (or loads) the data, validates the schema, filters outliers, and **normalizes reference electrodes to SHE**.
```bash
python code/data/download_nist.py
python code/data/preprocess.py
```
*Output*: `data/processed/corrosion_dataset.parquet` and `data/logs/pipeline.log`.

### 2. Model Training & Evaluation
Trains Random Forest and Gradient Boosting models using **GroupKFold (k=5)** to ensure statistical power.
```bash
python code/models/train.py
python code/models/evaluate.py
```
*Output*: `data/processed/model_metrics.json` and `data/processed/predictions.parquet`.

### 3. Interpretability Analysis
Generates feature importance plots and partial dependence plots.
```bash
python code/models/interpret.py
```
*Output*: `data/figures/` (PDF/PNG) and `data/processed/importance_report.csv`.

## Verification

To verify the pipeline:
1. Check `data/logs/pipeline.log` for "Schema Validation: PASSED" and "Reference Electrode Normalization: COMPLETED".
2. Ensure `data/processed/model_metrics.json` contains `r2_score` and `rmse`.
3. Confirm `data/figures/` contains at least one partial dependence plot.
4. Verify that `data/processed/model_metrics.json` includes a `regime_of_validity` field listing the alloy families tested.

## Troubleshooting

- **Error: `DataInsufficientError`**: The dataset has a limited number of records or alloy designations. The pipeline cannot proceed.
- **Error: `SchemaMismatchError`**: The source data lacks required columns (pH, temperature, composition, reference electrode). Check the raw data source.
- **Error: `429 Too Many Requests`**: The download script has a built-in retry mechanism. If it fails after multiple retries, check network connectivity.
- **Error: `ReferenceMismatchError`**: The reference electrode is missing or cannot be converted to SHE. Check the raw data for reference electrode metadata.