# Quickstart: Predicting Plant Phenology from Satellite Imagery and Climate Data

## Prerequisites

- Python 3.11+
- Git
- **Google Earth Engine Account**: Required. You must authenticate via `earthengine authenticate`.
- NOAA/NASA API keys (if required, otherwise public access)
- Nature's Notebook API key (if required, otherwise public access)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-264-predicting-plant-phenology-from-satellit
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Google Earth Engine**:
   **Required**: Even for public data, GEE requires authentication.
   ```bash
   earthengine authenticate
   ```

## Running the Pipeline

### 1. Data Ingestion
Download and align data for a single site (test run):
```bash
python src/cli/run_pipeline.py --mode ingestion --sites SITE_001 --year 2020
```

### 2. Model Training
Train XGBoost model with **Spatial Block Cross-Validation**:
```bash
python src/cli/run_pipeline.py --mode train --folds 5 --sites SITE_001..SITE_015 --cv-type spatial
```

### 3. Sensitivity Analysis
Run hyperparameter sweep:
```bash
python src/cli/run_pipeline.py --mode sensitivity --alpha 0.01,0.05,0.1
```

### 4. Evaluation
Generate metrics report:
```bash
python src/cli/run_pipeline.py --mode evaluate --model artifacts/models/best_model.pkl
```

## Expected Outputs

- **`data/processed/environmental_time_series.csv`**: Cleaned, aligned dataset.
- **`artifacts/models/best_model.pkl`**: Trained model artifact.
- **`artifacts/reports/metrics.json`**: RMSE, MAE, R², feature importance.
- **`data/provenance.yaml`**: API endpoints, parameters, checksums.

## Troubleshooting

- **API Rate Limits**: Add `--delay 5` to throttle requests.
- **Memory Errors**: Reduce `--sites` batch size or enable `--chunking`.
- **Missing Data**: Check `data/raw/` logs for failed downloads; retry with `--retry`.
- **Authentication Error**: Ensure you ran `earthengine authenticate` and are in the correct virtual environment.

## Next Steps

- Expand to all 15 sites.
- Add new phenological events (e.g., leaf-out).
- Integrate additional climate variables (e.g., humidity).
