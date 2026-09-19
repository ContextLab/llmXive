# Quickstart: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the verified dataset URLs (no credentials required).

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <repo-url>
cd <repo-dir>/projects/PROJ-293-predicting-the-impact-of-laser-surface-t
pip install -r code/requirements.txt
```

### 2. Prepare Data Directory Structure

Ensure the following directories exist:
```bash
mkdir -p data/raw data/processed models reports state
```

### 3. Download Data

The ingestion script will automatically download the verified datasets. To run manually:
```bash
# The script code/01_ingest.py handles this, but you can verify the sources:
# OpenML: Wear of Materials
curl -o data/raw/openml_wear.json "https://www.openml.org/api/v1/json/data/4594"
# Zenodo: LST Parameters (ID 1006980)
curl -o data/raw/zenodo_lst.csv "https://doi.org/10.5281/zenodo.1006980"
```

### 4. Run the Pipeline

Execute the full pipeline sequentially:

```bash
# Step 1: Ingest and Standardize (includes data verification, unit conversion, and Archard normalization)
python code/01_ingest.py

# Step 2: Preprocess (Missing values, VIF, Scaling)
python code/02_preprocess.py

# Step 3: Train Models (GridSearch, LOO-CV with fallback)
python code/03_train.py

# Step 4: Interpret (SHAP, Permutation, Literature Consensus Check)
python code/04_interpret.py

# Step 5: Generate Reports (includes validation_status)
python code/05_report.py
```

### 5. Verify Outputs

Check the `reports/` directory for:
*   `model_report.json`: Contains R², MAE, RMSE, transferability flags, and validation status.
*   `shap_summary.png`: Feature importance visualization.
*   `validation_log.txt`: LOO-CV results and warnings.
*   `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml`: Hash registry for data and model artifacts.

### 6. Run Tests

```bash
pytest tests/
```

## Troubleshooting

*   **Data Insufficiency Error**: If the script halts with `data_insufficiency_error`, check `reports/validation_log.txt` for the record count. The dataset may not meet the N=300 target. The system will proceed with a power limitation warning.
*   **Missing Columns**: If the ingestion fails, verify that the source CSVs contain the required columns defined in `contracts/dataset.schema.yaml`.
*   **Unit Conversion Error**: If `unit_conversion_status` is 'unavailable', check the source data for `contact_area` or `density`. Records with 'unavailable' status are excluded from the normalized set.
*   **Memory Error**: Unlikely given the dataset size, but if it occurs, reduce the `n_estimators` grid size in `03_train.py`.
*   **Versioning**: Ensure `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml` is updated with checksums after each run.