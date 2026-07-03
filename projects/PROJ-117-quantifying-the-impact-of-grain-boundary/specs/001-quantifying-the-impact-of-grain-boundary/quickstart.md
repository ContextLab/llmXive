# Quickstart: Quantifying the Association of Grain Boundary Character with Diffusivity

## Prerequisites

- Python 3.10+
- `pip` or `conda`
- Access to Materials Project API (API Key required, set as `MP_API_KEY` env var)
- GitHub Actions Free Tier Runner (for CI execution)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-117-quantifying-the-impact-of-grain-boundary
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

4.  **Set Environment Variables**:
    ```bash
    export MP_API_KEY="your_materials_project_api_key"
    export OPENKIM_API_KEY="your_openkim_api_key" # If required
    ```

## Running the Pipeline

### Step 1: Download Data
Execute the download script. This will attempt to fetch grain boundary data from the configured sources.
```bash
python code/download.py
```
*Output*: Raw files in `data/raw/`. If < 500 records are found, the script exits with code 1.

### Step 2: Geometry Parsing & Preprocessing
Clean data, parse geometry files (POSCAR/CIF) to extract boundary width and excess volume, and engineer features.
```bash
python code/preprocess.py
```
*Output*: `data/processed/grain_boundary_clean.parquet`.

### Step 3: Collinearity Diagnostics
Run diagnostics to check for redundancy between misorientation and Σ value.
```bash
python code/diagnostics.py
```
*Output*: `artifacts/reports/collinearity_report.json`.

### Step 4: Train Model
Train the XGBoost model with hyperparameter tuning.
```bash
python code/train.py
```
*Output*: `models/best_model.json`, `artifacts/reports/training_log.json`.

### Step 5: Validate & Interpret
Perform k-fold validation, bias testing, SHAP analysis, and threshold sensitivity sweep.
```bash
python code/validate.py
python code/interpret.py
```
*Output*: `artifacts/reports/validation_report.json`, `artifacts/figures/shap_summary.png`, `artifacts/reports/threshold_sweep_report.json`.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Error: Data Insufficiency**: The dataset retrieved contained a limited number of valid records. Check the API keys and the availability of grain boundary data in the source repositories. This is an expected outcome if the open data does not contain the required descriptors.
- **Error: Memory Limit**: If running locally on a machine with < 7 GB RAM, the script may crash. The pipeline is designed for GitHub Actions; local runs may need manual sampling.
- **API Rate Limit**: The `download.py` script includes exponential backoff. If the limit is exceeded, wait and retry.
- **Collinearity Warning**: If MI > 0.8, the model will automatically select a reduced feature set. Check `collinearity_report.json` for details.